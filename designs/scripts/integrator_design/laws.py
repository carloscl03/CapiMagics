"""Leyes empiricas del integrador de CapiMagics (GF180MCU).

El integrador es el LECTOR DE LA TASA DE DISPARO: convierte frecuencia de spikes
en una tension continua `vm` que se puede sacar del chip.

    avdd --- M6 (se abre con cada spike, ~33 ns)     INYECCION: sube vm
      |
     vm --- C3 (la memoria; vm es la salida)
      |
     M1 (pfet diodo) --- M2 (espejo de Iref)         FUGA: baja vm
      |
     avss

El equilibrio es donde lo que entra por spike iguala lo que se escapa en un
periodo:

    dV(vm) = I_fuga(vm) / (f * C)

Esa ecuacion es todo el circuito. Mas spikes por segundo -> menos tiempo para
fugarse entre uno y otro -> vm sube.

Procedencia: sch/integrator/results/integrator_knowledge_base.md

Solo stdlib.

AVISO SOBRE LOS EXPONENTES. Igual que en el encoder: son derivadas parciales,
con todo lo demas quieto. No se leen como consejo de diseño.
"""
from __future__ import annotations

from math import log10

from . import coeffs as C

__all__ = [
    "techo", "fuga", "inyeccion", "vm_equilibrio", "rizado",
    "sensibilidad", "resolucion", "f_satura", "ancho_ns", "t_respuesta",
    "c_in", "r_out", "en_caja_fuga", "en_caja_iny", "BANDA_CADENA", "S_MIN",
]

BANDA_CADENA = C.BANDA_CADENA

S_MIN = 0.05   # V. Margen minimo al techo donde la ley de inyeccion vale.
#
# NO ES DECORATIVO. La ley se ajusto exigiendo `techo - vm > 0.05`, y es un
# polinomio de grado 4 en `log10(techo - vm)`: por debajo de ese margen
# log(s) -> -inf y la extrapolacion se dispara. Medido, con W6=0.26, L6=2.0:
#
#     techo - vm = 0.0437 V  ->  dV = 0.0001 mV
#                  0.0237    ->       5.3e+08
#                  0.0007    ->       3.6e+150
#
# Con la version de grado 3 esto no se notaba (era mas suave fuera de su caja)
# y por eso paso desapercibido hasta cambiar de grado.


# --- evaluacion de la base polinomica ---------------------------------------

def _evalua(co, v):
    """Los 35 terminos de la cubica completa en 4 variables.

    Se precalculan las potencias en vez de usar `x**p`: el motor llama a esto
    millones de veces al barrer la rejilla.
    """
    a, b, c, d = v
    P = ((1.0, a, a*a, a*a*a), (1.0, b, b*b, b*b*b),
         (1.0, c, c*c, c*c*c), (1.0, d, d*d, d*d*d))
    t = 0.0
    for k, ex in zip(co, C.EXPONENTES):
        t += k * P[0][ex[0]] * P[1][ex[1]] * P[2][ex[2]] * P[3][ex[3]]
    return t


# --- el techo ---------------------------------------------------------------

def techo(W6, L6):
    """Tension [V] a la que la inyeccion se anula.

    Por encima NO HAY EQUILIBRIO: `dV -> 0`, la inyeccion ya no sostiene a la
    fuga y `vm` se queda clavado. Eso es la SATURACION del integrador, y dice a
    que frecuencia deja de leer cada geometria.

    Depende solo de `W6` y `L6`. `C` no lo mueve nada (2.735 V para los tres
    condensadores medidos) y `W6` apenas 23 mV en un factor 8 de anchura:

        L6 = 0.28 um -> 2.73 V        L6 = 1.00 -> 2.35 V
        L6 = 0.50    -> 2.42          L6 = 2.00 -> 2.33

    7 coeficientes, 6.8 mV de error sobre 48 geometrias.

    CORRIGE al knowledge base, que tenia 2.323 y 1.953: aquellos valores
    estaban topados por una malla de V0 que acababa en 2.45 V -- no se midio el
    techo, se midio el borde del barrido.
    """
    u, w = log10(W6), log10(L6)
    return (C.TECHO[0]
            + C.TECHO[1]*u + C.TECHO[2]*u*u + C.TECHO[3]*u**3
            + C.TECHO[4]*w + C.TECHO[5]*w*w + C.TECHO[6]*w**3)


# --- la fuga ----------------------------------------------------------------

