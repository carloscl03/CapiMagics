"""Generation: turn a placement plan into glayout geometry.

Kept apart from `place.py` on purpose. Placement is arithmetic over design
rules and can be exercised without generating anything; this module is where
the glayout dependency, the port names and the ordering of routing calls all
live. Mixing them means a spacing calculation cannot be checked without
building a layout.

The flow inside generation runs in two passes, which reads like an inversion
but is not: primitives have to exist before their size and wells can be read,
so it goes

    generate primitives  ->  plan (place.py)  ->  assemble at the planned x

Power rails are drawn here rather than left to the caller. A cell that exposes
VDD and VSS as ports and never connects them looks finished and is not -- the
LIF neuron reached DRC-clean in that state, which is exactly how the omission
survived.
"""
from __future__ import annotations

from decimal import ROUND_UP, Decimal

from dataclasses import dataclass
from typing import Optional
from warnings import warn

from . import mim as mim_pdk
from .place import MIM_BOTTOM_TO_MET2 as MIM_A_MET2
from .place import Cell, Rails, Stack, pair, plan_row
from .spec import Note, Severity

# Ports a glayout FET offers that this module relies on.
GATE = "multiplier_0_gate_{side}"
DRAIN = "multiplier_0_drain_{side}"
SOURCE = "multiplier_0_source_{side}"
# The tie has ports on comp and on the top metal. Routing from the comp one
# drops a full via stack in the middle of the tie's own contact row -- 0.18 um
# between contacts where the rule wants 0.25. The narrow top-metal port on the
# side avoids both that and the wide N/S port, which is broad enough to merge
# with whatever it passes.
TIE = "tie_{end}_top_met_E"

# met3 es la capa mas alta que los transistores dejan libre. Con el MIM en
# met4/met5 (opcion B, la que sigue el equipo) esas dos ya no lo estan sobre
# la huella del banco, asi que met3 no se elige por dejar met4 abierto: se
# elige porque es la que hay. Fuera del banco met4 y met5 siguen disponibles
# para el ruteo entre neuronas.
RIEL_POR_DEFECTO = "met3"


@dataclass
class Inverter:
    """One placed inverter and the ports the row needs from it."""
    ref_p: object
    ref_n: object
    stack: Stack

    @property
    def vdd_port(self):
        return self.ref_p.ports[SOURCE.format(side="N")]

    @property
    def vss_port(self):
        return self.ref_n.ports[SOURCE.format(side="S")]

    @property
    def in_port(self):
        return self.ref_n.ports[GATE.format(side="E")]

    @property
    def out_port(self):
        return self.ref_n.ports[DRAIN.format(side="W")]

    @property
    def vdd_tie(self):
        return self.ref_p.ports[TIE.format(end="N")]

    @property
    def vss_tie(self):
        return self.ref_n.ports[TIE.format(end="S")]


def _into_metal(port, distance: float) -> float:
    """How far to step in y so a via lands on the port's metal, not past it.

    A port marks the edge of its shape and faces *away* from it: a south
    facing port has its metal to the north. Centring a via on the port leaves
    half of it hanging over whatever is on the other side -- on a glayout FET
    that is the tie ring, a few tens of nanometres away. Ports on a vertical
    edge (east, west) need no y step at all.
    """
    angle = (port.orientation or 0) % 360
    if 45 < angle < 135:          # faces north -> metal is south
        return -distance
    if 225 < angle < 315:         # faces south -> metal is north
        return +distance
    return 0.0


def _merge_columns(points, width: float, sep: float) -> list[list]:
    """Group drop positions that are too close to stand as separate shapes.

    Two rectangles of `width` centred less than `width + sep` apart leave a
    gap the spacing rule rejects. Since every drop on one rail carries the
    same net, the fix is to draw them as one rectangle rather than to shove
    them apart -- shoving would walk the via off the metal it has to land on.

    `points` must be sorted by x.
    """
    groups: list[list] = []
    for point in points:
        if groups and point[0] - groups[-1][-1][0] < width + sep:
            groups[-1].append(point)
        else:
            groups.append([point])
    return groups


def _center_on(ref, x: float, y: float):
    """Move a reference so its centre lands on (x, y).

    `move(destination=...)` is a plain translation in gdsfactory -- origin
    defaults to (0, 0), not to the reference centre -- so placing by centre
    has to be written as an explicit delta.
    """
    cx, cy = ref.center
    ref.movex(float(x) - float(cx)).movey(float(y) - float(cy))
    return ref


