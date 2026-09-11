"""Leyes empiricas del encoder de CapiMagics (GF180MCU).

El encoder es una VCCS diferencial: dos entradas complementarias (Vin, Vin_neg)
alrededor de un modo comun, un par de entrada M1/M2, cargas pmos en diodo M3/M4,
cola M9, y espejos de salida que entregan Iex a la membrana de cada LIF.

Con `L_in` y `W_tail` fijos (ver coeffs), el espacio de diseño son CUATRO variables:

    W_in   ancho del par de entrada M1/M2
    W_load   ancho de las cargas M3/M4
    L_load   largo de las cargas M3/M4
    L_tail   largo de la cola M9

Procedencia de todo: sch/encoder/results/encoder_knowledge_base.md

Solo stdlib. Son ~35 productos por evaluacion; importar numpy costaria mas que
el calculo entero.

LAS CUBICAS SON DE 35 TERMINOS, Y NO SE PUEDEN ACORTAR. No es que la curva sea
complicada: cada variable por su cuenta es casi una parabola. Lo que cuesta son
los CRUCES -- 22 de los 35 terminos -- y son superaditivos: cada pareja por
separado gana poco, las seis juntas ganan mucho. Probado factorizar y competir
formas estructuradas; todas peores a igual tamaño (seccion 16 del documento).
Cada ley trae abajo su lectura corta alrededor del nominal, que es exacta como
reescritura pero aproximada si la truncas.

AVISO SOBRE LOS EXPONENTES. Los coeficientes de una ley son derivadas
PARCIALES, con todo lo demas quieto. No se leen como consejo de diseño: a
especificacion constante las otras variables se reacomodan y el efecto neto
puede invertirse. Paso con `L_in` en `sigma_vos` (seccion 8.5 del documento).
"""
from __future__ import annotations

from . import coeffs as C

__all__ = [
    "iex_min", "gain", "v_a", "iex_max", "sigma_vos", "area",
    "source_ro", "iex_para_ro", "c_in", "i_ref", "corner_factors", "en_caja", "en_caja_bias",
    "forma_corta", "CONDICIONES", "VA_MIN",
]

VA_MIN = 0.15   # V. Margen de saturacion exigido a M9.

CONDICIONES = tuple(sorted(C.ESQUINAS))


# --- evaluacion: POTENCIA x CORRECCION --------------------------------------
#
# Las tres leyes principales se guardan alrededor de `REF` en la forma
#
#     ley = valor_en_REF  x  PROD (v/REF)^exponente  x  10^correccion
#
# que es una reescritura EXACTA de la cubica de 35 terminos (discrepancia
# 1e-14), no una aproximacion. Se eligio asi para que se LEAN: la constante es
# el valor en el punto de referencia y los cuatro exponentes son los de la ley
# de potencia local, que es como se piensa un circuito.
#
# La `correccion` son los 30 terminos de grado 2 y 3. Sin ella la potencia sola
# da 24 % de media en toda la caja (5.8 % cerca de REF): sirve para entender,
# NO para calcular, y por eso el motor evalua las dos partes.

def _lg(W_in, W_load, L_load, L_tail):
    """lg10 de cada dimension relativa al punto de referencia."""
    from math import log10
    return tuple(log10(v / r) for v, r in
                 zip((W_in, W_load, L_load, L_tail), C.REF))


def _potencia(exps, v):
    """Sum(exponente * lg10(v/REF)) -- el exponente de la ley de potencia."""
    return sum(e * x for e, x in zip(exps, v))


def _correccion(cor, v):
    """Los 30 terminos de grado 2 y 3, en las mismas variables relativas."""
    t = 0.0
    for c, k in zip(cor, C.CORRECCION):
        ex = C.EXPONENTES[k]
        m = c
        for x, p in zip(v, ex):
            if p:
                m *= x ** p
        t += m
    return t


# --- leyes directas ---------------------------------------------------------

def iex_min(W_in, W_load, L_load, L_tail):
    """Iex [nA] en el extremo bajo de la excursion (Vdif = -0.14 V).

    Error externo 0.65 %. Cubica de 35 terminos, `siete.npz`.

    PARA LEERLA, el mismo polinomio alrededor del nominal (cambio de base
    exacto, residuo 1e-14) es una ley de potencia:

        Iex(-) = 80.1 nA x (W_in/0.725)^-0.468 (W_load/0.947)^-0.865
                           (L_load/0.394)^+2.510 (L_tail/1.811)^-1.609

    `L_load` manda (+2.5), `L_tail` va detras (-1.6), `W_in` casi no interviene. Esa
    forma da 5.8 % en media caja: sirve para entender, NO para calcular, y por
    eso aqui se evalua la cubica entera. Ver ECUACIONES.md y la seccion 16 del
    knowledge base.
    """
    v = _lg(W_in, W_load, L_load, L_tail)
    return (C.IEX_MIN_0 * 1e9
            * 10.0 ** (_potencia(C.IEX_MIN_EXP, v) + _correccion(C.IEX_MIN_COR, v)))