def fuga(vm, W1, W2, L2, Iref):
    """Corriente de fuga [A] que descarga el condensador entre spikes.

    `Iref` en amperios. `L1` va FIJO en `coeffs.L1_FIJO` (0.28 um): fijarlo
    cubre el 78 % del rango del nivel y el 98 % del de la pendiente, y con el
    fijo la ley baja de 5 variables a 4.

    35 coeficientes, 7.37 % K-fold por geometria, 15.2 % en la peor.

    Valida donde `I_fuga > 0.30 * Iref` y `vm` en 1.00-2.45 V.

    REHECHA (2026-09-05). La version anterior se ajusto sobre un barrido que
    fijaba `Iref = 50 nA` en su malla y solo lo movia sobre UNA linea de
    geometria: 12 puntos de 93. `Iref` estaba casi confundido. Contra datos con
    `Iref` cruzado de verdad daba **18.75 % de media y 263 % en el peor caso**,
    cuando en su propia malla reportaba 2.08 %.

    La forma se eligio compitiendo familias: el polinomio de grado 3 (35 coef,
    7.37 %) contra `A + B*vm` con A y B cubicas (40 coef, 7.14 % pero peor
    cola), el grado 4 (70 coef, 5.56 % de media pero 16.9 % de cola) y colapsos
    por `W2/L2` (10 coef, 9.59 % pero 28.6 % de cola).

    La curva de aprendizaje es PLANA (8.77 % con 36 geometrias, 7.37 % con 360):
    es limite de modelo, no de dato. Barrer mas no bajaria de ~7 %.

    Y NO es separable: el doble centrado deja un residuo del 62.7 % con un
    segundo modo al 31 %, asi que `lg(I/Iref) != f(geometria) + g(vm)`.
    """
    v = (log10(W1), log10(W2), log10(L2), vm)
    return Iref * 10.0 ** _evalua(C.FUGA, v)


# --- la inyeccion -----------------------------------------------------------

def inyeccion(vm, W6, L6, Cf):
    """Salto [V] que da `vm` con cada spike. `Cf` en fF.

    LA VARIABLE NO ES `vm`, ES LA DISTANCIA AL TECHO. Con `s = techo - vm`, la
    ley dejo de necesitar los 126 terminos de la version original.

    REHECHA (2026-09-07) sobre un barrido DENSO en la region donde el motor
    opera. La version anterior daba 4.03 % de LOO sobre su propia caja y
    fallaba un -25.6 % en el punto de trabajo -- exactamente los -43 mV de
    sesgo que la validacion de 84 puntos midio en `vm`.

    Ahora: 2.93 % LOO por geometria, 6.0 % en la peor, -6.4 % en el punto de
    trabajo. 70 coeficientes (grado 4): aqui gana en media Y en cola.

    Leida como potencia alrededor de W6=0.25, L6=1.0, C=5111, s=0.5:

        dV = 11.69 mV x (W6/0.25)^+0.62 (L6/1.00)^-1.10 (C/5111)^-0.98
                      x ((techo-vm)/0.50)^+3.46 x 10^correccion

    El `C^-0.98` es `Q/C` casi exacto. Y el exponente +3.46 en la distancia al
    techo es lo que hace que `vm` salga logaritmico en la frecuencia: la
    inyeccion se desvanece deprisa al acercarse al techo, y eso comprime dos
    decadas de frecuencia en un recorrido de tension manejable.

    Devuelve 0.0 en el techo y por encima.
    """
    s = techo(W6, L6) - vm
    if s < S_MIN:
        return 0.0        # ver S_MIN: fuera de la caja el grado 4 explota
    a, b, c, d = log10(W6), log10(L6), log10(Cf), log10(s)
    P = ((1.0, a, a*a, a**3, a**4), (1.0, b, b*b, b**3, b**4),
         (1.0, c, c*c, c**3, c**4), (1.0, d, d*d, d**3, d**4))
    t = 0.0
    for k, ex in zip(C.INY_UTIL, C.EXPONENTES_INY):
        t += k * P[0][ex[0]] * P[1][ex[1]] * P[2][ex[2]] * P[3][ex[3]]
    return 10.0 ** t


# --- el rizado: sin coeficientes --------------------------------------------

def rizado(vm, W1, W2, L2, Iref, Cf, f_kHz):
    """Excursion pico a pico [V] de `vm` en un periodo.

    LEY SIN COEFICIENTES:

        rizado = I_fuga / (f * C)

    Dispersion 1.12x sobre 344 puntos medidos (mediana 1.002, p10 0.954,
    p90 1.069). La cubica de 84 coeficientes ajustada directamente daba 14.38 %.

    Sale de que en equilibrio la carga que entra por spike iguala a la que se
    fuga en un periodo. Es el denominador de la resolucion.

    Correccion conocida y no aplicada: a 4500 kHz el factor cae a 0.90, porque
    el pulso ocupa el 19 % del periodo y la fuga tambien corre durante la
    inyeccion. Es del orden del error de la propia ley de fuga.
    """
    return fuga(vm, W1, W2, L2, Iref) / (f_kHz * 1e3 * Cf * 1e-15)


