"""Resolucion por capas: intencion -> parametros.

El sistema NO es "spec -> parametros" sino un sistema de restricciones
parcialmente fijadas. W, L, Cm y W_M7M8 pueden venir dados o quedar libres, y
se resuelve solo lo libre.

Tres regimenes:
  sub-determinado  hay familia de soluciones -> se elige por criterio
  determinado      solucion unica
  sobre-determinado  puede no haber solucion -> se ajusta lo fijo (warning)
                     o se reporta la contradiccion (error)

Orden de ajuste cuando hay que tocar algo fijado, por coste de cambio:
  1. Cm      solo un capacitor
  2. L_M5    transistor largo
  3. W_M5    afecta mas al layout
W_M7M8 queda fuera de la cadena: depende solo del fan-out y no compite con la
frecuencia ni el threshold (la carga no afecta a f, <0.7%).
"""
from __future__ import annotations

import math

from . import laws as L
from .spec import NeuronDesign, NeuronSpec, Severity

# Punto nominal de la celda actual (sch/lif/neurona_input_current.sch).
# Es el unico con simulacion directa del circuito completo, asi que es el
# default mas honesto para "haz una neurona y ya".
NOMINAL = {"W_M5": 1.25, "L_M5": 50.0, "Cm": 150.0, "W_M7M8": 0.22}


def _clamp(v: float, lo: float, hi: float) -> tuple[float, bool]:
    """Devuelve (valor acotado, si hubo que acotarlo)."""
    if v < lo:
        return lo, True
    if v > hi:
        return hi, True
    return v, False


def design(spec: NeuronSpec) -> NeuronDesign:
    """Resuelve una especificacion. Nunca lanza; ver NeuronDesign.notes."""
    d = NeuronDesign(params={})

    # ---- caso trivial: sin objetivos -> punto nominal medido --------------
    if not spec.has_objectives() and not spec.fixed_dims():
        d.params = dict(NOMINAL)
        d.add(Severity.INFO, "diseño",
              "sin objetivos; se devuelve el punto nominal de la celda actual, "
              "que es el unico con simulacion directa del circuito completo")
        _predict(d, spec)
        return d

    # ---- capa 1: geometria (W, L) desde la frecuencia --------------------
    W, Lg = _solve_geometry(spec, d)

    # ---- capa 2: Cm desde el threshold -----------------------------------
    Cm = _solve_cm(spec, d, W, Lg)

    # ---- capa 3: buffer de salida (independiente) ------------------------
    w78 = _solve_buffer(spec, d)

    d.params = {"W_M5": round(W, 3), "L_M5": round(Lg, 2),
                "Cm": round(Cm, 1), "W_M7M8": round(w78, 3)}

    # ---- capa 4: validacion y prediccion ---------------------------------
    _validate(d, W, Lg, Cm, spec)
    _predict(d, spec)
    return d