def gain(W_in, W_load, L_load, L_tail):
    """Ganancia dV(x)/dVdif en el centro de la excursion.

    Error externo 0.26 %.

    `L_tail` sale con exponente ~0.03: la ganancia NO depende de la cola. Medido
    dos veces, en barridos independientes.

    Alrededor del nominal (exacto, para leer):

        G = 0.400 x (W_in/0.725)^+0.452 (W_load/0.947)^-0.436
                    (L_load/0.394)^+0.533 (L_tail/1.811)^+0.024

    Ahi se ve el +0.024 de `L_tail`. Esa forma da 0.92 % en media caja.
    """
    v = _lg(W_in, W_load, L_load, L_tail)
    return (C.GAIN_0
            * 10.0 ** (_potencia(C.GAIN_EXP, v) + _correccion(C.GAIN_COR, v)))


def v_a(W_in, W_load, L_load, L_tail):
    """Tension [V] del nodo `a` (drenador de la cola M9) en el centro.

    Es el margen de saturacion de M9: debe quedar sobre VA_MIN. Error 0.12 %.

    En las 15 condiciones de proceso y temperatura medidas nunca bajo de
    350 mV, sobre 6000 casos. La restriccion no llega a morder.

    Alrededor del nominal (exacto, para leer):

        V(a) = 0.582 V + 0.189 lg10(W_in/0.725) + 0.234 lg10(L_tail/1.811)

    `W_load` y `L_load` salen en CERO exacto: el nodo `a` solo ve el par de entrada y
    la cola. Esa forma da 2.1 mV en media caja.
    """
    v = _lg(W_in, W_load, L_load, L_tail)
    return C.VA_0 + _potencia(C.VA_EXP, v) + _correccion(C.VA_COR, v)


def forma_corta(digitos=3):
    """Las tres leyes escritas como potencia, en texto, para leer o citar.

    Es la MISMA ley que evalua el motor, sin su correccion. La correccion son
    los terminos de grado 2 y 3, y sin ella el error es 5.8 % cerca de `REF` y
    24 % en toda la caja. Para entender el circuito, no para calcular.
    """
    W = C.REF
    f = "%%+.%df" % digitos
    def pot(exps):
        return "  ".join(("(%s/%.3f)^" + f) % (n, w, e)
                          for n, w, e in zip(("W_in", "W_load", "L_load", "L_tail"), W, exps))
    return "\n".join([
        "Iex(-) = %.1f nA  x  %s" % (C.IEX_MIN_0 * 1e9, pot(C.IEX_MIN_EXP)),
        "G      = %.3f     x  %s" % (C.GAIN_0, pot(C.GAIN_EXP)),
        "V(a)   = %.3f V   +  %s" % (C.VA_0, "  ".join(
            ("%+.3f lg10(%s/%.3f)" % (e, n, w))
            for n, w, e in zip(("W_in", "W_load", "L_load", "L_tail"), W, C.VA_EXP)
            if abs(e) > 5e-4)),
    ])


# --- ley de viabilidad ------------------------------------------------------

def iex_max(iex_min_nA, gain_):
    """Iex [nA] en el extremo alto, DEDUCIDO del extremo bajo y la ganancia.

    Los tres objetivos NO son independientes. La imagen del espacio de diseño
    en (Iex(-), Iex(+), G) es una SUPERFICIE de espesor 0.022 decadas, no un
    volumen: fijados dos, el tercero esta determinado.

    Por eso un pedido de tres cifras inventadas casi nunca existe, y por eso
    EncoderSpec se pide con (iex_min, gain).

    Error externo 1.26 %. Reproducida por dos barridos independientes: sobre
    cuatro pedidos de prueba coincide con la version anterior dentro del 1.5 %.
    """
    from math import log10
    a, g = log10(iex_min_nA * 1e-9), log10(gain_)
    k = (1.0, a, g, a * a, g * g, a * g)
    return iex_min_nA * 10.0 ** sum(c * x for c, x in zip(C.VIABILIDAD, k))


# --- desapareamiento --------------------------------------------------------