def inverter_row(pdk, nmos_params: dict, pmos_params: dict, count: int = 3,
                 pair_gap: float = 0.95, rails: Optional[Rails] = None,
                 stages: Optional[list] = None, chain: bool = False,
                 channel_tracks: int = 2):
    """A row of inverters with VDD and VSS rails, wired to both.

    `chain` wires stage i to stage i+1, turning the row into a chain
    instead of three independent inverters.

    `stages` gives per-inverter sizing as [(nmos_params, pmos_params), ...] and
    overrides `count`. The row is not uniform in practice: in a LIF cell the
    threshold inverter sets the trip point the characterisation was fitted
    around and must not move, while the output inverter is sized for whatever
    it drives. Sizing them all alike is the special case, not the rule.

    Returns (Component, [Inverter]). Spacing comes from place.plan_row, so the
    only distance decided here is `pair_gap` -- the room the gate and drain
    links need to turn between the two devices, which no well rule constrains
    because gf180 lets nwell and pwell abut.
    """
    from glayout.backend import Component, rectangle
    from glayout.primitives.fet import nmos, pmos
    from glayout.routing.c_route import c_route
    from glayout.routing.L_route import L_route
    from glayout.routing.straight_route import straight_route

    if any(p.get("multipliers", 1) > 1
           for stage in (stages or [(nmos_params, pmos_params)]) for p in stage):
        warn("multipliers > 1 doubles the device height, and the rail drops "
             "then run the full way down it alongside the gate and drain "
             "links; they end up 0.10 um apart where met3 wants 0.30. The "
             "cell is still correctly connected -- only the spacing fails -- "
             "but placing the drops clear of the routing needs a router that "
             "knows where the routes are. Use fingers instead: they widen the "
             "device without making it taller, and come out DRC clean.")

    if stages is None:
        stages = [(nmos_params, pmos_params)] * count

    devices, stacks, blocks = [], [], []
    for i, (nparams, pparams) in enumerate(stages):
        pfet = pmos(pdk, **pparams)
        nfet = nmos(pdk, **nparams)
        stack = pair(Cell.from_component("pfet", pfet, pdk),
                     Cell.from_component("nfet", nfet, pdk),
                     pdk, minimum=pair_gap, name=f"inv{i}")
        as_cell = stack.as_cell()
        devices.append((pfet, nfet))
        stacks.append(stack)
        blocks.append(Cell(f"inv{i}", stack.width, stack.height,
                           as_cell.wells, as_cell.layers))

    # One layer above whatever the blocks reach, so the straps fly over. The
    # tallest stage sets the rail height for the whole row: shorter ones sit
    # inside it rather than each getting its own pair of rails.
    tallest = max(blocks, key=lambda b: b.height)
    # One track of channel per chained link; an unchained row needs none.
    rails = rails or Rails.above(pdk, blocks,
                                 tracks=channel_tracks if chain else 0)
    plan = plan_row(blocks, [], pdk, rails=rails)

    top = Component(name="inverter_row")
    invs: list[Inverter] = []

    for i, (stack, (pfet, nfet)) in enumerate(zip(stacks, devices)):
        cx = plan.x[i] + stack.width / 2
        offsets = stack.offsets()
        ref_p = top << pfet
        ref_n = top << nfet
        # Stages of different height share one pair of rails, so they are
        # placed against the rails rather than centred on the row: the source
        # of a small inverter has to reach the same strap as a big one.
        _center_on(ref_p, cx + offsets["pfet"][0], offsets["pfet"][1])
        _center_on(ref_n, cx + offsets["nfet"][0], offsets["nfet"][1])
        ref_p.name, ref_n.name = f"pfet_{i}", f"nfet_{i}"

        # gate to gate and drain to drain: the two links that make it an
        # inverter, and the reason the pair needs any vertical gap at all.
        top << c_route(pdk, ref_p.ports[GATE.format(side="W")],
                       ref_n.ports[GATE.format(side="W")])
        top << c_route(pdk, ref_p.ports[DRAIN.format(side="E")],
                       ref_n.ports[DRAIN.format(side="E")])
        # The body ties are not wired to their source here. Doing so needs a
        # met2 run from the tie, at the device edge, to the source port, which
        # sits inside the device -- and that run crosses the gate on the way,
        # shorting input to source. Both belong on the same rail anyway, so
        # each is taken up to it separately and meets there.
        invs.append(Inverter(ref_p, ref_n, stack))

    if chain:
        # Stage i drives stage i+1. The output leaves on the west (the drain's
        # east port is taken by the pfet-to-nfet link) and the input arrives on
        # the east (the west gate port is taken by the gate-to-gate link), so
        # the signal runs east to west and the chain is laid out right to left:
        # driving left to right would send every hop back across two blocks.
        # Pairing runs right to left: the driver is the eastern stage, whose
        # west-facing drain then points straight at the load's east-facing
        # gate. Driving the other way leaves the two ports back to back, which
        # is why straight_route silently fails to join them -- the same shape
        # Abrahan's neuron has, where the OUT-to-IN links never connected.
        # The link leaves both stages southward and runs across in the channel
        # reserved under the row. `extension` is what puts it there: left at
        # its default the crossing segment lands 0.5 um below the ports, which
        # is still inside the device, and the route merges with the tie ring
        # and the rail instead of connecting anything. Reserving the channel
        # is necessary but not sufficient -- the router has to be aimed at it.
        # The drain's south port sits at the *top* of the device and merely
        # faces south, so a route leaving through it runs down across the
        # device's own source and tie ring on the way out -- which is how the
        # link kept shorting to VSS no matter how wide the channel got. It has
        # to leave sideways instead. drain_W is horizontal and gate_S is
        # vertical, so the corner between them is an L.
        for driver, load in zip(invs[1:], invs):
            top << L_route(pdk, driver.out_port,
                           load.ref_n.ports[GATE.format(side="S")])

    _add_rails(pdk, top, invs, tallest.height, plan, rails, rectangle)
    # Signal enters at the eastern end and leaves at the western one.
    top.add_port(name="IN", port=invs[-1].in_port if chain else invs[0].in_port)
    top.add_port(name="OUT", port=invs[0].out_port if chain else invs[-1].out_port)
    return top, invs


def _add_rails(pdk, top, invs, row_height: float, plan, rails: Rails, rectangle):
    """Draw VDD above and VSS below, then tie every inverter to both.

    The rails sit one layer above the blocks. That is not a preference: a
    glayout FET occupies met2 out to its own tie ring, and its source port
    sits *inside* that ring rather than on the boundary, so a met2 drop from
    the source to a rail crosses the tie on the way out and shorts the two
    together -- which is what a first attempt here did, taking every net in
    the row with it. On met3 the strap flies over the ring untouched and only
    comes down, through a via stack, exactly on the source.

    The straps span the full row width so abutting rows can share them.
    """
    from glayout.primitives.via_gen import via_stack

    rail_layer = pdk.get_glayer(rails.glayer)
    # The rails clear the tallest stage, so every stage reaches the same
    # strap regardless of its own height.
    half = row_height / 2
    # band, not clearance: the rail sits beyond the routing channel too.
    y_vdd = pdk.snap_to_2xgrid(half + rails.band - rails.width / 2)
    y_vss = -y_vdd

    for y in (y_vdd, y_vss):
        strap = top << rectangle(
            size=pdk.snap_to_2xgrid([plan.width, rails.width]),
            layer=rail_layer, centered=True)
        _center_on(strap, pdk.snap_to_2xgrid(plan.width / 2), y)

    from glayout.util.comp_utils import evaluate_bbox

    climb = via_stack(pdk, "met2", rails.glayer)
    via_h = evaluate_bbox(climb)[1]

    # First place every via, then draw the straps: which drops can share one
    # rectangle is a property of the whole row, not of one inverter.
    via_w = evaluate_bbox(climb)[0]
    clear = via_w + float(pdk.get_grule(rails.glayer)["min_separation"])

    landings: dict[float, list[tuple[float, float]]] = {y_vdd: [], y_vss: []}
    for inv in invs:
        for source, tie, y_rail in ((inv.vdd_port, inv.vdd_tie, y_vdd),
                                    (inv.vss_port, inv.vss_tie, y_vss)):
            # The tie is the eastern port, so it lands where it is. The source
            # then has to sit east of the device midline -- the gate runs up
            # the middle and a via on it overlaps, a short no spacing rule
            # reports because the shapes touch rather than crowd -- but not so
            # far east that it crowds the tie's own via. A quarter of the port
            # width is the natural offset and works until the port is wide,
            # which is what a second multiplier does: the offset grows with
            # the port and walks the via to 0.10 um of the tie's, where met3
            # wants 0.30. Via stacks cannot be merged away like the straps
            # above them, so the offset is capped instead.
            x_tie = pdk.snap_to_2xgrid(float(tie.center[0]) + tie.width / 4)
            wanted = float(source.center[0]) + source.width / 4
            x_src = pdk.snap_to_2xgrid(min(wanted, x_tie - clear))
            if x_src <= float(source.center[0]):
                warn(f"no room east of the gate for the {y_rail:+.2f} drop on "
                     f"{source.name}; leaving it at {wanted:.3f} and expecting "
                     f"a spacing violation against the body tie")
                x_src = pdk.snap_to_2xgrid(wanted)
            for port, x in ((source, x_src), (tie, x_tie)):
                # A port marks the *edge* of its metal, not the middle:
                # centring a via on it leaves half the stack hanging off the
                # source and into whatever sits beyond -- on a glayout FET,
                # the tie ring a few tens of nm away. Step in by half a stack.
                y_via = pdk.snap_to_2xgrid(
                    float(port.center[1]) + _into_metal(port, via_h / 2))
                _center_on(top << climb, x, y_via)
                landings[y_rail].append((x, y_via))

    # Drops are minimum width, not the port's: at port width the source and
    # tie of one device sit 0.10 um apart where met3 wants 0.30, and they
    # carry the same net, so widening them buys nothing a wider rail would
    # not. Two drops that still end up closer than the rule share a single
    # rectangle instead -- same net, so merging is free, and it is the only
    # way out when the crowding comes from two different devices.
    sep = float(pdk.get_grule(rails.glayer)["min_separation"])
    for y_rail, points in landings.items():
        for group in _merge_columns(sorted(points), rails.width, sep):
            xs = [p[0] for p in group]
            left, right = min(xs) - rails.width / 2, max(xs) + rails.width / 2
            deepest = max((p[1] for p in group), key=lambda y: abs(y_rail - y))
            drop = top << rectangle(
                size=pdk.snap_to_2xgrid([right - left, abs(y_rail - deepest)]),
                layer=rail_layer, centered=True)
            _center_on(drop, pdk.snap_to_2xgrid((left + right) / 2),
                       pdk.snap_to_2xgrid((y_rail + deepest) / 2))

    top.add_port(name="VDD", port=invs[0].vdd_port)
    top.add_port(name="VSS", port=invs[0].vss_port)