# --------------------------------------------------------------------------
def _solve_geometry(spec: NeuronSpec, d: NeuronDesign) -> tuple[float, float]:
    """(W, L) desde el objetivo de frecuencia, respetando lo que este fijo."""
    W, Lg = spec.W_M5, spec.L_M5

    # que frecuencia se persigue, y a que corriente
    f_target = iex_at = None
    if (spec.freq_range and spec.iex_range
            and spec.iex_range[1] != spec.iex_range[0]):
        # el objetivo real es la GANANCIA: rango de salida / rango de entrada
        k_req = ((spec.freq_range[1] - spec.freq_range[0]) /
                 (spec.iex_range[1] - spec.iex_range[0]))
        f_target, iex_at = spec.freq_range[1], spec.iex_range[1]
        d.add(Severity.INFO, "ganancia",
              f"k requerida = {k_req:.3f} kHz/nA "
              f"(f {spec.freq_range} kHz sobre Iex {spec.iex_range} nA)")
    elif spec.freq_range and spec.iex_range:
        # Iex fija: no hay pendiente que perseguir (seria 0/0), es un punto de
        # operacion. Se dimensiona para esa frecuencia a esa corriente.
        f_target, iex_at = spec.freq_range[1], spec.iex_range[1]
        d.add(Severity.INFO, "frecuencia",
              f"objetivo puntual: {f_target} kHz a {iex_at} nA")
    elif spec.freq_range:
        f_target, iex_at = spec.freq_range[1], L.IEX_REF
        d.add(Severity.INFO, "frecuencia",
              f"sin iex_range; se apunta a {f_target} kHz a {L.IEX_REF} nA")

    if f_target is None:
        # sin objetivo de frecuencia: completar lo que falte con el nominal
        return (W if W is not None else NOMINAL["W_M5"],
                Lg if Lg is not None else NOMINAL["L_M5"])

    # F_MAX es un limite medido, no de las leyes: sobre el, el reset no llega a
    # completarse y la celda deja de disparar como predice la ley. Las leyes
    # despejan igual y devuelven una geometria de aspecto razonable, asi que
    # sin este aviso el motor entrega en silencio un diseño que no funciona.
    if f_target > L.F_MAX:
        d.add(Severity.WARNING, "frecuencia",
              f"{f_target:.0f} kHz esta sobre el maximo medido "
              f"({L.F_MAX:.0f} kHz): la geometria sale de las leyes, pero el "
              f"reset no completa y la celda no llegara a esa frecuencia",
              chain=f"F_MAX={L.F_MAX:.0f} kHz (el reset tarda ~215 ns)")

    if W is not None and Lg is not None:
        # sobre-determinado: ambas fijas Y hay objetivo de frecuencia
        f_real = L.freq(W, Lg, iex_at)
        if abs(f_real - f_target) / f_target > spec.freq_tolerance:
            _resolve_freq_conflict(spec, d, W, Lg, f_target, iex_at, f_real)
            return _adjusted_geometry(spec, d, f_target, iex_at)
        return W, Lg

    if W is not None:
        Lg = L.solve_L_for_freq(W, f_target, iex_at)
        Lg, hit = _clamp(Lg, L.L_MIN, L.L_MAX)
        if hit:
            # L sola no alcanza. Los objetivos mandan, asi que se libera W
            # aunque el usuario la hubiera fijado.
            w_new = L.solve_W_for_freq(Lg, f_target, iex_at)
            w_new, hit_w = _clamp(w_new, L.W_MIN, L.W_MAX)
            if not hit_w:
                d.add(Severity.WARNING, "W_M5",
                      f"cambiada de {W} a {w_new:.3f} um para alcanzar "
                      f"{f_target:.0f} kHz",
                      f"con W={W} fija habria hecho falta L="
                      f"{L.solve_L_for_freq(W, f_target, iex_at):.1f} um, "
                      f"fuera del rango {L.L_MIN}-{L.L_MAX}")
                return w_new, Lg
            f_got = L.freq(w_new, Lg, iex_at)
            d.add(Severity.ERROR, "frecuencia",
                  f"{f_target:.0f} kHz inalcanzable ni ajustando W y L",
                  f"lo mas cercano con ambas en rango: {f_got:.0f} kHz "
                  f"({100*(f_got-f_target)/f_target:+.0f}%)")
            return w_new, Lg
        return W, Lg

    if Lg is not None:
        W = L.solve_W_for_freq(Lg, f_target, iex_at)
        W, hit = _clamp(W, L.W_MIN, L.W_MAX)
        if hit:
            # analogo: se libera L para no incumplir el objetivo
            l_new = L.solve_L_for_freq(W, f_target, iex_at)
            l_new, hit_l = _clamp(l_new, L.L_MIN, L.L_MAX)
            if not hit_l:
                d.add(Severity.WARNING, "L_M5",
                      f"cambiada de {Lg} a {l_new:.1f} um para alcanzar "
                      f"{f_target:.0f} kHz",
                      f"con L={Lg} fija habria hecho falta W fuera del rango "
                      f"{L.W_MIN}-{L.W_MAX}")
                return W, l_new
            f_got = L.freq(W, l_new, iex_at)
            d.add(Severity.ERROR, "frecuencia",
                  f"{f_target:.0f} kHz inalcanzable ni ajustando W y L",
                  f"lo mas cercano con ambas en rango: {f_got:.0f} kHz "
                  f"({100*(f_got-f_target)/f_target:+.0f}%)")
            return W, l_new
        return W, Lg

    # ambas libres: hay un grado de libertad. Como gastarlo depende de si hay
    # objetivo de threshold: Vth alto exige W*L pequeño (para que Cm_min sea
    # bajo y Vth pueda subir), lo que compite con el criterio de margen.
    return _pick_by_margin(d, f_target, iex_at, spec.vth)


