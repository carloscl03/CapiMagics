"""Build the LIF cell at several sizes and check each one is really a LIF.

Run inside the container:

    GLAYOUT_BACKEND=gdstk python check.py

The dimensions come from the characterisation layer, so the generator has to
hold up across the range those laws produce, not just at one point. For every
size this runs DRC *with the MIM rules enabled* -- the gf180 deck defaults
mim_option to "Nan" and silently skips the whole MIM section otherwise -- and
then checks the six nets of the LIF topology by walking the metal.

What is being asserted, per the netlist:

    integration  M5 drain, inv0 gate, the cap top plates
    spike_neg    inv0 drain, inv1 gate, inv2 gate
    spike/reset  inv1 drain, M5 gate            <- the reset feedback
    spike        inv2 drain                     <- the cell output
    VDD          pfet sources, the top rail
    VSS          nfet sources, M5 source, the cap bottom plates, bottom rail

A net coming out merged with another is a short; one splitting in two is an
open. Both show up here as a set that does not match.
"""
import json
import os
import pathlib
import re
import subprocess
import sys

# El paquete se importa por su sitio en el disco, no por una ruta fija: asi
# esto corre igual desde el repo, desde un notebook o dentro del contenedor.
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))

from glayout import gf180                                       # noqa: E402

from lif_design.build import (lif_cell, _cap_glayers,           # noqa: E402
                              _CAP_TOP, _CAP_BOT)

def _deck():
    """El deck de DRC que trae el propio glayout instalado.

    Derivado de donde este el paquete, no una ruta fija: asi esto corre en la
    maquina de cualquiera y no solo en el contenedor donde se escribio.
    GF180_DRC lo sobreescribe si hace falta apuntar a otro.
    """
    import glayout
    return str(pathlib.Path(glayout.__file__).parent
               / "pdk" / "gf180_mapped" / "gf180mcu.drc")


DECK = os.environ.get("GF180_DRC") or _deck()
NETCHECK = str(AQUI / "netcheck.py")
SALIDA = os.environ.get("LIF_OUT", "/tmp")
# LIF_RAIL_LAYER fuerza la capa de los rieles en todo el barrido, para poder
# medir la celda entera en un stack de 3 metales. Sin la variable NO se pasa
# rail_layer, para que valga el defecto del paquete: pasar None pide la
# eleccion automatica, y esa mira la capa mas alta de la fila. Con el MIM en
# met4/met5 la mas alta es la placa superior y no queda piso encima, asi que
# levanta. La regla es conservadora -- los rieles corren por los extremos y
# no cruzan el banco -- pero no lo sabe.
RIEL = os.environ.get("LIF_RAIL_LAYER") or None
_RIEL_KW = {"rail_layer": RIEL} if RIEL else {}
FET = dict(multipliers=1, fingers=1, with_substrate_tap=False,
           with_dummy=False, tie_layers=("met2", "met1"), sd_rmult=1)

CASOS = [
    ("base",        dict(w_inv=0.22, l_inv=0.28, w_m5=1.25, l_m5=50.0, cap=5.0)),
    ("inv anchos",  dict(w_inv=1.00, l_inv=0.28, w_m5=1.25, l_m5=50.0, cap=5.0)),
    ("M5 corto",    dict(w_inv=0.22, l_inv=0.28, w_m5=1.25, l_m5=25.0, cap=5.0)),
    ("M5 ancho",    dict(w_inv=0.22, l_inv=0.28, w_m5=3.50, l_m5=50.0, cap=5.0)),
    ("cap grande",  dict(w_inv=0.22, l_inv=0.28, w_m5=1.25, l_m5=50.0, cap=8.0)),
    ("todo grande", dict(w_inv=1.00, l_inv=0.50, w_m5=3.50, l_m5=50.0, cap=8.0)),
    # esquina baja: M5 en los dos minimos a la vez. El anillo de M5 se queda
    # mas estrecho que el paso de las pistas, que es donde el ruteo aprieta.
    ("todo minimo", dict(w_inv=0.22, l_inv=0.28, w_m5=0.22, l_m5=20.0, cap=5.0)),
]

def esperado(n_caps):
    """Las seis redes del LIF. El numero de MIM no es fijo: baja cuando la
    membrana es pequeña, porque MIM.8a impide un FuseTop de menos de 25 um2."""
    arriba = {"cap%d_arriba" % i for i in range(n_caps)}
    abajo = {"cap%d_abajo" % i for i in range(n_caps)}
    return {
        "membrana":   {"M5_drain", "nfet0_gate", "pfet0_gate"} | arriba,
        "spike_neg":  {"nfet0_drain", "pfet0_drain",
                       "nfet1_gate", "pfet1_gate", "nfet2_gate", "pfet2_gate"},
        "realimenta": {"nfet1_drain", "pfet1_drain", "M5_gate"},
        "salida":     {"nfet2_drain", "pfet2_drain"},
        "VDD":        {"riel_VDD", "pfet0_source", "pfet1_source", "pfet2_source"},
        "VSS":        {"riel_VSS", "M5_source", "nfet0_source", "nfet1_source",
                       "nfet2_source"} | abajo,
    }