# --------------------------------------------------------------------------
# the LIF cell
# --------------------------------------------------------------------------

# Ports the routing relies on, and why each side rather than another.
_GATE_MID = "multiplier_0_gate_{side}"
_DRAIN_MID = "multiplier_0_drain_{side}"


def lif_cell(pdk, inverter: dict, m5: dict, cap_size: float = 5.0,
             supply_width: float = 1.0, output_inverter: dict | None = None,
             n_caps: int = 3, rail_layer: Optional[str] = RIEL_POR_DEFECTO,
             name: str = "lif"):
    """A LIF neuron: three inverters, the reset device and the membrane cap.

    Laid out in bands rather than as a row of inverters. Grouping by device
    type is what makes it compact: the pfets share one band, the nfets another,
    and the strip beside the long reset device -- 45% dead area in a single
    row -- holds the capacitors.

        pfets            <- top
        M5 (reset)       <- spans the full width; its length IS the cell width
        nfets + caps     <- bottom

    That puts M5 between the two halves of every inverter, so the gate and
    drain links cross it. They can, because M5 stops at met2 and met3 is free
    over the whole band. The rails then go to met4, since the capacitors reach
    met3. Nobody designed that assignment -- it falls out of asking, at each
    step, which layer is free above what has to be crossed.

    Returns (Component, dict of references).
    """
    from glayout.backend import Component, rectangle
    from glayout.primitives.fet import nmos, pmos
    from glayout.primitives.mimcap import mimcap
    from glayout.primitives.via_gen import via_stack
    from glayout.routing.c_route import c_route
    from glayout.routing.straight_route import straight_route
    from glayout.util.comp_utils import evaluate_bbox

    from .place import Band, plan_bands

    # The third inverter is the output buffer -- M7/M8 in the netlist -- and
    # the solver sizes it on its own, by the load it has to drive. The other
    # two are the ones inside the loop and stay minimum.
    salida = output_inverter or inverter

    pfet_c = pmos(pdk, **inverter)
    nfet_c = nmos(pdk, with_dnwell=False, **inverter)
    pfet_o_c = pmos(pdk, **salida)
    nfet_o_c = nmos(pdk, with_dnwell=False, **salida)
    m5_c = nmos(pdk, with_dnwell=False, **m5)
    cap_c = mimcap(pdk, size=(cap_size, cap_size))

    m5_cell = Cell.from_component("M5", m5_c, pdk)
    cap = Cell.from_component("cap", cap_c, pdk)

    def clones(cell, n, prefix):
        # insets included: without them the MIM.1 clearance is computed as if
        # the cap's met2 plate reached its outline, which it does not, and the
        # planner asks for more room than the rule wants.
        return [Cell(f"{prefix}{i}", cell.width, cell.height,
                     cell.wells, cell.layers, cell.insets) for i in range(n)]

    nfet_comps = [nfet_c, nfet_c, nfet_o_c]
    pfet_comps = [pfet_c, pfet_c, pfet_o_c]
    nf_cells = [Cell.from_component(f"nf{i}", c, pdk)
                for i, c in enumerate(nfet_comps)]
    pf_cells = [Cell.from_component(f"pf{i}", c, pdk)
                for i, c in enumerate(pfet_comps)]

    # Por defecto met3. Rails.above llega sola a la misma capa: el mimcap esta
    # en la cima de la pila y no participa en una regla que consiste en subir
    # un piso, asi que decide el mas alto de los que quedan. Pasar
    # `rail_layer=None` devuelve esa eleccion automatica, y coincide.
    # Con el MIM en met4/met5 la separacion del riel deja de decidirla met3.
    # La correa de la placa inferior aterriza en el riel viniendo de met5, y
    # esa pila deja un pad de met4 justo bajo el banco: contra la placa, que
    # tambien es met4, manda MIM.1 y no la separacion de met3, que es cuatro
    # veces menor. Sin esto la celda sale con una violacion por condensador.
    holgura = None
    if n_caps:
        g_bot = pdk.layer_to_glayer(pdk.get_grule("capmet")["capmetbottom"])
        if g_bot != rail_layer:
            holgura = float(pdk.get_grule("capmet")["min_separation"])
    rails_forzados = (Rails.minimum(pdk, rail_layer, width=supply_width,
                                    clearance=holgura)
                      if rail_layer else None)
    plan = plan_bands([Band("bottom", nf_cells + clones(cap, n_caps, "cap")),
                       Band("m5", [m5_cell]),
                       Band("top", pf_cells)], pdk, rails=rails_forzados,
                      rail_clearance=holgura)
    lower, middle, upper = plan.bands

    top = Component(name=name)
    nfets, pfets, caps = [], [], []
    for i in range(3):
        nfets.append(_center_on(top << nfet_comps[i],
                                lower.plan.x[i] + nf_cells[i].width / 2, lower.y))
    for i in range(n_caps):
        caps.append(_center_on(top << cap_c,
                               lower.plan.x[3 + i] + cap.width / 2, lower.y))
    m5_ref = _center_on(top << m5_c, middle.plan.x[0] + m5_cell.width / 2, middle.y)
    for i in range(3):
        pfets.append(_center_on(top << pfet_comps[i],
                                upper.plan.x[i] + pf_cells[i].width / 2, upper.y))

    # --- each inverter: gate to gate, drain to drain -----------------------
    # The two links must not share a column. gate_S and drain_S both sit at
    # x=0 of the device, so routing both from there overlays them and leaves
    # every inverter diode-connected -- with the gate and drain on one net,
    # which still looks like a correctly paired inverter to a careless check.
    drain_routes = []
    for p, n in zip(pfets, nfets):
        top << straight_route(pdk, p.ports[_GATE_MID.format(side="S")],
                              n.ports[_GATE_MID.format(side="N")], glayer1="met3")
        drain_routes.append(top << c_route(
            pdk, p.ports[_DRAIN_MID.format(side="E")],
            n.ports[_DRAIN_MID.format(side="E")], cglayer="met3"))

    _wire_lif(pdk, top, nfets, caps, m5_ref, drain_routes, plan,
              via_stack, rectangle, evaluate_bbox)
    rails_y = _rails_bands(pdk, top, pfets, nfets, plan, via_stack, rectangle,
                           evaluate_bbox, supply_width, m5_ref, caps)
    rails_y = _al_origen(top, rails_y)
    _boundary(pdk, top, rectangle)

    top.add_port(name="IN", port=nfets[0].ports[_GATE_MID.format(side="W")])
    top.add_port(name="OUT", port=nfets[2].ports[_DRAIN_MID.format(side="W")])
    _pin_labels(pdk, top, rectangle, nfets, pfets, caps, m5_ref, rails_y,
                drain_routes)
    return top, {"nfets": nfets, "pfets": pfets, "caps": caps, "m5": m5_ref,
                 "rails": rails_y,
                 "plan": plan}


