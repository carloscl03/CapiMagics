"""Motor de diseno de la sinapsis STDP.

Politica de prioridades, la misma que `lif_design`, `encoder_design` e
`integrator_design`:

  1. OBJETIVOS de diseno  -- mandan
  2. DIMENSIONES fijadas  -- se ajustan si estorban, con WARNING
  3. Si la contradiccion no se puede resolver -> ERROR con la cadena causal

Y la escalera cuando un objetivo choca con una dimension dada, como en el LIF:

  1. mover la dimension LIBRE
  2. si no basta, CAMBIAR la que fijo el usuario, con un WARNING que lleve el
     CONTRAFACTUAL -- que habria hecho falta respetandola
  3. si aun asi no llega, ERROR con LO MAS CERCANO alcanzable
  4. y al final, comprobar la caja sobre TODO, incluidas las dimensiones del
     usuario: las leyes no estan validadas fuera de donde se midio

Orden de resolucion propio de esta celda:

  1. `tau` -> `itd`.  Directo y fisico (`tau = eta*Cdep/Itd`), sin ajuste.
  2. ventana de `W1` que PERMITE equilibrar, para cada `L1` discreta.
  3. `W1` dentro de esa ventana: el nulo del suelo (0.357) si cabe; si el
     usuario la fijo fuera, se recorta con WARNING.
  4. `W4` <- EQUILIBRIO. No se elige: lo fija `A+ tau+ = A- tau-`.

Lo que el motor NO hace: elegir el punto de trabajo de las trazas. `Vdep0` y
`Vtr0` los fijan los bias y el techo `n5`; aqui entran como dados.
"""
from __future__ import annotations

from . import coeffs as C
from . import laws as L
from .spec import Severity, StdpDesign, StdpSpec

__all__ = ["design", "nominal", "NOMINAL_SPEC"]

# DEFAULT, derivado de la CADENA y no puesto a ojo.
# La capa 1 con la celda v3 y el encoder por defecto dispara a 205-734 kHz, o
# sea intervalos entre spikes de 1.36 a 4.88 us. Para que la ventana cubra el
# extremo lento al 10 % hace falta `tau = 4.88/ln(10) = 2.12 us`.
# `asimetria` = 1.0 porque con `tau+ = tau-` es la condicion de equilibrio:
# en STDP aditivo, si `A+ tau+ != A- tau-` los pesos se van al rail.
NOMINAL_SPEC = {"tau_us": 2.12, "asimetria": 1.0,
                "f_min_kHz": 205.1, "f_max_kHz": 734.5}

_NOM_CACHE = None


def nominal():
    """Las dimensiones del punto nominal, derivadas de `NOMINAL_SPEC`.

    No estan clavadas: si la ley cambia, esto cambia con ella.
    """
    global _NOM_CACHE
    if _NOM_CACHE is None:
        from .spec import StdpSpec
        _NOM_CACHE = dict(design(StdpSpec(**NOMINAL_SPEC)).params)
    return dict(_NOM_CACHE)


# punto de trabajo de las trazas con el bias nominal medido, ver el KB
VDEP0_NOM = 0.767
VTR0_NOM = 1.213
NCDEP_NOM = 2
NCW_NOM = 10


def _a_dep(W4, ncw):
    return abs(L.dvw_dep(VDEP0_NOM, W4, ncw))


def _rango_dep(ncw):
    """Amplitudes de depresion alcanzables en la caja. Monotona en W4."""
    return _a_dep(C.CAJA_W4[0], ncw), _a_dep(C.CAJA_W4[1], ncw)


def _invierte(f, y, lo, hi):
    """Biseccion sobre una funcion monotona creciente. RECORTA a los extremos.

    Antes devolvia None fuera de rango, y eso rompia el caso de borde: la
    biseccion de la ventana converge a un `W1` cuyo `A+` queda un pelo fuera
    por coma flotante, y el siguiente `_invierte` lo rechazaba. La decision de
    VIABILIDAD la toma `_ventana_W1` con comprobaciones explicitas; esto solo
    resuelve, y en el borde devuelve el borde.
    """
    if f(lo) >= y:
        return lo
    if f(hi) <= y:
        return hi
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if f(m) < y:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def _ventana_W1(L1, asim, ncw):
    """Rango de `W1` que permite equilibrar con esa `L1`, o None.

    `A+` crece con `W1`; el equilibrio pide `A+ = asim * A-`, y `A-` solo puede
    moverse entre sus dos extremos de caja. Asi que la ventana de `W1` es la
    preimagen de [asim*A-_min, asim*A-_max].
    """
    dmin, dmax = _rango_dep(ncw)
    g = lambda w: L.dvw_pot(VTR0_NOM, w, L1, ncw)
    glo, ghi = g(C.CAJA_W1[0]), g(C.CAJA_W1[1])
    # `_invierte` devuelve None por ARRIBA y por ABAJO sin distinguir, asi que
    # los dos casos imposibles se comprueban aparte:
    if glo > asim * dmax:
        return None          # hasta la W1 minima se pasa de amplitud
    if ghi < asim * dmin:
        return None          # ni la maxima llega
    lo = (C.CAJA_W1[0] if glo >= asim * dmin
          else _invierte(g, asim * dmin, *C.CAJA_W1))
    hi = (C.CAJA_W1[1] if ghi <= asim * dmax
          else _invierte(g, asim * dmax, *C.CAJA_W1))
    return (lo, hi)