MET = {"met1": 34, "met2": 36, "met3": 42, "met4": 46, "met5": 81}


def sondas(handles, bbox):
    r = handles["rails"]
    L = MET[r["glayer"]]
    mid = float(bbox[0][0] + bbox[1][0]) / 2
    pr = {"riel_VDD": [L, 0, mid, r["vdd"]], "riel_VSS": [L, 0, mid, r["vss"]]}
    # Las capas del MIM salen del PDK: gf180 lo ofrece en met2/met3 o en
    # met4/met5 y son excluyentes. Con los numeros escritos a mano la sonda
    # cae en una capa vacia y la red sale "partida" sin que nada este mal.
    g_top, g_bot = _cap_glayers(gf180)
    l_top, l_bot = MET[g_top], MET[g_bot]
    for i, c in enumerate(handles["caps"]):
        q = c.ports[_CAP_TOP.format(end="S")]
        pr["cap%d_arriba" % i] = [l_top, 0, float(q.center[0]), float(q.center[1]) + 0.25]
        # la placa inferior se pincha en su metal, bajo la extension sur
        b = c.ports[_CAP_BOT.format(end="S")]
        pr["cap%d_abajo" % i] = [l_bot, 0, float(b.center[0]), float(b.center[1]) + 0.25]
    for tag, lst in (("nfet", handles["nfets"]), ("pfet", handles["pfets"])):
        for i, ref in enumerate(lst):
            for nombre, puerto in (("source", "multiplier_0_source_W"),
                                   ("drain", "multiplier_0_drain_W")):
                p = ref.ports[puerto]
                pr["%s%d_%s" % (tag, i, nombre)] = [
                    36, 0, float(p.center[0]) + 0.2, float(p.center[1])]
            g = ref.ports["multiplier_0_gate_S"]
            pr["%s%d_gate" % (tag, i)] = [
                36, 0, float(g.center[0]), float(g.center[1]) + 0.15]
    for nombre, puerto in (("source", "multiplier_0_source_W"),
                           ("drain", "multiplier_0_drain_W"),
                           ("gate", "multiplier_0_gate_W")):
        p = handles["m5"].ports[puerto]
        pr["M5_%s" % nombre] = [36, 0, float(p.center[0]) + 0.2, float(p.center[1])]
    return pr


def _mim_option(pdk):
    """A o B, segun donde ponga el PDK las placas del MIM.

    No se fija a mano: el deck de la opcion equivocada busca la placa
    inferior en la capa que no es, `mim_virtual` sale vacio, y MIM.3 acusa
    al condensador de no tener placa. Un falso positivo que parece un fallo
    de layout.
    """
    bottom = pdk.layer_to_glayer(pdk.get_grule("capmet")["capmetbottom"])
    return "A" if bottom == "met2" else "B"


def _metal_level(pdk):
    """Cuantos metales tiene la pila, como los nombra el deck.

    Hay que pasarlo: el deck del PDK asume 5LM si falta, pero la copia que
    trae glayout asume 6LM. Con 6LM el deck cree que la cima es metaltop, asi
    que `topmin1_via` pasa a ser via4 -- que es justo la via del MIM en
    opcion B -- y MIMTM.10 acusa al condensador de tener vias prohibidas
    dentro de si mismo. Ciento y pico violaciones que no existen.
    """
    n = sum(1 for i in range(1, 7) if "met%d" % i in pdk.glayers)
    return "%dLM" % n


def drc(gds, tag, pdk=gf180):
    rep = "%s/%s.lyrdb" % (SALIDA, tag)
    subprocess.run(["klayout", "-b", "-r", DECK, "-rd", "input=" + gds,
                    "-rd", "report=" + rep,
                    "-rd", "mim_option=" + _mim_option(pdk),
                    "-rd", "metal_level=" + _metal_level(pdk)],
                   capture_output=True)
    texto = open(rep).read()
    cuenta = {}
    for cat in re.findall(r"<category>'([^']+)'", texto):
        cuenta[cat] = cuenta.get(cat, 0) + 1
    return texto.count("<item>"), cuenta


def redes(gds, probes):
    salida = subprocess.run(["klayout", "-b", "-r", NETCHECK, "-rd", "gds=" + gds,
                             "-rd", "probes=" + probes],
                            capture_output=True, text=True).stdout
    grupos = []
    for linea in salida.splitlines():
        m = re.match(r"\s+(\S+)\s+(.+)$", linea)
        if m and "#" in m.group(1):
            grupos.append(set(m.group(2).split()))
    return grupos


