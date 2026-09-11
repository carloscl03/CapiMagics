"""Leyes empiricas de la neurona LIF (GF180MCU, entrada de corriente).

Cada ley trae su despeje inverso, porque el diseñador puede fijar cualquier
variable y pedir que se resuelvan las demas. Todas son potencias o lineales en
1/Cm, asi que los despejes son cerrados -- no hace falta iterar.

Procedencia de los coeficientes: sch/lif/results/lif_knowledge_base.md
Medidos con .tran 1n sobre tb_charac_isrc.spice (entrada de corriente, sin M6).
"""
from __future__ import annotations

# Solo stdlib, y ni siquiera math aqui: son potencias con ** y divisiones.
# El paquete no arrastra numpy a proposito -- son ~15 pow() por diseño, y
# importar numpy costaria ~100 ms para un calculo de 50 us.

# --- constantes del proceso / celda ---------------------------------------
VDD = 3.3           # V
IEX_REF = 100.0     # nA, corriente a la que se ajusto la ley de frecuencia

# --- limites de validez ----------------------------------------------------
# Medidos, no supuestos. Ver "Limites de validez" en la knowledge base.
W_MIN, W_MAX = 0.22, 3.5    # um. Sobre 3.5 la membrana sale del riel.
L_MIN, L_MAX = 20.0, 50.0   # um. L=60 no converge.
L_PRECISE_MIN = 25.0        # bajo esto el error de f sube de ~1% a 5-7%
CM_FLOOR = 50.0             # fF. Bajo esto la ley de Vth diverge.
F_MAX = 4500.0              # kHz. El reset no completa por debajo de ~215 ns.
IEX_VERIFIED_MIN = 5.0      # nA. Verificado sin degradacion; no hay piso real.


# --- frecuencia ------------------------------------------------------------
def freq_at_iex_ref(W: float, L: float) -> float:
    """f [kHz] a Iex = 100 nA.  RMS 2.03% sobre 69 puntos."""
    return 24837.0 * W ** -1.076 * L ** -0.940


def gain(W: float, L: float) -> float:
    """k [kHz/nA], pendiente de f = k*Iex + f0.  RMS 2.18%, |max| 4.9%.

    Cm NO interviene: anadirlo al ajuste lo empeora.

    Ajustada sobre las 9 pendientes medidas en Iex 25-400 nA.

    SESGO CONOCIDO: k tiene curvatura -- la pendiente cae al subir la corriente
    (13.33 -> 10.47 kHz/nA dentro de una misma serie). En el extremo bajo del
    rango la ganancia real es ~11.6% MAYOR que esta ley: medido a 5-10 nA para
    W=0.5/L=41 da k=16.41 frente a 14.51 de la formula.
    Para f() esto importa poco porque el anclaje proporcional lo compensa
    (error ~3%); para consumir gain() directamente a corriente muy baja,
    contar con ese margen.
    """
    return 280.22 * W ** -1.0447 * L ** -0.9923


def freq(W: float, L: float, iex: float) -> float:
    """f [kHz] a una corriente dada.  Proporcional pura, sin intercepto.

    El f0 de 14-144 kHz que salia de ajustar rectas sobre Iex 25-400 nA era un
    ARTEFACTO: un intercepto ajustado lejos del origen absorbe la curvatura de
    la zona alta. Midiendo a 5 y 10 nA (W=0.5, L=41, Cm=150f) sale f0 = +0.57
    kHz, o sea cero, y k = 16.41 kHz/nA.

    Extrapolar la recta con intercepto hacia abajo falla feo:
        a  5 nA predice 129.2 kHz, medido 82.6   (+56%)
        a 10 nA predice 204.7 kHz, medido 164.6  (+24%)
    mientras que este anclaje da -3.4% y -3.1%.

    Queda un sesgo conocido: k tiene curvatura y a corriente baja la pendiente
    real es ~11% mayor que la de gain(). Ver la nota en gain().
    """
    return freq_at_iex_ref(W, L) * (iex / IEX_REF)