def design(spec: StdpSpec) -> StdpDesign:
    d = StdpDesign()
    if not spec.has_objectives:
        d.add(Severity.ERROR, "objetivos",
              "hace falta `tau_us`: es lo que acopla la ventana con la neurona")
        d.params = {"W4": 0.30, "W1": 0.357, "L1": 0.40,
                    "nCdep": NCDEP_NOM, "nCW": NCW_NOM}
        return d

    fx = spec.fixed_dims
    ncw = int(fx.get("nCW", NCW_NOM))
    ncdep = int(fx.get("nCdep", NCDEP_NOM))
    asim = spec.asimetria

    # ---- capa 1: tau -> corrientes ----------------------------------------
    tau_s = spec.tau_us * 1e-6
    itd = fx.get("itd") or L.itd_para_tau(tau_s, ncdep, "dep")
    itp = fx.get("itp") or L.itd_para_tau(tau_s * asim, ncdep, "pot")

    # ---- capas 2 y 3: L1 y W1, con la escalera ----------------------------
    candidatas = [fx["L1"]] if "L1" in fx else list(C.L1_DISC)
    for L1 in candidatas:
        if L1 not in C.L1_DISC:
            d.add(Severity.ERROR, "L1",
                  f"{L1} um no es interpolable; usa una de {C.L1_DISC}",
                  "LOO dejando fuera una L entera: 43-47 %, peor 140 %. Estos "
                  "transistores cruzan la transicion canal corto/largo")
            # se vuelve YA: encadenar el error de equilibrio detras seria
            # informar de un fallo que no existe
            d.params = {"nCdep": ncdep, "nCW": ncw,
                        "itd_nA": round(itd * 1e9, 4),
                        "itp_nA": round(itp * 1e9, 4)}
            return d

    elegido, diag = None, []
    for L1 in candidatas:
        vent = _ventana_W1(L1, asim, ncw)
        if vent is None:
            amin = L.dvw_pot(VTR0_NOM, C.CAJA_W1[0], L1, ncw)
            amax = L.dvw_pot(VTR0_NOM, C.CAJA_W1[1], L1, ncw)
            dmin, dmax = _rango_dep(ncw)
            por = ("se PASA: hasta W1={:.2f} da {:.1f} mV y el maximo util es "
                   "{:.1f}".format(C.CAJA_W1[0], amin*1e3, asim*dmax*1e3)
                   if amin > asim * dmax else
                   "NO LLEGA: ni con W1={:.2f} ({:.1f} mV) alcanza el minimo "
                   "util de {:.1f}".format(C.CAJA_W1[1], amax*1e3, asim*dmin*1e3))
            diag.append((L1, None, por))
            continue
        W1_pedida = fx.get("W1")
        W1_pref = W1_pedida if W1_pedida is not None else L.w1_suelo_nulo()
        W1 = min(max(W1_pref, vent[0]), vent[1])
        elegido = (L1, W1, vent, W1_pedida, W1_pref)
        break

    if elegido is None:
        # peldano 3: nada funciona -> ERROR con lo mas cercano
        for L1, _, por_que in diag:
            d.add(Severity.INFO, "L1", f"L1 = {L1}: {por_que}")
        mejor = max(C.L1_DISC,
                    key=lambda l: L.dvw_pot(VTR0_NOM, C.CAJA_W1[1], l, ncw))
        amax = L.dvw_pot(VTR0_NOM, C.CAJA_W1[1], mejor, ncw)
        dmin, _ = _rango_dep(ncw)
        d.add(Severity.ERROR, "equilibrio",
              f"no hay geometria que de A+/A- = {asim:.2f}",
              f"lo mas cercano: L1={mejor}, W1={C.CAJA_W1[1]:.2f} dan "
              f"A+/A- = {amax/dmin:.2f}. Sube `asimetria` o baja `nCW` "
              f"(escala las dos amplitudes pero mueve la caja util)")
        d.params = {"nCdep": ncdep, "nCW": ncw,
                    "itd_nA": round(itd * 1e9, 4), "itp_nA": round(itp * 1e9, 4)}
        return d

    L1, W1, vent, W1_pedida, W1_pref = elegido

    # peldano 2: se cambio lo que el usuario fijo -> WARNING con contrafactual
    if W1_pedida is not None and abs(W1 - W1_pedida) > 1e-6:
        a_ped = L.dvw_pot(VTR0_NOM, W1_pedida, L1, ncw)
        dmin, dmax = _rango_dep(ncw)
        d.add(Severity.WARNING, "W1",
              f"cambiada de {W1_pedida:.3f} a {W1:.3f} um para poder equilibrar",
              f"con W1={W1_pedida:.3f} la potenciacion da {a_ped*1e3:.1f} mV y "
              f"la depresion solo llega de {dmin*1e3:.1f} a {dmax*1e3:.1f}; "
              f"los objetivos tienen prioridad sobre las dimensiones")
    elif W1_pedida is None and abs(W1 - W1_pref) > 1e-6:
        d.add(Severity.INFO, "W1",
              f"{W1:.3f} um en vez del nulo del suelo ({W1_pref:.3f}): el "
              f"equilibrio no deja llegar",
              f"ventana util con L1={L1}: {vent[0]:.3f} a {vent[1]:.3f} um. "
              f"El suelo de potenciacion no se anula, quedan "
              f"{L.suelo_pot(W1, ncw)*1e3:+.3f} mV")

    a_pot = L.dvw_pot(VTR0_NOM, W1, L1, ncw)
    W4 = _invierte(lambda w: _a_dep(w, ncw), a_pot / asim, *C.CAJA_W4)
    a_dep = _a_dep(W4, ncw)

    if "W4" in fx and abs(fx["W4"] - W4) > 1e-6:
        d.add(Severity.WARNING, "W4",
              f"cambiada de {fx['W4']:.3f} a {W4:.3f} um: NO es libre",
              f"la fija la condicion de equilibrio A+ tau+ = A- tau-. Con "
              f"W4={fx['W4']:.3f} la deriva seria "
              f"{L.deriva(a_pot, tau_s, _a_dep(fx['W4'], ncw), tau_s):+.3e} y "
              f"los pesos se irian al rail")

    d.params = {"W4": round(W4, 3), "L4": C.L4_FIJO, "W1": round(W1, 3),
                "L1": L1, "nCdep": ncdep, "nCW": ncw,
                "itd_nA": round(itd * 1e9, 4), "itp_nA": round(itp * 1e9, 4)}

    # ---- lo que sale -------------------------------------------------------
    su_d, su_p = L.suelo_dep(W4, ncw), L.suelo_pot(W1, ncw)
    tau_d = L.tau(itd, ncdep, "dep")
    tau_p = L.tau(itp, ncdep, "pot")
    d.predicted = {
        "A- por evento [mV]": round(-a_dep * 1e3, 2),
        "A+ por evento [mV]": round(a_pot * 1e3, 2),
        "asimetria A+/A-": round(a_pot / a_dep, 3),
        "tau- [us]": round(tau_d * 1e6, 2),
        "tau+ [us]": round(tau_p * 1e6, 2),
        "deriva (0 = equilibrio)": f"{L.deriva(a_pot, tau_p, a_dep, tau_d):+.3e}",
        "suelo NO hebbiano [mV]": f"pre {su_d*1e3:+.3f}, post {su_p*1e3:+.3f}",
        "senal/suelo": round(abs(a_dep / su_d), 1) if su_d else "inf",
        "retencion del peso [ms]": round(L.retencion_peso() * 1e3, 1),
    }

    # ---- requisitos sobre el entorno ---------------------------------------
    cpre = L.c_in(spec.n_sinapsis_pre, "pre")
    cpost = L.c_in(spec.n_sinapsis_post, "post")
    d.requirements = {
        "c_load para NeuronSpec": (
            f"pre {cpre*1e15:.2f} fF ({spec.n_sinapsis_pre} sinapsis), "
            f"post {cpost*1e15:.2f} fF ({spec.n_sinapsis_post}). La neurona "
            f"mueve ~300 fF: no es restriccion, pero pasalo en vez de suponerlo"),
        "Cm de la neurona": (
            f"+{L.c_out(spec.n_sinapsis_post)*1e15:.2f} fF que las sinapsis "
            f"anaden a la membrana. En el LIF `Cm` NO fija la frecuencia pero SI "
            f"el umbral y la excursion"),
        "R_out": (
            f"{L.r_out()/1e6:.0f} MOhm: sobre la excursion de membrana (~1.6 V) "
            f"la corriente entregada varia un 0.36 %"),
        "RETENCION": (
            f"el peso se olvida con tau = {L.retencion_peso()*1e3:.0f} ms. Los "
            f"pesos son VOLATILES: no hay memoria a largo plazo sin refresco"),
        "bias": (
            f"vb_idep y vb_pot fijan Vdep0={VDEP0_NOM} y Vtr0={VTR0_NOM}, que es "
            f"donde estan calculadas estas amplitudes. 1 mV de deriva en vb_idep "
            f"son 3.4 % de tasa de aprendizaje"),
    }

    # ---- acoplo con la neurona --------------------------------------------
    if spec.f_min_kHz and spec.f_max_kHz:
        fc = L.f_cubierta(itd, ncdep) / 1e3
        d.predicted["f cubierta al 10 % [kHz]"] = round(fc, 1)
        if fc > spec.f_min_kHz * 1.01:   # tolerancia: 12.80 vs 12.80
            tau_need = 1.0 / (spec.f_min_kHz * 1e3 * 2.303)
            d.add(Severity.WARNING, "acoplo",
                  f"la ventana solo cubre por encima de {fc:.1f} kHz y la "
                  f"neurona baja a {spec.f_min_kHz:.1f}",
                  f"para cubrirla entera: tau = {tau_need*1e6:.1f} us, o sea "
                  f"itd = {L.itd_para_tau(tau_need, ncdep)*1e9:.3f} nA")
        else:
            d.add(Severity.INFO, "acoplo",
                  f"cubre {fc:.1f} a {spec.f_max_kHz:.0f} kHz; la neurona hace "
                  f"{spec.f_min_kHz:.1f} a {spec.f_max_kHz:.0f}")

    # ---- peldano 4: la caja, sobre TODO -----------------------------------
    if not L.en_caja_dep(W4, VDEP0_NOM):
        d.add(Severity.WARNING, "caja",
              f"W4={W4:.3f} fuera de {C.CAJA_W4}: las leyes no estan "
              f"validadas ahi")
    if not L.en_caja_pot(W1, VTR0_NOM):
        d.add(Severity.WARNING, "caja",
              f"W1={W1:.3f} fuera de {C.CAJA_W1}: idem")
    if not (C.ITD_CAJA[0] <= itd <= C.ITD_CAJA[1]):
        d.add(Severity.WARNING, "caja",
              f"itd = {itd*1e9:.4f} nA fuera de la caja util "
              f"({C.ITD_CAJA[0]*1e12:.0f} pA a {C.ITD_CAJA[1]*1e9:.1f} nA)",
              f"por debajo de {C.ITD_CAJA[0]*1e12:.0f} pA la fuga del "
              f"dispositivo ({C.FUGA_VDEP*1e12:.1f} pA, medida) pasa del 5 % "
              f"de Itd y la ley se va; tau maxima util ~500 us")
    if "W1" not in fx and W1 > C.W1_UTIL_MAX:
        d.add(Severity.INFO, "W1",
              f"{W1:.3f} um pasa del maximo util ({C.W1_UTIL_MAX})",
              "por ahi A+ se sale de lo que la depresion puede igualar, y "
              "ademas el suelo de potenciacion crece +0.77 mV por um")

    if spec.dvw_evento_mV:
        obj = spec.dvw_evento_mV * 1e-3
        if abs(a_dep - obj) / obj > 0.15:
            d.add(Severity.WARNING, "amplitud",
                  f"pediste {spec.dvw_evento_mV:.1f} mV y sale {a_dep*1e3:.1f}",
                  f"la amplitud NO es libre: la fija el equilibrio. Para "
                  f"moverla hay que cambiar `nCW` (la escala) o aceptar deriva")

    d.add(Severity.INFO, "L4",
          f"fija en {C.L4_FIJO} um, el minimo del proceso",
          "el optimo esta ahi y gana en los tres ejes; entre 0.28 y 0.45 la "
          "dependencia con W cambia de sentido y la ley no vale")
    return d