def sigma_vos(W_in, W_load, L_load, L_tail):
    """Desviacion tipica [V] de la tension de entrada, por desapareamiento.

    Medida por Monte Carlo con los modelos del PDK (`sw_stat_mismatch=1`),
    150 geometrias x 200 tiradas. Error externo 5.6 %.

    LA PALANCA ES `L_load`, NO EL PAR DE ENTRADA. Exponentes: W_in -0.44, L_load -1.07,
    y W_load y L_tail en 0.03 (no intervienen). El reflejo habitual de "agrandar el par
    de entrada" da 1.7x de mejora; guiarse por esta ley da 3.1x por la misma
    area. El par de carga pone el suelo: en subumbral gm = I/(n*VT) para los
    dos pares con la misma corriente, asi que la carga refiere su desviacion a
    la entrada casi con ganancia unidad.
    """
    from math import log10
    v = (1.0, log10(W_in), log10(W_load), log10(L_load), log10(L_tail))
    return 10.0 ** sum(c * x for c, x in zip(C.SIGMA_VOS, v))


# --- impedancia de salida: la interfaz con el LIF ---------------------------

def source_ro(iex_nA, Wo=None, Lo=None):
    """Impedancia de salida [ohm] que ve la membrana del LIF.

    ES EL CAMPO `source_ro` DE NeuronSpec: lo que hace que los dos motores
    compongan. `NeuronSpec` lo pide para calcular el error esperado, y su ley
    dice que hacen falta 1.9 / (tol * iex) GOhm.

    Medida CON EL ESPEJO FIJO de esta celda (WO, LO) y la corriente controlada
    de forma independiente. Polinomio de grado 3 en lg10(Iex): error medio
    0.09 %, peor 0.33 %.

    `Wo` y `Lo` se aceptan por compatibilidad pero NO se usan: la ley es de una
    sola variable. Para otro espejo hay que volver a medir.

    CORRECCION (2026-09-03): la primera version se ajusto sobre un barrido
    donde `Wo`, `Lo` y la corriente estaban ACOPLADOS -- la corriente la fijaba
    la geometria, no era independiente. Daba 9.4 % de error y la conclusion
    falsa de que el cruce del 1 % estaba en 126 nA.

    LO QUE DICE LA MEDIDA BUENA: el espejo NO cumple el 1 % en ningun punto, y
    el error es PEOR a corriente baja.

        Iex        ro          error que ve el LIF
          5 nA   1.36e+10             2.8 %
         20      4.18e+09             2.3 %
        100      1.13e+09             1.7 %
        400      3.55e+08             1.3 %

    Importa porque el estudio de acoplamiento con NeuronSpec dice que la
    demanda se concentra en corrientes BAJAS (mediana 17.6 nA).
    """
    from math import log10
    u = log10(iex_nA * 1e-9)
    return 10.0 ** (((C.RO_SALIDA[0] * u + C.RO_SALIDA[1]) * u
                     + C.RO_SALIDA[2]) * u + C.RO_SALIDA[3])


def c_in(W_in, W_load, L_load, L_tail):
    """Capacidad de entrada [fF] por pin (Vin o Vin_neg).

    ES EL DUAL DEL `C_in` DE LA NEURONA: lo que la etapa anterior tiene que
    mover, igual que el `C_in` del LIF (2.03 fF) es lo que mueve el encoder.
    `NeuronSpec` lo llama `c_in_max` cuando lo recibe como cota.

    En un MOS la impedancia de entrada en continua es practicamente infinita
    (solo fuga de puerta), asi que la magnitud que importa es esta.

    Medida con `.ac` a 1 kHz, una fuente por geometria, 300 puntos.
    De 0.86 a 5.65 fF en la caja; mediana 2.31 fF. Error externo 0.73 %.

    Depende casi solo de `W_in` (exponente 0.934, cerca de 1 como corresponde a
    una capacidad de puerta con `L_in` fijo). `W_load` y `L_load` estan en 0.01: no
    intervienen. El 0.934 en vez de 1.0, y el termino de `L_tail`, son el efecto
    Miller: `Cgd` se multiplica por (1 + ganancia) y la ganancia si depende de
    las otras dimensiones.
    """
    from math import log10
    v = (1.0, log10(W_in), log10(W_load), log10(L_load), log10(L_tail))
    return 10.0 ** sum(c * x for c, x in zip(C.C_IN, v)) * 1e15


def iex_para_ro(tol=0.01, Wo=None, Lo=None):
    """Corriente [nA] hasta la que el espejo sostiene una tolerancia `tol`.

    Devuelve 0.0 si la tolerancia no se alcanza en ningun punto, que es lo que
    pasa con `tol = 0.01` en el espejo de esta celda: el error va de 2.8 % a
    5 nA hasta 1.2 % a 800 nA, sin bajar nunca del 1 %.

        iex [nA]      ro [ohm]    LIF pide (1%)    error real
              5       1.36e+10       3.71e+10          2.8 %
             20       4.18e+09       9.72e+09          2.3 %
            100       1.13e+09       1.90e+09          1.7 %
            400       3.55e+08       4.75e+08          1.3 %

    Se arregla en el espejo, no en la etapa diferencial. Cuanto ayuda alargar
    `Lo` o cascodear NO esta medido: esta ley es de una variable.
    """
    if 1.9e9 / (source_ro(1.0) * 1.0) > tol:
        return 0.0                      # no se alcanza en ningun punto
    lo, hi = 1.0, 5000.0
    for _ in range(60):
        m = (lo * hi) ** 0.5
        if 1.9e9 / (source_ro(m) * m) <= tol:
            lo = m
        else:
            hi = m
    return lo


