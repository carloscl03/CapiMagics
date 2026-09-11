"""Motor de diseno de la sinapsis STDP.

Orden de resolucion, y el porque de cada capa:

  1. `tau` -> `itd`.  Directo y fisico (`tau = eta*Cdep/Itd`), sin ajuste.
  2. `W1` -> el suelo de potenciacion.  Se anula solo en 0.357 um, asi que se
     coge ese salvo que el usuario mande otra cosa. La depresion NO tiene este
     remedio (sus dos terminos son negativos), asi que alli se reporta y ya.
  3. `W4` <- EQUILIBRIO.  No se elige: lo fija la condicion `A+ tau+ = A- tau-`
     dada la amplitud que produce la potenciacion. Es la capa que hace que la
     regla no derive.
  4. `L1` se recorre sobre `L1_DISC` y se queda la que permite equilibrar
     dentro de la caja. Con el punto de trabajo nominal, `L1 = 2.00` no puede:
     su maximo es 141 mV contra los 209 minimos de la depresion.

Lo que el motor NO hace: elegir el punto de trabajo de las trazas. `Vdep0` y
`Vtr0` los fijan los bias (`vb_idep`, `vb_pot`) y el techo `n5`, y eso vive en
la ley de dispositivo del encoder. Aqui entran como dados.
"""
from __future__ import annotations

from math import log10

from . import coeffs as C
from . import laws as L
from .spec import Severity, StdpDesign, StdpSpec

# punto de trabajo de las trazas con el bias nominal medido, ver el KB
VDEP0_NOM = 0.767
VTR0_NOM = 1.213
NCDEP_NOM = 2
NCW_NOM = 10