def _pick_by_margin(d: NeuronDesign, f_target: float, iex_at: float,
                    vth_target: float | None = None) -> tuple[float, float]:
    """Elige (W,L) sobre la curva de iso-frecuencia.

    Sin objetivo de Vth: se maximiza el margen a los limites duros, con L en
    la zona precisa (>=25 um, donde el error es ~1% y no 5-7%).

    Con objetivo de Vth: se prefiere el punto que MAS Vth permite, es decir el
    de menor Cm_min, es decir el de menor W*L. Solo si ninguno alcanza el Vth
    pedido se cae de nuevo al criterio de margen.
    """
    best, best_score = None, -1.0
    steps = 60
    for i in range(steps + 1):
        Lg = L.L_PRECISE_MIN + (L.L_MAX - L.L_PRECISE_MIN) * i / steps
        W = L.solve_W_for_freq(Lg, f_target, iex_at)
        if not (L.W_MIN <= W <= L.W_MAX):
            continue
        if vth_target is not None:
            # puntuar por cuanto Vth admite; el mejor es el de mayor techo
            score = L.vth_max_at(W, Lg)
            if score >= vth_target:
                # alcanza: entre los que alcanzan, preferir el de mas margen
                score = 1000.0 + min(math.log(W / L.W_MIN),
                                     math.log(L.W_MAX / W))
        else:
            # margen relativo al borde mas cercano, en escala log
            mw = min(math.log(W / L.W_MIN), math.log(L.W_MAX / W))
            ml = min(math.log(Lg / L.L_PRECISE_MIN), math.log(L.L_MAX / Lg))
            score = min(mw, ml)
        if score > best_score:
            best, best_score = (W, Lg), score
    if best is None:
        # la frecuencia no es alcanzable con L en zona precisa; reintentar
        # permitiendo L corta
        for i in range(steps + 1):
            Lg = L.L_MIN + (L.L_MAX - L.L_MIN) * i / steps
            W = L.solve_W_for_freq(Lg, f_target, iex_at)
            if L.W_MIN <= W <= L.W_MAX:
                d.add(Severity.WARNING, "L_M5",
                      f"L={Lg:.1f} um esta bajo {L.L_PRECISE_MIN} um: el error "
                      "de la ley de frecuencia sube de ~1% a 5-7%")
                return W, Lg
        # nada alcanzable. El techo real es el menor entre lo que da la
        # geometria minima y F_MAX (el reset no completa mas alla).
        fmin = L.freq(L.W_MAX, L.L_MAX, iex_at)
        fmax = min(L.freq(L.W_MIN, L.L_MIN, iex_at), L.F_MAX)
        extra = ""
        if L.freq(L.W_MIN, L.L_MIN, iex_at) > L.F_MAX:
            extra = (f" (la geometria minima daria mas, pero sobre "
                     f"{L.F_MAX:.0f} kHz el reset no completa)")
        d.add(Severity.ERROR, "frecuencia",
              f"{f_target:.0f} kHz a {iex_at:.0f} nA no es alcanzable",
              f"rango posible a esa corriente: {fmin:.0f} - {fmax:.0f} kHz"
              + extra)
        return NOMINAL["W_M5"], NOMINAL["L_M5"]
    d.add(Severity.INFO, "geometria",
          f"W={best[0]:.3f} L={best[1]:.1f} elegidas por margen de validez "
          "(habia una familia de soluciones sobre la curva de iso-frecuencia)")
    return best