def solve_L_for_freq(W: float, f_target: float, iex: float = IEX_REF) -> float:
    """L [um] que da f_target con W fija."""
    f_ref = f_target * IEX_REF / iex
    return (24837.0 * W ** -1.076 / f_ref) ** (1.0 / 0.940)


def solve_W_for_freq(L: float, f_target: float, iex: float = IEX_REF) -> float:
    """W [um] que da f_target con L fija."""
    f_ref = f_target * IEX_REF / iex
    return (24837.0 * L ** -0.940 / f_ref) ** (1.0 / 1.076)


def solve_L_for_gain(W: float, k_target: float) -> float:
    """L [um] que da la ganancia k_target con W fija."""
    return (280.22 * W ** -1.0447 / k_target) ** (1.0 / 0.9923)


def solve_W_for_gain(L: float, k_target: float) -> float:
    """W [um] que da la ganancia k_target con L fija."""
    return (280.22 * L ** -0.9923 / k_target) ** (1.0 / 1.0447)


# --- threshold -------------------------------------------------------------
def _vth_numerator(W: float, L: float) -> float:
    return -16.83 * W + 0.4884 * L + 1.766 * W * L


def vth(W: float, L: float, Cm: float) -> float:
    """Vth [V] de la membrana.  RMS 1.32%.

    Ortogonal a Iex: varia <1.2% con la corriente x16.
    """
    return 1.2792 + _vth_numerator(W, L) / Cm


def solve_Cm_for_vth(W: float, L: float, vth_target: float) -> float:
    """Cm [fF] que da vth_target con (W,L) fijas.

    Lanza ValueError si vth_target <= 1.2792 (la asintota de la ley): por
    debajo de ese valor no hay Cm positivo que lo consiga.
    """
    denom = vth_target - 1.2792
    if denom <= 0:
        raise ValueError(
            f"Vth={vth_target:.3f} V esta en o bajo la asintota (1.2792 V); "
            "ningun Cm lo alcanza"
        )
    return _vth_numerator(W, L) / denom


def vth_max_at(W: float, L: float) -> float:
    """Vth [V] maximo alcanzable con esa geometria.

    Como Cm >= Cm_min y Vth baja al subir Cm, el techo esta en Cm = Cm_min.
    Esta es la razon de que f y Vth esten acoplados: f baja -> W*L grande ->
    Cm_min grande -> Vth acotado.
    """
    return vth(W, L, Cm_min(W, L))


# --- swing -----------------------------------------------------------------
def swing(W: float, L: float, Cm: float) -> float:
    """Excursion de la membrana [V].  RMS 1.68%.

    Exponentes ~ (1, 1, -1): es W*L/Cm, carga acoplada sobre capacitancia.
    """
    return 4.114 * W ** 0.951 * L ** 1.065 * Cm ** -1.006


# --- limite de operacion ---------------------------------------------------
def Cm_min(W: float, L: float) -> float:
    """Cm [fF] minimo para que la membrana no salga del riel.

    Conservadora 10-25%: la frontera medida esta en 0.75-0.93 x este valor.
    """
    return 8.94 * W ** 1.038 * L ** 0.700


# --- entrada ---------------------------------------------------------------
def c_in(W: float) -> float:
    """Capacidad [fF] que la fuente de corriente ve en el nodo de membrana,
    aparte de Cm.  LOO 0.67% RMS, validacion externa 0.56% RMS.

    NO es potencia sino afin, y por la misma razon que Vth: hay un termino
    constante fisico. El 0.945 son las puertas de M1/M2, que cuelgan del nodo
    aunque M5 sea minimo; el 0.865*W es la union de drenador de M5. Una
    potencia pura tendria que pasar por el origen y falla -21% en W=0.22.

    Solo depende de W. L no entra (4 pares de L medidos, <1.5% entre ellos).

    OJO, NO usar para corregir freq(): la ley de frecuencia se ajusto sobre
    simulaciones del circuito completo, con este C_in ya dentro. Sumarlo otra
    vez lo cuenta dos veces. Esto sirve para el contrato hacia la etapa previa
    (es el c_load que esa etapa debe manejar) y como linea base contra la que
    medir la parasita de interconexion cuando se extraiga el layout.

    Residuo conocido: C_in tambien depende de la excursion, no solo de W --
    a mas swing, menos C_in. Entra por ahi lo que parecian dependencias de Cm
    y de L. Esto se lleva hasta el 15% del valor de C_in en las esquinas de
    Cm grande con W pequeña, pero como C_in solo pesa cuando Cm es pequeño, la
    desviacion que traslada a la frecuencia queda bajo 0.15% en todo el
    espacio que el solver alcanza. Sin modelar a proposito: afinarlo mas seria
    afinar una correccion muy por debajo del error de la ley que corrige.
    """
    return 0.945 + 0.865 * W