# --- el bloque de polarizacion ----------------------------------------------

def i_ref(Wn, Ln, Wp, Lp):
    """Corriente [uA] que consume el divisor de bias M10/M11.

    Es el mayor consumidor de todo lo medido en la celda, y por eso esta aqui:
    el divisor del equipo (0.5/0.28 : 0.5/0.28) chupa 43.2 uA, contra 14.6 de
    la neurona, 2.93 de la etapa diferencial y 0.05 del integrador.

    ES UNA LEY DEL DIVISOR, NO DE LA ETAPA DIFERENCIAL. Sus cuatro variables
    son las dimensiones de M10 (nmos) y M11 (pmos), que no son ninguna de las
    cuatro del resto del paquete. Caja propia: `coeffs.CAJA_BIAS`.

    Cubica de 35 terminos sobre `iref2.npz` (900 geometrias, 3.24 decadas).
    Externo 3.15 %; validada POR GEOMETRIA en 12 puntos fuera de la malla al
    2.14 % medio, 3.61 % peor. La ley de potencia que estuvo antes daba 41 %
    de media y 539 % en el peor caso: no servia.

    RECOMENDACION MEDIDA: `Ln = 10, Lp = 20` da 0.585 uA -- 74x menos que el
    divisor actual -- Y ADEMAS el doble de seguimiento de esquina (99 mV
    contra 44). Gana en las dos cosas a la vez, que es raro.

    No colapsa a (Wn/Ln, Wp/Lp): probado hasta grado 6, se estanca en 6.7 %
    y el residuo correlaciona con `Wp` (-0.62) y `Lp` (-0.41) por separado.
    El lado pmos no obedece a la relacion de aspecto sola.
    """
    from math import log10
    z = (log10(Wn), log10(Ln), log10(Wp), log10(Lp))
    t = 0.0
    for c, ex in zip(C.I_REF, C.EXPONENTES):
        m = c
        for x, p in zip(z, ex):
            if p:
                m *= x ** p
        t += m
    return 10.0 ** t * 1e6


def en_caja_bias(Wn, Ln, Wp, Lp):
    """True si el divisor cae en la caja donde se midio `i_ref`."""
    return all(lo <= v <= hi for v, (lo, hi) in
               zip((Wn, Ln, Wp, Lp), C.CAJA_BIAS))


# --- geometria --------------------------------------------------------------

def area(W_in, W_load, L_load, L_tail):
    """Area activa [um2] de la etapa diferencial (sin los espejos de salida)."""
    return W_in * C.LD + 2.0 * W_load * L_load + C.W_tail * L_tail


def en_caja(W_in, W_load, L_load, L_tail):
    """True si la geometria cae dentro de la caja donde se midieron las leyes."""
    return all(lo <= v <= hi for v, (lo, hi) in
               zip((W_in, W_load, L_load, L_tail), C.CAJA))


# --- esquinas ---------------------------------------------------------------

def corner_factors(corner="typical", temp=27):
    """Factores (Iex, ganancia) respecto de typical/27C. 1.0 = sin deriva.

    Un solo numero por condicion, con 15 % de error en el peor caso -- de sobra
    cuando lo que describe es una deriva de 3.3x a 10.7x (mediana 5.0x).

    Modelar esto fino costaria 725 coeficientes para bajar ese 15 % al 1.35 %:
    refinar la tercera cifra de algo que se mueve un factor 5. El bloque fino
    esta medido en `esquinas7.npz` por si algun dia la polarizacion se arregla
    y la deriva residual baja al 3-13 %.

    EL PROBLEMA DE FONDO NO ES DE MODELADO SINO DE CIRCUITO. Ninguna cantidad
    de coeficientes arregla que Iex se mueva un factor 5 entre chips; lo arregla
    la polarizacion (ajuste por chip, referencia compensada, o hacer el sistema
    ratiometrico con el LIF). Ver seccion 7 del documento.
    """
    t = min((-40, 27, 125), key=lambda x: abs(x - temp))
    if (corner, t) not in C.ESQUINAS:
        raise ValueError(
            "condicion desconocida: %r a %r C. Disponibles: %s"
            % (corner, temp, ", ".join(sorted({c for c, _ in C.ESQUINAS})))
        )
    return C.ESQUINAS[(corner, t)]