# Puertos del mimcap. La placa superior sale por `top_met_*`; la inferior no
# tiene puerto propio a nivel superior, se saca por la extension al sur, que
# la sube a la capa de la placa superior. Ver _cap_glayers.
_CAP_TOP = "top_met_{end}"
_CAP_BOT = "bot_via_S_top_met_{end}"


def _cap_glayers(pdk):
    """(capa de la placa superior, capa de la inferior) segun el PDK.

    No se escriben a mano: gf180 ofrece el MIM entre met2/met3 (opcion A) o
    entre met4/met5 (opcion B), y son excluyentes a nivel de proceso. Suponer
    una deja el ruteo aterrizando dos niveles por debajo de la placa, sin via
    que lo salve y sin error -- el condensador queda flotando.
    """
    g = pdk.get_grule("capmet")
    return (pdk.layer_to_glayer(g["capmettop"]),
            pdk.layer_to_glayer(g["capmetbottom"]))


def _wire_lif(pdk, top, nfets, caps, m5_ref, drain_routes, plan,
              via_stack, rectangle, evaluate_bbox):
    """Fan-out and membrane node, both on met2.

    met3 is taken end to end by the per-inverter columns, so a horizontal run
    there would touch every one of them. The obvious way out was met4, above
    everything -- but the channel between the bottom band and M5 is empty on
    met2 as well, and going down instead of up leaves met4 to the
    mimcap, whose bottom plate lives there under option B.

    It also falls out of one rule instead of a decision per wire: met2 runs
    horizontal, met3 runs vertical. Every crossing then lands on a different
    layer by construction.
    """
    m2 = pdk.get_glayer("met2")
    m3 = pdk.get_glayer("met3")
    width = float(pdk.get_grule("met2")["min_width"])
    width_v = float(pdk.get_grule("met3")["min_width"])
    climb = via_stack(pdk, "met2", "met3")
    vw, vh = evaluate_bbox(climb)

    def strip(a, b, capa=None):
        """Un tramo, con la capa que le toca por su direccion.

        Bajar TODO a met2 es lo que rompe: el tramo vertical que va de la
        pista al banco de condensadores cruza las placas inferiores, que son
        met2 y estan a VSS, y funde la membrana con el riel. La regla tiene
        que ser por direccion, no por funcion.
        """
        horizontal = abs(b[0] - a[0]) >= abs(b[1] - a[1])
        if capa is not None:
            layer, w = pdk.get_glayer(capa), float(pdk.get_grule(capa)["min_width"])
        else:
            layer = m2 if horizontal else m3
            w = width if horizontal else width_v
        rect = top << rectangle(
            size=pdk.snap_to_2xgrid([abs(b[0] - a[0]) + w,
                                     abs(b[1] - a[1]) + w]),
            layer=layer, centered=True)
        _center_on(rect, pdk.snap_to_2xgrid((a[0] + b[0]) / 2),
                   pdk.snap_to_2xgrid((a[1] + b[1]) / 2))

    def land(x, y, hasta="met3"):
        pila = climb if hasta == "met3" else via_stack(pdk, "met2", hasta)
        _center_on(top << pila, pdk.snap_to_2xgrid(x), pdk.snap_to_2xgrid(y))
        return (pdk.snap_to_2xgrid(x), pdk.snap_to_2xgrid(y))

    # Both inter-band nets run in the gap between the bottom band and M5,
    # on separate tracks. Routing the fan-out down at gate level instead --
    # the obvious choice, since that is where the gate ports are -- puts a
    # met4 line straight across the nfets, exactly where their sources have
    # to drop to VSS. The met3 column of a gate spans the whole cell height,
    # so it can be tapped up here just as well.
    lower, middle, upper = plan.bands
    gap_lo = lower.y + lower.height / 2
    gap_hi = middle.y - middle.height / 2
    # El paso lo fija la PILA DE VIAS, no la pista: los cuadrados de 0.5 um
    # de cada aterrizaje son lo que se acerca entre pistas vecinas, no los
    # 0.28 del conductor. Dimensionarlo con el ancho de pista deja 0.18 um
    # donde la capa pide mas.
    sep = float(pdk.get_grule("met2")["min_separation"])
    pitch = vh + sep
    # Y hay que separarse tambien de los BORDES del canal, no solo entre
    # pistas: los anillos de guarda que lo limitan -- el de los nfets abajo,
    # el de M5 arriba -- son met2, la misma capa en la que corren ahora estas
    # dos. Con met4 eso daba igual y el par se centraba en el canal a secas;
    # asi, el pad de una pila quedaba a 0.26 um del anillo donde M2.2a pide
    # 0.28, y la membrana salia soldada al riel por dos centesimas.
    # Y el borde se toma de los ANILLOS, no de la frontera de banda: la banda
    # del planificador va mas arriba que el metal del anillo, asi que restarle
    # margen a `gap_hi` deja la pila donde ya estaba.
    margen = vh / 2 + sep
    techo = float(m5_ref.ports["tie_S_top_met_S"].center[1])
    suelo = max(float(r.ports["tie_N_top_met_N"].center[1]) for r in nfets)
    lo, hi = suelo + margen, techo - margen
    if caps:
        # El suelo lo marcan los nfet... salvo cuando el banco crece mas que
        # ellos. Con Cm grande la placa superior sube por encima de la banda,
        # y como la pista de membrana comparte SU capa, la separacion de esa
        # capa decide donde puede ir la pista. Misma red, asi que el corto no
        # es el problema: lo es la regla, que se mide igual entre poligonos
        # del mismo nodo.
        g_top = _cap_glayers(pdk)[0]
        regla = pdk.get_grule(g_top)
        placa = max(float(c.ports[_CAP_TOP.format(end="N")].center[1])
                    for c in caps)
        lo = max(lo, placa + float(regla["min_separation"])
                 + float(regla["min_width"]) / 2)
    # La pista de membrana sube a met3 sobre el primer condensador, asi que su
    # pila queda ENCIMA de la placa inferior y MIM.1 se mide en vertical: 1.2
    # um desde el borde alto de la placa hasta el pad, no solo de lado.
    # Sin margen vertical contra las placas: la pista de membrana corre por
    # la capa de la placa SUPERIOR y la separacion de MIM.1 se mide contra la
    # INFERIOR, que es otra capa. Quien si tiene que apartarse es la pila de
    # la esquina, que atraviesa met4 -- y por eso va donde no hay cap debajo.
    centro = (lo + hi) / 2
    y_fan = pdk.snap_to_2xgrid(centro - pitch / 2)
    y_mem = pdk.snap_to_2xgrid(centro + pitch / 2)

    # --- fan-out: inv0 drives inv1 and inv2 --------------------------------
    # The drain's met3 column is NOT above its port -- c_route leaves eastward
    # before climbing -- so its x comes from the route's own bbox. A gate's
    # column does sit on its port, because that link is a straight run up the
    # device centre.
    src = land(float(drain_routes[0].xmax) - width / 2, y_fan)
    loads = [land(float(nfets[i].ports[_GATE_MID.format(side="S")].center[0]), y_fan)
             for i in (1, 2)]
    strip(src, loads[-1])

    # --- membrane: M5 drain, inv0 gate, cap top plates ---------------------
    # inv0's gate column already crosses the M5 band on met3, and M5's drain
    # is met2 directly under it, so one via joins them with no route at all.
    gate_x = float(nfets[0].ports[_GATE_MID.format(side="S")].center[0])
    drain_n = m5_ref.ports[_DRAIN_MID.format(side="N")]
    bridge = via_stack(pdk, "met2", "met3")
    _center_on(top << bridge, pdk.snap_to_2xgrid(gate_x),
               pdk.snap_to_2xgrid(float(drain_n.center[1])
                                  - evaluate_bbox(bridge)[1] / 2))

    # --- feedback: inv1's output drives M5's gate --------------------------
    # M5's gate is a met2 strip running the length of the device, and inv1's
    # drain column crosses it on met3 on its way between the bands. So this
    # needs one via and no route at all, same as the membrane bridge above.
    # inv0 and inv2 cross it too; only inv1 gets a via.
    gate_m5 = m5_ref.ports[_GATE_MID.format(side="W")]
    tap = via_stack(pdk, "met2", "met3")
    _center_on(top << tap,
               pdk.snap_to_2xgrid(float(drain_routes[1].xmax) - width / 2),
               pdk.snap_to_2xgrid(float(gate_m5.center[1])))

    # Las placas superiores YA son met3, asi que se unen entre si en su propia
    # capa: nada de subir a met4 desde met3 para volver a bajar en el cap de
    # al lado. Se ahorra una pila de vias por cap y la tira de met4.
    # El puente corre por la capa de la placa superior, sea cual sea: asi se
    # funde con ella y no hace falta via sobre el FuseTop. Con el MIM en
    # met2/met3 esa capa es met3 y coincide con la vertical de la disciplina;
    # con el MIM en met4/met5 el puente sube a met5 y el vertical le lleva.
    g_top, _ = _cap_glayers(pdk)
    m3 = pdk.get_glayer(g_top)
    w3 = float(pdk.get_grule(g_top)["min_width"])
    izq, der = caps[0], caps[-1]
    y_cap = float(izq.ports[_CAP_TOP.format(end="E")].center[1])
    # de borde OESTE del primero a borde ESTE del ultimo, para cruzar las tres
    # placas por encima. Al reves la tira pasa por los huecos y no toca ninguna.
    x0 = float(izq.ports[_CAP_TOP.format(end="W")].center[0])
    x1 = float(der.ports[_CAP_TOP.format(end="E")].center[0])
    # La subida a met3 va sobre el PRIMER condensador, a media placa. Llegando
    # ya en met3 no hace falta via sobre el FuseTop: el vertical baja y se
    # funde con la placa superior, que es de su misma capa. Y aterrizar en
    # mitad de la placa reparte mejor que entrar por un borde.
    # La via en si queda muy por encima del FuseTop -- en el canal -- asi que
    # tampoco cae en la exclusion de conectividad del deck de LVS.
    # Con la placa en la capa vertical basta con caer a media placa: el
    # metal se funde y no hay via. En cualquier otro caso hace falta una, y
    # tiene que quedar FUERA del FuseTop, asi que se busca el hueco entre la
    # primera y la segunda placa. Con un solo cap no hay hueco y se sale por
    # el oeste, mas alla del borde.
    if True:
        x_sube = pdk.snap_to_2xgrid(float(izq.center[0]))
    else:
        # La pila crea su propio pad en la capa de la placa inferior, asi que
        # tiene que guardarle MIM.1 -- 1.2 um -- igual que cualquier otro
        # poligono de esa capa. En el hueco entre placas no cabe: ese hueco ES
        # 1.2 um, el minimo, y el pad quedaria a 0.35 de cada lado. Va al
        # OESTE del banco, donde solo tiene una placa de la que apartarse y el
        # canal entre inversores y condensadores esta vacio.
        mim1 = float(pdk.get_grule("capmet")["min_separation"])
        x_sube = pdk.snap_to_2xgrid(float(izq.xmin) - mim1 - vw / 2)
    # El puente se estira hasta donde baje la membrana, que puede quedar al
    # oeste de la primera placa.
    xa, xb = min(x0, x_sube), max(x1, x_sube)
    puente = top << rectangle(size=pdk.snap_to_2xgrid([abs(xb - xa) + w3, w3]),
                              layer=m3, centered=True)
    _center_on(puente, pdk.snap_to_2xgrid((xa + xb) / 2),
               pdk.snap_to_2xgrid(y_cap))

    # De ahi al inversor. La transicion de capa se hace FUERA del banco: sobre
    # el cap no se puede bajar a met2 porque MIM.1 pide 1.2 um entre la placa
    # inferior y cualquier otro met2, y la superior cae dentro de esa huella.
    # El tramo largo de la membrana sube a met4. Es la red sensible de la
    # celda -- el nodo de integracion que fija la frecuencia -- y met2 es el
    # carril mas poblado. Arriba corre sola, con menos vecinos que le acoplen.
    # Solo se puede cuando el MIM NO esta en met4: alli met4 es la placa
    # inferior y la pista tendria que guardarle MIM.1 en todo su recorrido.
    # La membrana corre por la capa de la placa superior. Asi llega al banco
    # y se funde con las placas sin una sola via, que es lo que hacia la
    # opcion A cuando esa capa era met3. Con el MIM arriba la pista sube a
    # met5 y se lleva de paso la ventaja: sale del carril met2, que es el mas
    # poblado, y la red sensible de la celda deja de tener vecinos que le
    # acoplen.
    via_mem = g_top
    a = land(gate_x, y_mem, hasta=via_mem)
    # El puente sigue en met3 hasta SALIR del banco por el oeste, y solo
    # entonces baja a met2. Bajar encima del cap cruza la placa inferior, que
    # es VSS: MIM.4 dentro de la huella y MIM.1 justo encima. Se entra por un
    # extremo (la membrana, oeste) y se sale por el otro (VSS, sur).
    # La transicion a met4 va en el HUECO entre el primer y el segundo cap, no
    # encima de una placa. El deck de LVS descarta del grafo de conectividad
    # cualquier via que solape el FuseTop --
    #     via3_n_cap = via3.not(fusetop)
    # -- asi que una pila puesta sobre la placa deja la membrana desconectada
    # para el extractor aunque el metal se toque.
    # La esquina lleva su propia pila: es donde el tramo horizontal de met2
    # entrega al vertical de met3. Esta al oeste del banco, fuera de la huella
    # de MIM.1, asi que el met2 nunca llega a acercarse a una placa inferior.
    # De ahi baja en met3 y entra directo en el puente.
    # La esquina NO lleva pila: los dos tramos son la capa de la placa, asi
    # que es un simple doblez. Ponerle una la hace atravesar met1..met4 y
    # tocar lo que haya debajo -- que aqui es la columna del ultimo inversor.
    esquina = (pdk.snap_to_2xgrid(x_sube), pdk.snap_to_2xgrid(y_mem))
    strip(a, esquina, capa=via_mem)
    strip(esquina, (pdk.snap_to_2xgrid(x_sube), pdk.snap_to_2xgrid(y_cap)),
          capa=via_mem)

    # Si la placa superior NO es la capa vertical de la disciplina, el tramo
    # anterior deja la membrana dos niveles por debajo del puente y hay que
    # salvar. La pila no puede caer sobre el FuseTop: el deck de LVS descarta
    # del grafo de conectividad las vias que lo solapan --
    #     via4_n_cap = via4.not(fusetop)
    # -- asi que el condensador quedaria flotando para el extractor aunque el
    # metal se toque. Va en el hueco entre placas, que es donde no hay ninguna.
    # Sin pila al llegar: la pista YA es la capa de la placa.