# --- salida ----------------------------------------------------------------
def c_load_max(w_m7m8: float) -> float:
    """Carga capacitiva [fF] que la salida maneja con tf <= 5 ns.

    La carga NO afecta la frecuencia: <0.7% con C_load de 0 a 1600 fF.
    """
    return 600.0 * w_m7m8


def solve_w_m7m8_for_load(c_load: float) -> float:
    """W [um] de M7/M8 para soportar c_load [fF]."""
    return max(W_MIN, c_load / 600.0)


def i_drive(w_m7m8: float) -> float:
    """Corriente de drive [nA] del buffer de salida."""
    return 85.0 * w_m7m8


# --- requisito sobre la fuente ---------------------------------------------
def min_source_impedance(iex: float, tolerance: float = 0.01) -> float:
    """Impedancia de salida minima [ohm] que debe tener la fuente de corriente.

    Una ro finita inyecta corriente parasita proporcional a la caida sobre
    ella, y el nodo de membrana oscila ~1.9 V respecto a Vdd:

        dI = (Vdd - Vm) / ro        ->      ro = (Vdd - Vm) / (tol * Iex)

    Medido: a 100 nA con ro=100M la frecuencia se desvia +22.7%, y con 3M el
    circuito deja de oscilar. Un espejo simple (1-10 MOhm) NO sirve; hace
    falta cascodo o un transistor largo.
    """
    delta_v = 1.9  # V, caida tipica entre Vdd y el nodo de membrana
    return delta_v / (tolerance * iex * 1e-9)


def freq_error_from_source(iex: float, ro: float) -> float:
    """Error relativo de frecuencia por impedancia de fuente finita."""
    if ro <= 0:
        return float("inf")
    return (1.9 / ro) / (iex * 1e-9)


# --- ventana de corriente --------------------------------------------------
def iex_max(W: float, L: float) -> float:
    """Iex [nA] maxima antes de que el reset no complete.

    El techo es de FRECUENCIA (~4500 kHz), no de corriente: se midio en tres
    configuraciones que morian a 350, 500 y 600 nA pero todas alrededor de
    4400-4600 kHz.
    """
    return F_MAX * IEX_REF / freq_at_iex_ref(W, L)


def iex_window(W: float, L: float) -> tuple[float, float]:
    """Ventana util de corriente [nA].

    No hay piso real: verificado hasta 5 nA con ganancia y swing constantes.
    Lo que se reporto antes como piso era artefacto de ventana de simulacion.
    """
    return (IEX_VERIFIED_MIN, iex_max(W, L))


def geometria_para_iex(lo_nA, hi_nA, paso=24):
    """(W, L) cuya ventana de Iex cubre [lo, hi], o None si ninguna.

    `iex_range` por si sola no elegia geometria: el motor la usaba solo para
    calcular la ganancia junto con `freq_range`, y si le dabas una corriente
    que no cabia devolvia la geometria por defecto. Lo encontro la comprobacion
    de cadena, cuando el STDP entregaba 2764 nA a una neurona de ventana 5-911.

    De las que sirven devuelve la de MENOS area, que es el criterio del resto
    del motor.
    """
    mejor = None
    for i in range(paso + 1):
        W = W_MIN + i * (W_MAX - W_MIN) / paso
        for j in range(paso + 1):
            Lg = L_MIN + j * (L_MAX - L_MIN) / paso
            a, b = iex_window(W, Lg)
            if a <= lo_nA and hi_nA <= b:
                if mejor is None or W * Lg < mejor[0] * mejor[1]:
                    mejor = (W, Lg)
    return mejor