# Las cuatro primeras barren frecuencia por la misma ruta del solver (f fija
# con Iex fija). Las tres siguientes entran por rutas distintas Y salen con
# geometrias que ninguna de las anteriores produce -- ese es el criterio para
# estar aqui, porque cada caso cuesta un DRC completo.
# Un objetivo de ganancia (freq_range e iex_range los dos en rango) NO esta:
# recorre codigo distinto en el solver pero resuelve por (f_hi, iex_hi), asi
# que da el mismo GDS que el caso de 800 kHz. Vive en el notebook.
ESPECIFICACIONES = [
    ("200 kHz",     dict(freq_range=200, iex_range=100)),
    ("300 kHz",     dict(freq_range=300, iex_range=100)),
    ("800 kHz",     dict(freq_range=800, iex_range=100)),
    ("2000 kHz",    dict(freq_range=2000, iex_range=100)),
    # el umbral entra en juego y arrastra Cm, o sea el numero de MIM
    ("umbral 2.0V", dict(freq_range=800, iex_range=100, vth=2.0)),
    # extremo bajo de corriente verificado: saca W_reset casi al minimo (0.222)
    ("Iex 5 nA",    dict(freq_range=300, iex_range=5)),
    # unica ruta que dimensiona el bufer de salida: W_buf sube y el
    # inversor de salida cambia de tamaño en el layout
    ("carga 800fF", dict(freq_range=800, iex_range=100, c_load=800)),
]


def desde_especificacion():
    """El camino completo: kHz y nA -> geometria -> GDS verificado."""
    from lif_design.spec import NeuronSpec
    from lif_design.solver import design as resolver
    from lif_design.build import from_design

    fallos = 0
    print("\n%-12s %-16s %5s  %s" % ("spec", "caja um", "DRC", "topologia"))
    print("-" * 74)
    for nombre, kw in ESPECIFICACIONES:
        tag = "spec_" + re.sub(r"\W+", "_", nombre)
        d = resolver(NeuronSpec(**kw))
        top, h, _ = from_design(gf180, d, name=tag, **_RIEL_KW)
        gds = "%s/%s.gds" % (SALIDA, tag)
        top.write_gds(gds)
        bb = top.bbox
        n, cats = drc(gds, tag)
        json.dump(sondas(h, bb), open("%s/%s.json" % (SALIDA, tag), "w"))
        grupos = redes(gds, "%s/%s.json" % (SALIDA, tag))
        malas = [red for red, quiero in esperado(len(h["caps"])).items()
                 if not any(g == quiero for g in grupos)]
        if malas or n:
            fallos += 1
        print("%-12s %6.2f x %6.2f  %5s  %s"
              % (nombre, bb[1][0] - bb[0][0], bb[1][1] - bb[0][1],
                 n if not n else "%d %s" % (n, cats),
                 " ".join(malas) if malas else "ok (%d MIM)" % len(h["caps"])))
    return fallos


def main():
    fallos = 0
    print("%-12s %-16s %5s  %s" % ("caso", "caja um", "DRC", "topologia"))
    print("-" * 74)
    for nombre, kw in CASOS:
        tag = "chk_" + re.sub(r"\W+", "_", nombre)
        try:
            top, h = lif_cell(
                gf180,
                inverter=dict(width=kw["w_inv"], length=kw["l_inv"], **FET),
                m5=dict(width=kw["w_m5"], length=kw["l_m5"], **FET),
                cap_size=kw["cap"], name=tag, **_RIEL_KW)
        except Exception as exc:
            print("%-12s no genera: %s" % (nombre, str(exc)[:52]))
            fallos += 1
            continue

        gds = "%s/%s.gds" % (SALIDA, tag)
        top.write_gds(gds)
        bb = top.bbox
        n, cats = drc(gds, tag)
        pr = sondas(h, bb)
        json.dump(pr, open("%s/%s.json" % (SALIDA, tag), "w"))
        grupos = redes(gds, "%s/%s.json" % (SALIDA, tag))

        malas = []
        for red, quiero in esperado(len(h["caps"])).items():
            if not any(g == quiero for g in grupos):
                encontrado = next((g for g in grupos if g & quiero), set())
                malas.append("%s(%s)" % (
                    red, "+".join(sorted(encontrado - quiero)) or "partida"))
        estado = "ok" if not malas and n == 0 else " ".join(malas) or "DRC"
        if malas or n:
            fallos += 1
        print("%-12s %6.2f x %6.2f  %5s  %s"
              % (nombre, bb[1][0] - bb[0][0], bb[1][1] - bb[0][1],
                 n if not n else "%d %s" % (n, cats), estado))
    fallos += desde_especificacion()
    print("\n%s" % ("todos los casos pasan" if not fallos
                    else "%d caso(s) con problemas" % fallos))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