def _pin_labels(pdk, top, rectangle, nfets, pfets, caps, m5_ref, rails,
                drain_routes):
    """Marcas de pin para que el LVS sepa como se llama cada red.

    En gf180 met*_pin y met*_label son la MISMA capa, y no conduce: la marca
    tiene que caer ENCIMA de metal que ya exista, o el extractor no encuentra
    conductor bajo el texto y la red sale sin nombre. Y centrada sobre el
    punto, no alineada por un borde -- el centro de un puerto esta en el borde
    de su metal y mirando hacia afuera, asi que alinear por ahi deja la marca
    tangente. Es la leccion del PR 103 en diff_pair.
    """
    lado = 0.27

    def marca(glayer, texto, x, y):
        capa = pdk.get_glayer(glayer + "_pin")
        m = top << rectangle(size=(lado, lado), layer=capa, centered=True)
        _center_on(m, pdk.snap_to_2xgrid(x), pdk.snap_to_2xgrid(y))
        top.add_label(text=texto, layer=capa,
                      position=(pdk.snap_to_2xgrid(x), pdk.snap_to_2xgrid(y)))

    riel = rails["glayer"]
    ancho = float(pdk.get_grule(riel)["min_width"])
    medio = float(nfets[1].center[0])
    marca(riel, "Vdd", medio, rails["vdd"])
    marca(riel, "Vss", medio, rails["vss"])

    # Iin es la membrana, y se marca sobre la placa superior del primer cap.
    # La capa sale del PDK: met3 con el MIM en met2/met3, met5 con el en
    # met4/met5. Escribirla a mano deja la marca flotando sobre una capa
    # vacia, el extractor no encuentra conductor bajo el texto y la red sale
    # sin nombre -- que es como el LVS lo reporta: "missing top-level pin".
    g_top = _cap_glayers(pdk)[0]
    p = caps[0].ports[_CAP_TOP.format(end="E")]
    marca(g_top, "Iin", float(p.center[0]) - ancho, float(p.center[1]))
    # spike y spike_neg van sobre la RUTA del drenador, no sobre el puerto
    # _DRAIN_MID: en un fet de un dedo ese puerto comparte el x del centro
    # del dispositivo con la puerta, y por ahi corre la columna de met3 que
    # une las puertas -- que en el inversor 0 es la membrana. La marca caia
    # ahi y nombraba la red equivocada. El drenador sale por el ESTE con un
    # c_route, y ese es el conductor que hay que nombrar.
    #
    # netcheck no lo veia porque camina el metal y no mira etiquetas; el LVS
    # lo reporto en su primera ejecucion como "extra top-level pin".
    w3 = float(pdk.get_grule("met3")["min_width"])
    for nombre, ref, ruta in (("spike_neg", nfets[0], drain_routes[0]),
                              ("spike", nfets[2], drain_routes[2])):
        d = ref.ports[_DRAIN_MID.format(side="E")]
        marca("met3", nombre, float(ruta.xmax) - w3 / 2, float(d.center[1]))