# --- la composicion: vm no se ajusta, se RESUELVE ---------------------------

def vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_kHz):
    """Tension de reposo [V] a esa frecuencia. `None` si satura o no hay solucion.

    Resuelve  dV(vm) = I_fuga(vm) / (f * C)  por biseccion sobre `vm`.

    23.2 mV de error medio CONTRA NGSPICE, con CERO coeficientes propios: sale
    entera de componer las otras dos leyes. Una cubica de 84 coeficientes
    ajustada directamente a `vm` da 38.8 mV.

    El error se concentra a frecuencia baja (56 mV a 74 kHz, 8 mV a 4500) por
    mal condicionamiento del equilibrio: alli la curva es mas plana y el mismo
    error relativo en las leyes se traduce en mas milivoltios.
    """
    tc = techo(W6, L6)
    lo, hi = C.VM_RANGO[0], min(C.VM_RANGO[1], tc - S_MIN)
    if hi <= lo:
        return None

    def dif(vm):
        return inyeccion(vm, W6, L6, Cf) - rizado(vm, W1, W2, L2, Iref, Cf, f_kHz)

    a, b = dif(lo), dif(hi)
    if a * b > 0:
        return None                       # sin cruce: satura o no arranca
    for _ in range(25):                   # 25 vueltas dan 45 nV sobre 1.45 V
        m = 0.5 * (lo + hi)
        c = dif(m)
        if a * c <= 0:
            hi = m
        else:
            lo, a = m, c
    return 0.5 * (lo + hi)


def f_satura(W1, W2, L2, Iref, W6, L6, Cf, f_max=20000.0):
    """Frecuencia [kHz] a la que esta geometria deja de leer.

    Por encima `vm` se pega al techo y ya no responde. Es el limite que
    `IntegradorSpec` tiene que REPORTAR HACIA ARRIBA, no descubrirse en silicio.

    Devuelve 0.0 si no hay equilibrio en ninguna parte de la banda.

    Ojo con el bracket: a frecuencia MUY baja tampoco hay equilibrio, porque la
    fuga se come la inyeccion. Asi que no vale empezar la biseccion en 1 kHz y
    dar por hecho que ahi funciona -- hay que encontrar primero un punto que si.
    """
    ok = None
    f = 10.0
    while f < f_max:                       # buscar un punto con equilibrio
        if vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f) is not None:
            ok = f
            break
        f *= 1.5
    if ok is None:
        return 0.0
    lo, hi = ok, f_max
    if vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, hi) is not None:
        return hi                          # no satura dentro del rango mirado
    for _ in range(30):
        m = (lo * hi) ** 0.5
        if vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, m) is not None:
            lo = m
        else:
            hi = m
    return lo


def t_respuesta(vm, W1, W2, L2, Iref, Cf):
    """Tiempo de respuesta [us] del lector: `tau = C * vm / I_fuga`.

    ES UNA ESPECIFICACION, NO UN DETALLE. Cuando la neurona cambia de
    frecuencia, `vm` tarda del orden de `tau` en reflejarlo. Un integrador con
    tau de milisegundos no es un lector util por mucha resolucion que tenga.

    Aparecio porque el solver, sin este freno, elegia `Iref` minimo con `C`
    maximo -- lo que minimiza el rizado Y maximiza tau a la vez. Daba
    resoluciones de 127 y 230 con tau de 5 ms.

    Los dos objetivos son OPUESTOS por construccion: bajar el rizado pide poca
    corriente y mucha capacidad, que es justo lo que hace lenta la respuesta.

    Rango medido en el barrido de banda: 180 a 240 us de mediana.
    """
    I = fuga(vm, W1, W2, L2, Iref)
    return 1e6 * Cf * 1e-15 * vm / I if I > 0 else float('inf')


# --- lo que el motor optimiza -----------------------------------------------

def sensibilidad(W1, W2, L2, Iref, W6, L6, Cf, f_lo, f_hi):
    """Pendiente [mV/decada] de `vm` frente a `log10(f)`. `None` si no cubre."""
    a = vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_lo)
    b = vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_hi)
    if a is None or b is None:
        return None
    return 1000.0 * (b - a) / log10(f_hi / f_lo)


