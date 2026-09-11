"""La cadena completa: encoder -> LIF -> STDP -> LIF -> integrador.

Los cuatro motores ya emiten sus `requirements`. Lo que faltaba era quien los
CONFRONTE: cada bloque supone algo del vecino, y hasta ahora esas suposiciones
se comprobaban a mano o no se comprobaban.

    from cadena import CadenaSpec, resuelve
    c = resuelve(CadenaSpec(iex_min_nA=80.0, gain=0.40, tau_stdp_us=33.9))
    print(c.report())

Topologia, la del `stdp_4x2` que ya esta integrado:

    encoder --Iex--> LIF capa1 --spikes--> STDP --Iout--> LIF capa2 --> integrador
                        |                     |              |
                     source_ro             c_load        C_out suma a Cm

Los seis acoplos que se comprueban, y por que cada uno:

  1. Iex del encoder DENTRO de la ventana del LIF. Fuera, la neurona no
     dispara o se sale por arriba.
  2. `source_ro` del encoder contra lo que el LIF tolera. El LIF tiene
     `freq_error_from_source`: una fuente blanda mete error de frecuencia.
  3. Carga de los spikes: el STDP cuelga capacidad de las salidas del LIF.
     `c_load_max(W_M7M8)` es el limite.
  4. Ventana del STDP contra los INTERVALOS que la capa 1 produce. Si `tau` no
     solapa, no hay pares que aprender.
  5. `Iout` del STDP dentro de la ventana de la capa 2. Es el acoplo que nadie
     habia comprobado: la sinapsis entrega corriente a una neurona.
  6. `C_out` del STDP se SUMA a `Cm` de la capa 2. En el LIF `Cm` no fija la
     frecuencia pero SI el umbral y la excursion.

Politica: la misma de los cuatro motores. Un acoplo que no cuadra es WARNING si
se puede compensar y ERROR si no, siempre con la cadena causal.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from encoder_design import EncoderSpec
from encoder_design import design as _enc
from encoder_design import laws as EL
from integrator_design import IntegratorSpec
from integrator_design import design as _int
from lif_design import NeuronSpec
from lif_design import design as _lif
from lif_design import laws as LL
from stdp_design import StdpSpec
from stdp_design import design as _stdp
from stdp_design import laws as SL
from stdp_design.spec import Note, Severity


@dataclass
class CadenaSpec:
    """Lo que se le pide a la cadena entera.

    Solo los objetivos de SISTEMA. Cada bloque resuelve lo suyo con la misma
    politica de siempre (objetivos > dimensiones).
    """
    iex_min_nA: float = 80.0      # lo que el encoder entrega en el extremo bajo
    gain: float | None = 0.40     # ganancia del encoder
    tau_stdp_us: float = 33.9     # ventana STDP; 33.9 cubre la neurona v3
    n_pre: int = 4                # sinapsis por linea pre, en el 4x2
    n_post: int = 4               # sinapsis que suman en cada ifwd
    tol_freq: float = 0.01        # error de frecuencia tolerable por r_o


@dataclass
class CadenaDesign:
    bloques: dict = field(default_factory=dict)
    acoplos: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)

    @property
    def ok(self):
        return not any(n.severity is Severity.ERROR for n in self.notes)

    def add(self, sev, subj, msg, chain=""):
        self.notes.append(Note(sev, subj, msg, chain))

    def report(self):
        L = ["=" * 66, "CADENA " + ("OK" if self.ok else "CON ERRORES"), "=" * 66]
        for nom, d in self.bloques.items():
            L += ["", "--- %s ---" % nom]
            L.append("  " + "  ".join("%s=%.4g" % (k, v)
                                      for k, v in list(d.params.items())[:6]))
        L += ["", "ACOPLOS:"]
        for k, v in self.acoplos.items():
            L.append("  %-26s %s" % (k, v))
        if self.notes:
            L += ["", "NOTAS:"]
            L += ["  " + str(n) for n in self.notes]
        return "\n".join(L)


def resuelve(spec: CadenaSpec) -> CadenaDesign:
    c = CadenaDesign()

    # ---- 1. encoder -------------------------------------------------------
    enc = _enc(EncoderSpec(iex_min=spec.iex_min_nA, gain=spec.gain))
    c.bloques["encoder"] = enc
    iex_lo = enc.predicted["iex_min [nA]"]
    iex_hi = enc.predicted["iex_max [nA]"]

    # ---- 2. LIF capa 1 ----------------------------------------------------
    l1 = _lif(NeuronSpec(iex_range=(iex_lo, iex_hi)))
    c.bloques["LIF capa 1"] = l1
    W, Lg = l1.params["W_M5"], l1.params["L_M5"]
    f_lo, f_hi = LL.freq(W, Lg, iex_lo), LL.freq(W, Lg, iex_hi)

    # acoplo 1: Iex dentro de la ventana
    w_lo, w_hi = LL.iex_window(W, Lg)
    c.acoplos["1. Iex en la ventana"] = (
        "%.1f-%.1f nA pedidos, ventana %.1f-%.1f nA" % (iex_lo, iex_hi, w_lo, w_hi))
    if iex_lo < w_lo or iex_hi > w_hi:
        c.add(Severity.ERROR, "Iex",
              "el encoder entrega fuera de lo que la neurona admite",
              "recorta `iex_min_nA` o deja que el LIF elija otra geometria")

    # acoplo 2: source_ro
    ro = EL.source_ro(iex_lo)
    err = LL.freq_error_from_source(iex_lo, ro)
    ro_min = LL.min_source_impedance(iex_lo, spec.tol_freq)
    c.acoplos["2. source_ro del encoder"] = (
        "%.3g ohm -> %.2f %% de error de f (hace falta >= %.3g)"
        % (ro, 100 * err, ro_min))
    if ro < ro_min:
        c.add(Severity.WARNING, "source_ro",
              "la fuente del encoder es blanda: %.2f %% de error de frecuencia"
              % (100 * err),
              "sube `Lo` del espejo de salida, o acepta el error")

    # ---- 3. STDP ----------------------------------------------------------
    st = _stdp(StdpSpec(tau_us=spec.tau_stdp_us, f_min_kHz=f_lo, f_max_kHz=f_hi,
                        n_sinapsis_pre=spec.n_pre, n_sinapsis_post=spec.n_post))
    c.bloques["STDP"] = st
    c.notes += [n for n in st.notes if n.subject == "acoplo"]

    # acoplo 3: carga de los spikes
    cl = SL.c_in(spec.n_post, "post")
    cl_max = LL.c_load_max(l1.params["W_M7M8"])
    c.acoplos["3. carga en los spikes"] = (
        "%.2f fF (%d sinapsis) contra %.0f fF que mueve el LIF"
        % (cl * 1e15, spec.n_post, cl_max))
    if cl * 1e15 > cl_max:
        c.add(Severity.ERROR, "c_load",
              "las sinapsis cargan mas de lo que el inversor del LIF mueve",
              "sube `W_M7M8` o reparte las sinapsis en mas lineas")

    # acoplo 4: la ventana contra los intervalos
    fc = SL.f_cubierta(st.params["itd_nA"] * 1e-9, int(st.params["nCdep"])) / 1e3
    c.acoplos["4. ventana vs intervalos"] = (
        "cubre f >= %.1f kHz; la capa 1 hace %.1f-%.1f kHz" % (fc, f_lo, f_hi))

    # ---- 4. LIF capa 2, alimentada por el STDP ----------------------------
    # `ifwd` recoge n_post sinapsis EN PARALELO: lo que la membrana ve es la
    # SUMA, no una. Comparar una sola contra la ventana subestimaba el
    # desajuste por un factor n_post.
    iout_1 = SL.C.IOUT_MAX * 1e9            # nA por sinapsis
    iout_max = iout_1 * spec.n_post         # lo que llega a la membrana
    cm_extra = SL.c_out(spec.n_post) * 1e15  # fF
    # `iex_range` por si sola no elegia geometria en el motor del LIF, asi que
    # aqui se le busca una que SI acepte lo que la sinapsis entrega, y se le
    # pasa fijada. Si ninguna sirve, el problema es de la sinapsis.
    g2 = LL.geometria_para_iex(iout_max * 0.05, iout_max)
    if g2 is None:
        c.add(Severity.ERROR, "Iout",
              "ninguna geometria del LIF admite los %.0f nA que suman las "
              "%d sinapsis" % (iout_max, spec.n_post),
              "el maximo de todo el espacio del LIF es %.0f nA; el arreglo "
              "tiene que ir en el espejo de salida de la sinapsis"
              % max(LL.iex_window(*LL.geometria_para_iex(5.0, 100.0) or (1.25, 50.0))))
        g2 = (1.25, 50.0)
    l2 = _lif(NeuronSpec(iex_range=(iout_max * 0.05, iout_max),
                         W_M5=g2[0], L_M5=g2[1]))
    c.bloques["LIF capa 2"] = l2
    W2, L2g = l2.params["W_M5"], l2.params["L_M5"]
    w2_lo, w2_hi = LL.iex_window(W2, L2g)

    # acoplo 5: Iout dentro de la ventana de la capa 2
    c.acoplos["5. Iout en la capa 2"] = (
        "%d sinapsis x %.0f = %.0f nA; ventana de la capa 2 %.1f-%.1f nA"
        % (spec.n_post, iout_1, iout_max, w2_lo, w2_hi))
    if iout_max > w2_hi:
        sev = Severity.ERROR if iout_max > 3 * w2_hi else Severity.WARNING
        c.add(sev, "Iout",
              "las %d sinapsis suman %.0f nA y la capa 2 admite %.0f: factor "
              "%.1f" % (spec.n_post, iout_max, w2_hi, iout_max / w2_hi),
              "la membrana satura con una fraccion del rango de peso, asi que "
              "el resto no hace nada. El remedio es el espejo de salida de la "
              "sinapsis: %.0f nA por sinapsis en vez de %.0f"
              % (w2_hi / spec.n_post, iout_1))

    # acoplo 6: C_out suma a Cm
    cm = l2.params["Cm"]
    c.acoplos["6. C_out sobre Cm"] = (
        "+%.2f fF sobre %.0f fF (%.2f %%)" % (cm_extra, cm, 100 * cm_extra / cm))
    if cm_extra > 0.05 * cm:
        c.add(Severity.WARNING, "Cm",
              "las sinapsis anaden %.1f %% a la membrana: mueve Vth y la "
              "excursion" % (100 * cm_extra / cm))

    # ---- 5. integrador, leyendo la capa 2 ---------------------------------
    f2_lo, f2_hi = LL.freq(W2, L2g, w2_lo), LL.freq(W2, L2g, min(iout_max, w2_hi))
    ig = _int(IntegratorSpec(f_min=f2_lo, f_max=f2_hi))
    c.bloques["integrador"] = ig
    c.acoplos["7. banda que lee"] = "%.1f-%.1f kHz de la capa 2" % (f2_lo, f2_hi)
    c.notes += [n for n in ig.notes if n.severity is not Severity.INFO]

    return c