def _into_metal_xy(port, w, h):
    """Offset so a via stack lands on the port's metal rather than past it."""
    angle = (port.orientation or 0) % 360
    if 45 < angle < 135:
        return (0.0, -h / 2)
    if 225 < angle < 315:
        return (0.0, +h / 2)
    if 135 <= angle <= 225:
        return (+w / 2, 0.0)
    return (-w / 2, 0.0)


def _free_x(obstacles, lo, hi, need):
    """Widest window in [lo, hi] that no obstacle x-interval covers.

    The VSS drop from M5 has to cross the bottom band, so where it can go
    depends on what is placed there -- which moves when the caller changes
    M5's length or the cap size. Compute the corridor, do not hardcode it.
    """
    best, cur = None, lo
    for a, b in sorted(obstacles):
        if a - cur >= need and (best is None or a - cur > best[1] - best[0]):
            best = (cur, a)
        cur = max(cur, b)
    if hi - cur >= need and (best is None or hi - cur > best[1] - best[0]):
        best = (cur, hi)
    return best


def _rails_bands(pdk, top, pfets, nfets, plan, via_stack, rectangle,
                 evaluate_bbox, supply_width=1.0, m5_ref=None, caps=()):
    """VDD over the pfet band, VSS under the nfet band, on met4.

    The drops are short because the bands are ordered so each device type
    faces its own rail: a pfet's source_N points up at VDD, an nfet's
    source_S down at VSS. That ordering is not free -- it is why M5 sits
    between the two halves of every inverter -- but it makes the supply
    trivial, which is most of the wiring in the cell.
    """
    # Supply runs carry the whole cell's current, so they are sized rather
    # than left at minimum width -- both the rails and the drops that feed
    # them. Minimum-width metal is for signals.
    rails = plan.rails
    layer = pdk.get_glayer(rails.glayer)
    width = max(supply_width, float(pdk.get_grule(rails.glayer)["min_width"]))

    lower, _, upper = plan.bands
    # rails.band was sized for a minimum-width rail. Keep the clearance it
    # asked for and push the wider rail outward, rather than letting the extra
    # width eat into the gap to the band.
    grow = width - rails.width
    y_vdd = pdk.snap_to_2xgrid(upper.y + upper.height / 2 + rails.band + grow
                               - width / 2)
    y_vss = pdk.snap_to_2xgrid(lower.y - lower.height / 2 - rails.band - grow
                               + width / 2)
    for y in (y_vdd, y_vss):
        strap = top << rectangle(
            size=pdk.snap_to_2xgrid([plan.width, width]),
            layer=layer, centered=True)
        _center_on(strap, pdk.snap_to_2xgrid(plan.width / 2), y)

    from glayout.routing.straight_route import straight_route

    tie_top = "met2"
    clear = float(pdk.get_grule(rails.glayer)["min_separation"]) + width / 2

    def tie_to_rail(ref, y_rail, end):
        """Source -> guard ring -> rail.

        Not source -> rail directly. The ring sits immediately west of the
        device and its west face is one port 4.1 um tall, so reaching it is a
        short straight run across ground nobody else uses -- the gate column
        goes up the middle and the drain column east of it. Dropping from the
        source instead means threading a met4 line down the height of the
        cell, which is what crossed the fan-out and membrane tracks and merged
        them into the supply.

        """
        src = ref.ports[SOURCE.format(side="W")]
        ring_in = ref.ports["tie_W_top_met_E"]
        top << straight_route(pdk, src, ring_in)

        out = ref.ports[f"tie_{end}_top_met_{end}"]
        # From met2, not met1. tie_layers=(horizontal, vertical) puts the
        # ring's N and S edges on the first layer, so climbing from met1 here
        # would add a via1 alongside the one the ring already has -- they land
        # 0.258um apart and V1.2a wants 0.26.
        climb1 = via_stack(pdk, tie_top, rails.glayer)
        w1, h1 = evaluate_bbox(climb1)
        dx, dy = _into_metal_xy(out, w1, h1)
        x = pdk.snap_to_2xgrid(float(out.center[0]) + dx)
        y = pdk.snap_to_2xgrid(float(out.center[1]) + dy)
        _center_on(top << climb1, x, y)
        rect = top << rectangle(
            size=pdk.snap_to_2xgrid([width, abs(y_rail - y)]),
            layer=layer, centered=True)
        _center_on(rect, x, pdk.snap_to_2xgrid((y_rail + y) / 2))

    def drop(port, y_rail, x=None, reach_first=False, desde="met2",
             entrar=True):
        """Salva de una capa a la del riel y baja con una correa ancha.

        `desde` es la capa del puerto de partida. Casi siempre met2, pero la
        placa inferior del mimcap sale por la capa de la placa superior, que
        puede estar por ENCIMA del riel -- con el MIM en met4/met5 la pila va
        hacia abajo, no hacia arriba. via_stack quiere (inferior, superior),
        asi que se ordenan.

        reach_first mantiene la correa en `desde` hasta el riel y salva alli.
        Se usa donde la pila caeria dentro de un bloque: sobre un mimcap el
        met3 de la pila pasa a 0.09 um de la placa superior, que es la
        membrana -- un corto esperando, no solo un M3.2a.
        """
        orden = ("met1", "met2", "met3", "met4", "met5")
        a, b = sorted((desde, rails.glayer), key=orden.index)
        climb = via_stack(pdk, a, b)
        w, h = evaluate_bbox(climb)
        dx, dy = _into_metal_xy(port, w, h)
        if not entrar:
            # El desplazamiento "hacia dentro del metal" busca que la pila
            # quede sobre conductor. En la extension del mimcap eso empuja la
            # correa hacia la placa superior, que esta a 0.6 um: el borde
            # acaba rozandola y funde las dos placas. Aqui se sale recto.
            dy = 0.0
        px = pdk.snap_to_2xgrid(float(port.center[0]) + dx if x is None else x)
        py = pdk.snap_to_2xgrid(float(port.center[1]) + dy)
        if reach_first:
            strap = top << rectangle(
                size=pdk.snap_to_2xgrid([width, abs(y_rail - py) + h]),
                layer=pdk.get_glayer(desde), centered=True)
            _center_on(strap, px, pdk.snap_to_2xgrid((y_rail + py) / 2))
            py = y_rail
        _center_on(top << climb, px, py)
        rect = top << rectangle(size=pdk.snap_to_2xgrid([width, abs(y_rail - py) + h]),
                                layer=layer, centered=True)
        _center_on(rect, px, pdk.snap_to_2xgrid((y_rail + py) / 2))

    def _correa_met1(port, y_rail, x):
        """Correa vertical de alimentacion en met1, de un anillo al riel.

        met1 es la capa mas resistiva, asi que se compensa con ancho: esto
        lleva corriente de bulk, no una señal. A cambio no estorba a nadie --
        en el canal met1 esta tan libre como met2 y no compite con la
        disciplina de direcciones.
        """
        ancho = max(width, 3 * float(pdk.get_grule("met1")["min_width"]))
        py = pdk.snap_to_2xgrid(float(port.center[1]))
        px = pdk.snap_to_2xgrid(x)
        strap = top << rectangle(
            size=pdk.snap_to_2xgrid([ancho, abs(y_rail - py)]),
            layer=pdk.get_glayer("met1"), centered=True)
        _center_on(strap, px, pdk.snap_to_2xgrid((y_rail + py) / 2))
        # y sube al riel solo al final
        remate = via_stack(pdk, "met1", rails.glayer)
        _center_on(top << remate, px, pdk.snap_to_2xgrid(y_rail))

    if m5_ref is not None:
        # M5 sits in the middle band but its source and bulk belong to VSS at
        # the bottom, so this drop has to cross the bottom band. Send it down
        # the widest gap between the blocks placed there.
        top << straight_route(pdk, m5_ref.ports[SOURCE.format(side="W")],
                              m5_ref.ports["tie_W_top_met_E"])
        blocked = [(float(r.bbox[0][0]) - clear, float(r.bbox[1][0]) + clear)
                   for r in list(nfets) + list(caps)]
        ring = m5_ref.ports["tie_S_top_met_S"]
        lo = float(ring.center[0]) - ring.width / 2 + width / 2
        hi = float(ring.center[0]) + ring.width / 2 - width / 2
        window = _free_x(blocked, lo, hi, width)
        if window is not None:
            # Esta correa es la unica que cruza el canal, y por ahi corren
            # ahora la membrana y el fan-out en met2. Va por met1: la regla es
            # met1 y met3 verticales, met2 horizontal, asi que una vertical no
            # tiene nada que hacer en met2. Y el anillo ya lleva met1 debajo
            # -- tie_layers=(met2, met1) -- de modo que en el origen no hace
            # falta ninguna via nueva.
            _correa_met1(ring, y_vss, (window[0] + window[1]) / 2)
        else:
            # No corridor -- a short M5 shrinks the cell until the bottom band
            # fills it. Hop to the nfet's ring instead: both are pwell taps on
            # VSS, that ring is already strapped to the rail, and it sits
            # directly below by construction, so this route always exists.
            # Longer electrically than going straight to the rail, which is
            # why it is the fallback and not the rule.
            near = min(nfets, key=lambda r: abs(float(r.center[0])
                                                - float(ring.center[0])))
            up = near.ports["tie_N_top_met_N"]
            x = pdk.snap_to_2xgrid(float(up.center[0]))
            # Both ports sit ON the edge of their ring, so a rectangle drawn
            # between the two centres merely abuts them -- and after snapping
            # it can fall a few nm short and leave a gap that reads as met2
            # spacing. Overrun into each ring instead.
            # En met1, igual que la correa del corredor: este salto cruza el
            # canal de lado a lado, y en met2 se lleva por delante la membrana
            # y el fan-out. El anillo de M5 ya tiene su recorrido en met1, asi
            # que arriba enchufa directo; abajo hace falta una via porque el
            # borde norte del anillo del nfet si es met2.
            solape = float(pdk.get_grule("met1")["min_width"])
            y0 = float(up.center[1]) - solape
            y1 = float(ring.center[1]) + solape
            hop = top << rectangle(
                size=pdk.snap_to_2xgrid([width, abs(y1 - y0)]),
                layer=pdk.get_glayer("met1"), centered=True)
            _center_on(hop, x, pdk.snap_to_2xgrid((y0 + y1) / 2))
            # Sin via propia: el anillo del nfet ya lleva met1 bajo todo su
            # perimetro, asi que el salto entra por su misma capa. Ponerle una
            # aqui la deja a 0.258 um de las que el anillo ya tiene, y V1.2a
            # pide 0.26 -- la misma trampa que documenta tie_to_rail.

    for ref in caps:
        # bottom plate to VSS; the top plate is already on the membrane
        # La placa inferior sale por la extension sur, ya subida a la capa
        # de la placa superior. Con el MIM arriba eso queda por encima del
        # riel y la pila baja; drop lo resuelve por si sola.
        g_top, _ = _cap_glayers(pdk)
        drop(ref.ports[_CAP_BOT.format(end="S")], y_vss,
             reach_first=True, desde=g_top, entrar=False)

    for ref in pfets:
        tie_to_rail(ref, y_vdd, "N")
    for ref in nfets:
        tie_to_rail(ref, y_vss, "S")

    return {"vdd": y_vdd, "vss": y_vss, "width": width,
            "glayer": rails.glayer}