def resolucion(W1, W2, L2, Iref, W6, L6, Cf, f_lo, f_hi):
    """Sensibilidad dividida por el rizado PEOR de la banda.

    El rizado peor esta siempre en el extremo de BAJA frecuencia, donde cada
    spike es una fraccion grande de la excursion. Es la figura de merito con la
    que se compara un integrador con otro.
    """
    s = sensibilidad(W1, W2, L2, Iref, W6, L6, Cf, f_lo, f_hi)
    if s is None:
        return None
    v = vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_lo)
    r = 1000.0 * rizado(v, W1, W2, L2, Iref, Cf, f_lo)
    return None if r <= 0 else s / r


# --- el spike que entrega la neurona ----------------------------------------

def ancho_ns(f_kHz):
    """Ancho [ns] del pulso del LIF a esa frecuencia de disparo.

    ES UNA ENTRADA, no un parametro del integrador: lo fija la neurona. Estuvo
    clavado a 32 ns en ocho ficheros de banco sin haberse medido nunca.

    Medido sobre el netlist real, de 26 a 4902 kHz: 32-39 ns, con sigma de
    0.2-0.5 ns. La amplitud llega al riel (3.300 V).

    Su efecto sobre el rizado es <= 2 % en toda la banda, medido con el
    asentamiento validado. (Una primera estimacion mia de "9-24 %" venia de
    interpolar el dV de un spike AISLADO; en regimen el lazo lo reabsorbe.)
    """
    F, A = C.ANCHO_F_KHZ, C.ANCHO_NS
    x = log10(max(F[0], min(F[-1], f_kHz)))
    for i in range(len(F) - 1):
        a, b = log10(F[i]), log10(F[i+1])
        if x <= b:
            return A[i] + (A[i+1] - A[i]) * (x - a) / (b - a)
    return A[-1]


# --- LA INTERFAZ con el resto de la cadena -----------------------------------

def c_in(W6, L6):
    """Capacidad de entrada [fF]: la puerta de M6, que el spike del LIF mueve.

    ES EL DUAL DEL `C_in` DEL ENCODER. `NeuronSpec` acepta `c_in_max` como cota
    de lo que la neurona puede excitar.

    De 0.129 a 15.95 fF segun geometria; **0.547 fF con la que elige el motor**.
    La neurona mueve hasta ~300 fF, asi que NO es restriccion -- pero hay que
    declararlo, no darlo por hecho.

    6 coeficientes, 0.87 % de error medio, 1.97 % peor.
    """
    a, b = log10(W6), log10(L6)
    v = (1.0, a, b, a*b, a*a, b*b)
    return 10.0 ** sum(k*x for k, x in zip(C.C_IN, v)) * 1e15


def r_out(vm, W1, W2, L2, Iref):
    """Impedancia de salida [ohm] en `vm`. `Iref` en amperios.

    `R_out = 1/(dI_fuga/dvm)`.

    **`vm` NO PUEDE MOVER NADA.** 1.74-1.82 GOhm a Iref=5 nA, 0.37-0.40 a 25 nA.
    Hace falta un BUFER entre el integrador y el exterior, y su consumo se
    sumaria al del integrador (25 nA), asi que podria comerse el ahorro. Es un
    bloque que falta en la cadena y que nadie ha dimensionado.

    (El inversor de `tb_integrator` NO sirve de bufer: es un comparador,
    convierte a nivel digital y pierde la tasa, que es justo la informacion.)

    Cubica de 56 coeficientes, 26.7 % K-fold por geometria sobre 3.9 decadas.
    Sale de la derivada de los DATOS, no de la derivada de la ley -- ver coeffs.
    """
    v = (log10(W1), log10(W2), log10(L2), vm, log10(Iref))
    t = 0.0
    for k, ex in zip(C.R_OUT, C.EXPONENTES_ROUT):
        m = k
        for x, p in zip(v, ex):
            if p:
                m *= x ** p
        t += m
    return 10.0 ** t


# --- cajas ------------------------------------------------------------------

def en_caja_fuga(W1, W2, L2, Iref):
    """True si la geometria de la fuga cae donde se midio la ley."""
    return (all(lo <= v <= hi for v, (lo, hi) in
                zip((W1, W2, L2), C.CAJA_FUGA))
            and C.IREF_RANGO[0] <= Iref <= C.IREF_RANGO[1])


def en_caja_iny(W6, L6, Cf):
    """True si la geometria de la inyeccion cae donde se midio la ley."""
    return all(lo <= v <= hi for v, (lo, hi) in zip((W6, L6, Cf), C.CAJA_INY))