def _resolve_freq_conflict(spec: NeuronSpec, d: NeuronDesign, W: float,
                           Lg: float, f_target: float, iex_at: float,
                           f_real: float) -> None:
    """Informa el conflicto y que se puede liberar."""
    opts = []
    l_need = L.solve_L_for_freq(W, f_target, iex_at)
    if L.L_MIN <= l_need <= L.L_MAX:
        opts.append(f"liberar L_M5 -> L={l_need:.1f} um")
    else:
        opts.append(f"liberar L_M5 -> exigiria L={l_need:.1f} um (fuera de "
                    f"{L.L_MIN}-{L.L_MAX})")
    w_need = L.solve_W_for_freq(Lg, f_target, iex_at)
    if L.W_MIN <= w_need <= L.W_MAX:
        opts.append(f"liberar W_M5 -> W={w_need:.3f} um")
    else:
        opts.append(f"liberar W_M5 -> exigiria W={w_need:.3f} um (fuera de "
                    f"{L.W_MIN}-{L.W_MAX})")
    d.add(Severity.WARNING, "frecuencia",
          f"W={W} y L={Lg} fijas dan {f_real:.0f} kHz, no {f_target:.0f}. "
          "Los objetivos tienen prioridad, asi que se ajustan las dimensiones",
          " | ".join(opts))


def _adjusted_geometry(spec: NeuronSpec, d: NeuronDesign, f_target: float,
                       iex_at: float) -> tuple[float, float]:
    """Ajusta la geometria priorizando el objetivo, tocando L antes que W."""
    W = spec.W_M5
    l_need = L.solve_L_for_freq(W, f_target, iex_at)
    if L.L_MIN <= l_need <= L.L_MAX:
        d.add(Severity.WARNING, "L_M5",
              f"cambiada de {spec.L_M5} a {l_need:.1f} um para alcanzar "
              f"{f_target:.0f} kHz")
        return W, l_need
    # L no alcanza: tocar W tambien
    Lg, _ = _clamp(l_need, L.L_MIN, L.L_MAX)
    w_need = L.solve_W_for_freq(Lg, f_target, iex_at)
    w_need, hit = _clamp(w_need, L.W_MIN, L.W_MAX)
    d.add(Severity.WARNING, "W_M5",
          f"cambiada de {spec.W_M5} a {w_need:.3f} um; L_M5 tambien a "
          f"{Lg:.1f} um")
    if hit:
        f_got = L.freq(w_need, Lg, iex_at)
        d.add(Severity.ERROR, "frecuencia",
              f"{f_target:.0f} kHz inalcanzable incluso ajustando ambas",
              f"lo maximo con W,L en rango: {f_got:.0f} kHz")
    return w_need, Lg