def _boundary(pdk, top, rectangle):
    """Marca el contorno del macro en la capa (0,0).

    LibreLane no deduce donde acaba un bloque mirando su metal: lee esta
    capa. No se fabrica -- es una marca de contorno, como el PR_boundary de
    otros flujos -- y el equipo la ha fijado para todas las celdas del
    D14_topcell.

    Se dibuja despues de llevar la celda al origen, asi que va de (0,0) a la
    esquina opuesta y coincide exactamente con lo que el LEF va a declarar.
    """
    ancho = float(top.xmax - top.xmin)
    alto = float(top.ymax - top.ymin)
    marco = top << rectangle(size=(ancho, alto), layer=(0, 0), centered=False)
    marco.movex(float(top.xmin)).movey(float(top.ymin))
    return marco


def _al_origen(top, rails_y):
    """Lleva la esquina inferior izquierda de la celda a (0, 0).

    Un macro se integra por su LEF, que declara un origen. Si la geometria
    vive en (0, -2.21) y el LEF dice (0, 0), la herramienta coloca el bloque
    creyendo una cosa y el metal aparece desplazado: pistas que no conectan
    y violaciones en el borde, y no al colocar sino despues de rutear.

    Va aqui, despues de los rieles y antes de los puertos y las etiquetas:
    las referencias arrastran sus puertos al moverse, pero `rails_y` lleva
    coordenadas absolutas en float que no se enteran, asi que se corrigen a
    mano. Las etiquetas de pin todavia no existen y se dibujaran ya en su
    sitio.
    """
    dx, dy = top.bbox[0]
    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        return rails_y
    for ref in top.references:
        ref.movex(-dx).movey(-dy)
    corregido = dict(rails_y)
    for k in ("vdd", "vss"):
        corregido[k] = float(rails_y[k]) - dy
    return corregido