def _w4_que_equilibra(a_pot, ncw, lo=None, hi=None):
    """La `W4` cuya amplitud de depresion iguala a `a_pot`. Biseccion.

    Monotona creciente en `W4` (de 209 a 432 mV en la caja), asi que la
    biseccion es segura.
    """
    lo = C.CAJA_W4[0] if lo is None else lo
    hi = C.CAJA_W4[1] if hi is None else hi
    f = lambda w: abs(L.dvw_dep(VDEP0_NOM, w, ncw)) - a_pot
    if f(lo) > 0 or f(hi) < 0:
        return None                      # no se puede equilibrar en la caja
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if f(m) < 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


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

    # ---- capa 1: tau -> itd ------------------------------------------------
    tau_s = spec.tau_us * 1e-6
    itd = fx.get("itd") or L.itd_para_tau(tau_s, ncdep, "dep")
    itp = fx.get("itp") or L.itd_para_tau(tau_s * spec.asimetria, ncdep, "pot")

    # ---- capa 2: W1 por el suelo -------------------------------------------
    W1 = fx.get("W1", L.w1_suelo_nulo())
    if not (C.CAJA_W1[0] <= W1 <= C.CAJA_W1[1]):
        d.add(Severity.WARNING, "W1",
              f"{W1:.3f} um queda fuera de la caja {C.CAJA_W1}; se recorta")
        W1 = min(max(W1, C.CAJA_W1[0]), C.CAJA_W1[1])

    # ---- capas 3 y 4: L1 y W4 por el EQUILIBRIO ----------------------------
    candidatas = [fx["L1"]] if "L1" in fx else list(C.L1_DISC)
    elegido = None
    for L1 in candidatas:
        if L1 not in C.L1_DISC:
            d.add(Severity.ERROR, "L1",
                  f"{L1} no es interpolable; usa una de {C.L1_DISC}",
                  "LOO dejando fuera una L entera: 43-47 %, peor 140 %")
            continue
        a_pot = L.dvw_pot(VTR0_NOM, W1, L1, ncw)
        W4 = _w4_que_equilibra(a_pot / spec.asimetria, ncw)
        if W4 is not None:
            elegido = (L1, W4, a_pot)
            break
        d.add(Severity.INFO, "L1",
              f"L1 = {L1} no puede equilibrar: da {a_pot*1e3:.1f} mV y la "
              f"depresion no baja de {abs(L.dvw_dep(VDEP0_NOM, C.CAJA_W4[0], ncw))*1e3:.1f}")

    if elegido is None:
        d.add(Severity.ERROR, "equilibrio",
              "ninguna L1 permite A+ = A- con este W1 y esta caja",
              "sube W1 (mas amplitud de potenciacion) o acepta asimetria")
        d.params = {"W1": round(W1, 3), "nCdep": ncdep, "nCW": ncw}
        return d

    L1, W4, a_pot = elegido
    a_dep = abs(L.dvw_dep(VDEP0_NOM, W4, ncw))

    d.params = {"W4": round(W4, 3), "L4": C.L4_FIJO, "W1": round(W1, 3),
                "L1": L1, "nCdep": ncdep, "nCW": ncw,
                "itd_nA": round(itd * 1e9, 4), "itp_nA": round(itp * 1e9, 4)}

    # ---- lo que sale -------------------------------------------------------
    su_d, su_p = L.suelo_dep(W4, ncw), L.suelo_pot(W1, ncw)
    tau_d = L.tau(itd, ncdep, "dep")
    d.predicted = {
        "A- por evento [mV]": round(-a_dep * 1e3, 2),
        "A+ por evento [mV]": round(a_pot * 1e3, 2),
        "asimetria A+/A-": round(a_pot / a_dep, 3),
        "tau- [us]": round(tau_d * 1e6, 2),
        "tau+ [us]": round(L.tau(itp, ncdep, "pot") * 1e6, 2),
        "deriva (0 = equilibrio)": f"{L.deriva(a_pot, tau_d*spec.asimetria, a_dep, tau_d):+.3e}",
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

    # ---- comprobaciones ----------------------------------------------------
    if spec.f_min_kHz and spec.f_max_kHz:
        fc = L.f_cubierta(itd, ncdep) / 1e3
        d.predicted["f cubierta al 10 % [kHz]"] = round(fc, 1)
        if fc > spec.f_min_kHz:
            d.add(Severity.WARNING, "acoplo",
                  f"la ventana solo cubre por encima de {fc:.1f} kHz y la "
                  f"neurona baja a {spec.f_min_kHz:.1f}",
                  f"para cubrirla entera: tau = "
                  f"{1e6/(spec.f_min_kHz*1e3*2.303):.1f} us, o sea itd = "
                  f"{L.itd_para_tau(1/(spec.f_min_kHz*1e3*2.303), ncdep)*1e9:.3f} nA")
        else:
            d.add(Severity.INFO, "acoplo",
                  f"cubre {fc:.1f} a {spec.f_max_kHz:.0f} kHz; la neurona hace "
                  f"{spec.f_min_kHz:.1f} a {spec.f_max_kHz:.0f}")

    if not L.en_caja_dep(W4, VDEP0_NOM):
        d.add(Severity.WARNING, "caja", "la depresion queda fuera de lo medido")
    if not L.en_caja_pot(W1, VTR0_NOM):
        d.add(Severity.WARNING, "caja", "la potenciacion queda fuera de lo medido")

    if spec.dvw_evento_mV:
        obj = spec.dvw_evento_mV * 1e-3
        if abs(a_dep - obj) / obj > 0.15:
            d.add(Severity.WARNING, "amplitud",
                  f"pediste {spec.dvw_evento_mV:.1f} mV y el equilibrio obliga a "
                  f"{a_dep*1e3:.1f}. La amplitud NO es libre: la fija A+ = A-")

    d.add(Severity.INFO, "L4",
          f"fija en {C.L4_FIJO} um, el minimo del proceso. El optimo esta ahi y "
          f"gana en los tres ejes; entre 0.28 y 0.45 hay una transicion donde la "
          f"dependencia con W cambia de sentido y la ley no vale")
    return d