# --------------------------------------------------------------------------
def _solve_cm(spec: NeuronSpec, d: NeuronDesign, W: float, Lg: float) -> float:
    """Cm desde el threshold, o el minimo con margen si no se pidio."""
    floor = max(L.Cm_min(W, Lg), L.CM_FLOOR)

    if spec.vth is None:
        Cm = spec.Cm if spec.Cm is not None else 1.2 * floor
        if spec.Cm is not None and spec.Cm < floor:
            d.add(Severity.WARNING, "Cm",
                  f"subida de {spec.Cm} a {floor:.0f} fF: bajo Cm_min la "
                  "membrana sale del riel",
                  f"Cm_min(W={W:.2f}, L={Lg:.1f}) = {L.Cm_min(W, Lg):.0f} fF")
            Cm = floor
        elif spec.Cm is None:
            d.add(Severity.INFO, "Cm",
                  f"sin objetivo de Vth; se usa 1.2 x Cm_min = {Cm:.0f} fF "
                  "(margen sobre el limite de operacion)")
        return Cm

    # hay objetivo de Vth
    try:
        Cm = L.solve_Cm_for_vth(W, Lg, spec.vth)
    except ValueError as e:
        d.add(Severity.ERROR, "Vth", str(e))
        return max(floor, NOMINAL["Cm"])

    if Cm < floor:
        # el Vth pedido exige menos Cm del permitido -> acoplamiento f/Vth
        vmax = L.vth(W, Lg, floor)
        d.add(Severity.ERROR, "Vth",
              f"Vth={spec.vth:.3f} V exigiria Cm={Cm:.0f} fF, bajo el minimo "
              f"de {floor:.0f} fF",
              f"W*L={W*Lg:.0f} um2 -> Cm_min={L.Cm_min(W, Lg):.0f} fF -> "
              f"Vth <= {vmax:.3f} V. La frecuencia y el threshold estan "
              "acoplados: f baja exige W*L grande, que exige Cm grande, que "
              "baja Vth")
        return floor
    if spec.Cm is not None and abs(spec.Cm - Cm) / Cm > 0.05:
        d.add(Severity.WARNING, "Cm",
              f"cambiada de {spec.Cm} a {Cm:.0f} fF para lograr "
              f"Vth={spec.vth:.3f} V")
    return Cm


def _solve_buffer(spec: NeuronSpec, d: NeuronDesign) -> float:
    """W de M7/M8 desde el fan-out. Independiente del resto."""
    if spec.c_load is None:
        w = spec.W_M7M8 if spec.W_M7M8 is not None else L.W_MIN
        return w
    need = L.solve_w_m7m8_for_load(spec.c_load)
    if spec.W_M7M8 is not None:
        if L.c_load_max(spec.W_M7M8) < spec.c_load:
            d.add(Severity.WARNING, "W_M7M8",
                  f"subida de {spec.W_M7M8} a {need:.3f} um: con la fijada "
                  f"solo se manejan {L.c_load_max(spec.W_M7M8):.0f} fF de los "
                  f"{spec.c_load:.0f} pedidos")
            return need
        return spec.W_M7M8
    return need