# Los inversores del lazo van al minimo: el solver no los dimensiona porque
# no fijan nada del comportamiento, a diferencia de M5 y del buffer.
INVERSOR_MINIMO = dict(width=0.22, length=0.28)

FET_POR_DEFECTO = dict(multipliers=1, fingers=1, with_substrate_tap=False,
                       with_dummy=False, tie_layers=("met2", "met1"), sd_rmult=1)

CAPS = 3          # la membrana se reparte en tres MIM, uno por hueco de banda

# MIM.8a: el area del FuseTop no puede bajar de 25 um2, y el `size` de mimcap
# ES el FuseTop, asi que 5 um de lado es el minimo absoluto de un MIM.
LADO_MINIMO = 5.0


# Paso al que sale dibujada una dimension centrada: el GDS se escribe a 0.005
# um y tanto la placa del MIM como el canal de un FET van centrados, asi que
# cada borde cae en media unidad. `snap_to_2xgrid` no basta porque usa
# `pdk.grid_size`, que en gf180 dice 0.001.
REJILLA_DIBUJO = Decimal("0.01")


def en_rejilla(valor: float) -> float:
    """Dimension [um] que se dibuja exactamente como se pide.

    Sin esto lo pedido y lo dibujado divergen en menos de una centesima y el
    LVS lo ve: un MIM de 5.864 sale de 5.87 y su area no es la que declara el
    netlist; un M5 de 1.671 sale de 1.68 y el comparador marca el ancho.

    Se redondea hacia ARRIBA, como `snap_to_2xgrid`, para no perder ni
    capacidad ni corriente respecto a lo que el solver pidio.
    """
    return float(REJILLA_DIBUJO
                 * (Decimal(str(valor)) / REJILLA_DIBUJO).quantize(
                     1, rounding=ROUND_UP))


def from_design(pdk, design, mim: str = mim_pdk.POR_DEFECTO,
                fet: dict | None = None, rail_layer: Optional[str] = RIEL_POR_DEFECTO,
                name: str = "lif"):
    """Construye la celda que describe un NeuronDesign.

    Es la union entre la capa que resuelve el comportamiento y la que dibuja.
    Devuelve (componente, handles, notas); las notas dicen que se perdio al
    pasar de un numero continuo a geometria, que es donde se va la precision.

    El unico parametro que no sale del diseño es `mim`: cual de las tres
    opciones de MIM corre la fabrica es una decision de proceso, y cambia
    cuanta area hace falta para la misma Cm. Ver mim.py.
    """
    fet = dict(FET_POR_DEFECTO if fet is None else fet)
    p = design.params
    notas = []

    # Repartir la membrana en varios MIM ahorra area muerta, pero cada uno
    # tiene que seguir siendo legal: se baja el numero hasta que el lado
    # llegue al minimo.
    n = CAPS
    while n > 1 and mim_pdk.lado_para(p["Cm"], mim=mim, n=n) < LADO_MINIMO:
        n -= 1
    lado = mim_pdk.lado_para(p["Cm"], mim=mim, n=n)
    if lado < LADO_MINIMO:
        notas.append(Note(
            Severity.WARNING, "Cm",
            "%.1f fF cabe en menos de un MIM minimo; se usa uno de %.1f um "
            "y la membrana sube a %.1f fF"
            % (p["Cm"], LADO_MINIMO, mim_pdk.capacidad(LADO_MINIMO, mim, 1)),
            chain="MIM.8a: area de FuseTop >= 25 um2"))
        lado = LADO_MINIMO
    lado_real = en_rejilla(lado)
    cm_real = mim_pdk.capacidad(lado_real, mim=mim, n=n)
    error = (cm_real - p["Cm"]) / p["Cm"]
    notas.append(Note(
        Severity.INFO if abs(error) < 0.02 else Severity.WARNING, "Cm",
        "pedida %.1f fF -> %d MIM de %.3f um de lado = %.1f fF (%+.1f%%), "
        "con %s" % (p["Cm"], n, lado_real, cm_real, 100 * error,
                    mim_pdk.modelo(pdk, mim)),
        chain="snap a rejilla del lado del MIM"))

    # Las dimensiones que de verdad se dibujan. El netlist de referencia lee
    # de aqui, no de design.params: si declarase lo pedido, el LVS marcaria la
    # diferencia de rejilla como un ancho que no casa.
    dims = {k: en_rejilla(p[k]) for k in ("W_reset", "L_reset", "W_buf")}
    dims.update(W_inv=en_rejilla(INVERSOR_MINIMO["width"]),
                L_inv=en_rejilla(INVERSOR_MINIMO["length"]))

    top, handles = lif_cell(
        pdk,
        inverter=dict(INVERSOR_MINIMO, width=dims["W_inv"],
                      length=dims["L_inv"], **fet),
        m5=dict(width=dims["W_reset"], length=dims["L_reset"], **fet),
        output_inverter=dict(width=dims["W_buf"],
                             length=dims["L_inv"], **fet),
        cap_size=lado_real, n_caps=n, rail_layer=rail_layer, name=name)
    handles["dims"] = dims
    handles["Cm_real"] = cm_real
    handles["mim"] = mim_pdk.modelo(pdk, mim)
    handles["cap_lado"] = lado_real
    return top, handles, notas