# --------------------------------------------------------------------------
def _validate(d: NeuronDesign, W: float, Lg: float, Cm: float,
              spec: NeuronSpec) -> None:
    """Limites duros sobre TODO, incluidas las dimensiones fijadas."""
    if not (L.W_MIN <= W <= L.W_MAX):
        d.add(Severity.WARNING, "W_M5",
              f"{W:.3f} um esta fuera del rango medido "
              f"({L.W_MIN}-{L.W_MAX}); las leyes no estan validadas ahi")
    if not (L.L_MIN <= Lg <= L.L_MAX):
        d.add(Severity.WARNING, "L_M5",
              f"{Lg:.1f} um esta fuera del rango medido "
              f"({L.L_MIN}-{L.L_MAX})")
    elif Lg < L.L_PRECISE_MIN:
        d.add(Severity.WARNING, "L_M5",
              f"{Lg:.1f} um: bajo {L.L_PRECISE_MIN} um el error de la ley de "
              "frecuencia sube de ~1% a 5-7%")
    if Cm < L.Cm_min(W, Lg):
        d.add(Severity.WARNING, "Cm",
              f"{Cm:.0f} fF esta bajo Cm_min={L.Cm_min(W, Lg):.0f} fF; la "
              "membrana puede salir del riel (la ley es conservadora 10-25%, "
              "asi que puede funcionar igualmente)")
    # La corriente que la etapa previa entrega TIENE que caber en la ventana
    # de la geometria elegida. Sin esto el motor aceptaba iex_range=(111,2231)
    # y devolvia una geometria de ventana 5-911 nA sin decir nada: lo encontro
    # la comprobacion de cadena, no este motor.
    if spec.iex_range is not None:
        lo_v, hi_v = L.iex_window(W, Lg)
        lo_p, hi_p = spec.iex_range
        if lo_p < lo_v or hi_p > hi_v:
            sev = (Severity.ERROR if (hi_p > hi_v * 1.5 or lo_p < lo_v * 0.5)
                   else Severity.WARNING)
            d.add(sev, "iex_range",
                  f"la etapa previa entrega {lo_p:.1f}-{hi_p:.1f} nA y esta "
                  f"geometria solo admite {lo_v:.1f}-{hi_v:.1f} nA",
                  f"fuera de ahi la neurona no dispara (por abajo) o el reset "
                  f"no completa (por arriba). Da tambien `freq_range` para que "
                  f"el motor elija geometria, o acota lo que entrega el vecino")

    v = L.vth(W, Lg, Cm)
    if v >= L.VDD:
        d.add(Severity.ERROR, "Vth",
              f"el diseño da Vth={v:.2f} V, sobre VDD={L.VDD} V")
    if spec.c_in_max is not None:
        ci = L.c_in(W)
        if ci > spec.c_in_max:
            # solo se comprueba: C_in depende exclusivamente de W_M5, que es
            # el ultimo eslabon de la cadena de ajuste. Resolverlo aqui seria
            # gastar el mando mas caro por un margen de 1.1-4.0 fF.
            d.add(Severity.WARNING, "C_in",
                  f"el diseño presenta C_in={ci:.2f} fF a la etapa previa, "
                  f"sobre el maximo pedido de {spec.c_in_max:.2f} fF; haria "
                  f"falta W_M5 <= {(spec.c_in_max - 0.945) / 0.865:.3f} um")


def _predict(d: NeuronDesign, spec: NeuronSpec) -> None:
    """Comportamiento esperado y requisitos sobre el entorno."""
    W, Lg = d.params["W_M5"], d.params["L_M5"]
    Cm, w78 = d.params["Cm"], d.params["W_M7M8"]
    lo, hi = L.iex_window(W, Lg)
    ir = spec.iex_range or (lo, min(hi, 200.0))

    d.predicted = {
        "k [kHz/nA]": round(L.gain(W, Lg), 3),
        "f a 100 nA [kHz]": round(L.freq_at_iex_ref(W, Lg), 1),
        "f en el rango [kHz]": (round(L.freq(W, Lg, ir[0]), 1),
                                round(L.freq(W, Lg, ir[1]), 1)),
        "Vth [V]": round(L.vth(W, Lg, Cm), 3),
        "swing [V]": round(L.swing(W, Lg, Cm), 3),
        "Cm_min [fF]": round(L.Cm_min(W, Lg), 1),
        "ventana Iex [nA]": (round(lo, 1), round(hi, 1)),
        "C_in [fF]": round(L.c_in(W), 2),
        "C_load max [fF]": round(L.c_load_max(w78), 1),
    }

    iex_ref = ir[1] if spec.iex_range else L.IEX_REF
    ro_need = L.min_source_impedance(iex_ref, 0.01)
    d.requirements["impedancia de fuente"] = (
        f">= {ro_need/1e9:.2f} GOhm a {iex_ref:.0f} nA para 1% de error "
        "(un espejo simple da 1-10 MOhm: hace falta cascodo o L larga)"
    )
    if spec.source_ro is not None:
        err = L.freq_error_from_source(iex_ref, spec.source_ro)
        sev = Severity.WARNING if err > 0.02 else Severity.INFO
        d.add(sev, "fuente",
              f"con ro={spec.source_ro/1e6:.0f} MOhm el error de frecuencia "
              f"sera ~{100*err:.1f}%")
