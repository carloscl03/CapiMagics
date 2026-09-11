"""Coeficientes de integrator_design. GENERADO por gen_coeffs_int.py.

NO EDITAR A MANO. Procedencia: sch/integrator/results/ y los barridos
criba2.npz (fuga, 1440 geometrias con Iref cruzado), techo.npz (48
geometrias hasta V0=3.25) e iny3.npz (inyeccion, 200 geometrias).

Generado el 2026-09-05.

Error medido (validacion por GEOMETRIA, no por punto):
    fuga        7.37 %% K-fold, 15.2 %% peor geometria
    inyeccion   4.03 %% LOO,    11.4 %% peor geometria
    techo       6.8 mV
    rizado      dispersion 1.12x SIN coeficientes
    composicion 23.2 mV de error medio en vm
"""

# --- base polinomica: exponentes, cubica completa en 4 variables -------
EXPONENTES = (
    (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 0, 3), (0, 0, 1, 0),
    (0, 0, 1, 1), (0, 0, 1, 2), (0, 0, 2, 0), (0, 0, 2, 1), (0, 0, 3, 0),
    (0, 1, 0, 0), (0, 1, 0, 1), (0, 1, 0, 2), (0, 1, 1, 0), (0, 1, 1, 1),
    (0, 1, 2, 0), (0, 2, 0, 0), (0, 2, 0, 1), (0, 2, 1, 0), (0, 3, 0, 0),
    (1, 0, 0, 0), (1, 0, 0, 1), (1, 0, 0, 2), (1, 0, 1, 0), (1, 0, 1, 1),
    (1, 0, 2, 0), (1, 1, 0, 0), (1, 1, 0, 1), (1, 1, 1, 0), (1, 2, 0, 0),
    (2, 0, 0, 0), (2, 0, 0, 1), (2, 0, 1, 0), (2, 1, 0, 0), (3, 0, 0, 0),
)

# --- la FUGA: I_fuga/Iref = 10^(FUGA . base(lgW1, lgW2, lgL2, vm)) ----
# L1 va FIJO en 0.28 um: fijarlo cubre el 78 %% del rango de A y el 98 %%
# del de B, y con el fijo la ley baja de 5 variables a 4.
L1_FIJO = 0.28
FUGA = (
    -1.8034352, 2.8990814, -1.5455872, 0.27415844,
    0.57057967, -0.35519937, 0.002768675, -0.34676867,
    0.3316655, -0.18905168, 0.039834714, -0.047588809,
    0.015171725, -0.00553622, -0.012152657, 0.032618161,
    0.0090089147, -0.0005470241, -0.0099530297, -0.0072566781,
    0.07350155, -0.093101052, 0.027092732, 0.0040377157,
    -0.0067814932, 0.0083660061, 0.0173355, -0.0079240422,
    0.0011715704, -0.00085231444, 0.041175487, -0.024523451,
    -0.006786829, -0.0041490158, 0.028045057,
)

# --- el TECHO: techo[V] = TECHO . (1, u,u^2,u^3, w,w^2,w^3) -----------
# con u = lg10(W6), w = lg10(L6).  C NO interviene (2.735 V para los
# tres condensadores medidos) y W6 apenas 23 mV en un factor 8.
TECHO = (
    2.341904, 0.035108557, 0.097721015, -0.076739596,
    0.0027669843, 0.24375494, -1.8114291,
)

# --- la INYECCION: dV = 10^(INY_UTIL . base EXPONENTES_INY) -------------
# Variables: lgW6, lgL6, lgC, lg(techo - vm).
#
# REHECHA (2026-09-07) sobre `iny_util.npz`: 100 geometrias x 26 valores de vm
# DENSAS donde el motor opera de verdad (W6 0.26-1.0, L6 1.0-2.8, C 3000-18000,
# vm 1.0-2.25).
#
# La anterior salia de `iny3.npz` -- 200 geometrias aleatorias sobre una caja
# mucho mas ancha -- y daba 4.03 % de LOO ahi. Pero la validacion de 84 puntos
# mostro que el motor SIEMPRE elige L6=2.0, W6 en {0.26,0.5} y C en {5111,12000}:
# una esquina con poquisimo apoyo. En el punto de trabajo fallaba un -25.6 %,
# que por la pendiente d(ln dV)/dvm = 6.9/V da EXACTAMENTE los -43 mV de sesgo
# medidos en vm.
#
# La nueva: 2.93 % LOO por geometria, 6.0 % en la peor, -6.4 % en el punto de
# trabajo. Grado 4 y no 3 porque aqui gana en media Y en cola.

INY_UTIL = (
    -23.440693, -6.0125216, -3.3792345, 2.7256297,
    2.9826185, 23.159269, 4.8588331, 0.53131288,
    0.1204165, -8.4224136, -0.95193089, -0.085291326,
    1.3310817, 0.060137898, -0.080179591, 6.2032582,
    -0.42220931, -3.1195011, 2.7565181, -3.7852917,
    0.31992196, 0.72553815, 0.618721, 0.029826993,
    -0.028118544, -4.3671027, 4.36342, 15.69659,
    2.0450374, -1.1993268, -0.26581492, 0.069772299,
    -3.8722255, 0.28015621, 1.2497242, -10.46589,
    -4.8779601, -1.7740494, -0.93175904, 6.8158792,
    2.1144049, -0.14494314, -1.3930953, -0.23569417,
    0.094706676, 5.04196, 0.50142943, 1.0023244,
    -1.9686597, -0.22709389, 0.19792389, -2.0353295,
    -0.34889404, 0.45109319, 0.15011646, -5.1517544,
    0.015971761, -0.71736393, 1.3242482, 0.053083352,
    -0.16242804, 0.46520818, -0.76878713, -0.044122129,
    -0.12370257, -6.0297066, 0.63847412, -0.09894699,
    0.32558441, -5.0733809,
)

EXPONENTES_INY = (
    (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 0, 3), (0, 0, 0, 4),
    (0, 0, 1, 0), (0, 0, 1, 1), (0, 0, 1, 2), (0, 0, 1, 3), (0, 0, 2, 0),
    (0, 0, 2, 1), (0, 0, 2, 2), (0, 0, 3, 0), (0, 0, 3, 1), (0, 0, 4, 0),
    (0, 1, 0, 0), (0, 1, 0, 1), (0, 1, 0, 2), (0, 1, 0, 3), (0, 1, 1, 0),
    (0, 1, 1, 1), (0, 1, 1, 2), (0, 1, 2, 0), (0, 1, 2, 1), (0, 1, 3, 0),
    (0, 2, 0, 0), (0, 2, 0, 1), (0, 2, 0, 2), (0, 2, 1, 0), (0, 2, 1, 1),
    (0, 2, 2, 0), (0, 3, 0, 0), (0, 3, 0, 1), (0, 3, 1, 0), (0, 4, 0, 0),
    (1, 0, 0, 0), (1, 0, 0, 1), (1, 0, 0, 2), (1, 0, 0, 3), (1, 0, 1, 0),
    (1, 0, 1, 1), (1, 0, 1, 2), (1, 0, 2, 0), (1, 0, 2, 1), (1, 0, 3, 0),
    (1, 1, 0, 0), (1, 1, 0, 1), (1, 1, 0, 2), (1, 1, 1, 0), (1, 1, 1, 1),
    (1, 1, 2, 0), (1, 2, 0, 0), (1, 2, 0, 1), (1, 2, 1, 0), (1, 3, 0, 0),
    (2, 0, 0, 0), (2, 0, 0, 1), (2, 0, 0, 2), (2, 0, 1, 0), (2, 0, 1, 1),
    (2, 0, 2, 0), (2, 1, 0, 0), (2, 1, 0, 1), (2, 1, 1, 0), (2, 2, 0, 0),
    (3, 0, 0, 0), (3, 0, 0, 1), (3, 0, 1, 0), (3, 1, 0, 0), (4, 0, 0, 0),
)

# --- cajas de validez -------------------------------------------------
CAJA_FUGA = ((0.5, 4), (0.5, 4), (0.28, 10))   # W1, W2, L2 [um]
IREF_RANGO = (5e-09, 1e-07)   # A
CAJA_INY = ((0.256, 1.98), (0.283, 1.99), (802, 1.94e+04))    # W6, L6 [um], C [fF]
VM_RANGO = (1.00, 2.45)   # V
FUGA_MIN = 0.30   # la ley de fuga vale donde I_fuga > FUGA_MIN * Iref

# --- el ancho del spike del LIF (entrada, no parametro) ---------------
# Medido sobre el netlist real. Amplitud al riel (3.300 V).
ANCHO_F_KHZ = (26.0, 76.0, 203.0, 501.0, 1219.0, 2743.0, 4902.0)
ANCHO_NS = (33.0, 32.0, 33.0, 33.0, 34.0, 36.0, 39.0)

# --- la banda que la cadena puede producir ----------------------------
# EncoderSpec -> Iex 15-1307 nA -> NeuronSpec -> esta banda.
# El techo lo pone el reset del LIF (F_MAX), no el integrador.
# DERIVADA de la cadena con los defaults, no clavada a ojo. Es lo que la CAPA
# 2 produce: la alimentan 4 sinapsis de 252 nA (1009 nA en total) sobre la
# celda v3 del LIF (ganancia 2.419 kHz/nA), y el suelo es donde la neurona
# empieza a disparar (5 nA).
#   5 nA    -> 12.8 kHz        1009 nA -> 2586 kHz
# El (74, 4500) que decia antes no correspondia a ninguna celda: el 74 es el
# mismo numero fantasma que estaba en spec.py y en el KB. Si cambian los
# defaults de la cadena, esto se recalcula con `cadena.resuelve()`.
BANDA_CADENA = (12.8, 2586.0)   # kHz

# --- LA INTERFAZ: lo que la cadena necesita saber ------------------------
# Igual que `EncoderSpec` reporta `source_ro` y `C_in` para que `NeuronSpec`
# los consuma, el integrador tiene que declarar los suyos. Estaban medidos en
# el knowledge base (seccion 11.3) y el motor no los exponia.
#
# R_out = 1 / (dI_fuga/dvm), sacada de la DERIVADA DE LOS DATOS de criba2.npz,
# NO de la derivada de la ley: el polinomio ajusta valores al 7 % pero su
# pendiente amplifica el ruido -- probado, daba 0.50, 46.03 y 2.15 GOhm al
# mover vm, que es absurdo. Una ley validada en valores NO esta validada en su
# derivada.
#   Cubica, 56 coef, 26.7 % K-fold por geometria sobre 3.9 decadas de rango.
#   (El grado 4 baja a 14.7 % con 126 coeficientes: no compensa para una
#    magnitud que se REPORTA, no que el solver optimice.)
#   Reproduce el KB: 1.81 GOhm a 5 nA (KB 1.74-1.82), 0.40 a 25 (KB 0.37-0.40).
#
# C_in = la puerta de M6, lo que el spike del LIF tiene que mover.
#   lg10(C_in[F]) = C_IN . (1, lgW6, lgL6, lgW6*lgL6, lgW6^2, lgL6^2)
#   6 coeficientes, 0.87 % medio, 1.97 % peor. De 0.129 a 15.95 fF.

R_OUT = (
    -90.967818, -18.450918, -1.0503042, -0.016657807,
    78.737109, 10.349332, 0.36560204, -21.060667,
    -1.252279, 2.0587513, -10.520017, -1.5691534,
    -0.054850002, 5.741818, 0.39912948, -0.61341489,
    0.30699799, 0.11509454, -0.40427406, 0.88336451,
    5.7459668, 0.78789286, 0.025813369, -3.3244172,
    -0.25311225, 0.35724655, 0.32457017, 0.0026729877,
    -0.21752567, -0.083981048, -0.3111848, -0.023219394,
    0.10124828, 0.02204976, -0.015376783, 4.4575277,
    0.62424581, 0.021450835, -2.3103496, -0.16000164,
    0.30348573, 0.37449271, 0.030912145, -0.065710504,
    -0.022836174, -0.029965114, -0.001736144, 0.0085206109,
    -0.006165869, 0.0026516489, 0.74884359, 0.050467393,
    -0.17101668, 0.030997958, -0.0081059286, -0.05476217,
)

EXPONENTES_ROUT = (
    (0, 0, 0, 0, 0), (0, 0, 0, 0, 1), (0, 0, 0, 0, 2), (0, 0, 0, 0, 3),
    (0, 0, 0, 1, 0), (0, 0, 0, 1, 1), (0, 0, 0, 1, 2), (0, 0, 0, 2, 0),
    (0, 0, 0, 2, 1), (0, 0, 0, 3, 0), (0, 0, 1, 0, 0), (0, 0, 1, 0, 1),
    (0, 0, 1, 0, 2), (0, 0, 1, 1, 0), (0, 0, 1, 1, 1), (0, 0, 1, 2, 0),
    (0, 0, 2, 0, 0), (0, 0, 2, 0, 1), (0, 0, 2, 1, 0), (0, 0, 3, 0, 0),
    (0, 1, 0, 0, 0), (0, 1, 0, 0, 1), (0, 1, 0, 0, 2), (0, 1, 0, 1, 0),
    (0, 1, 0, 1, 1), (0, 1, 0, 2, 0), (0, 1, 1, 0, 0), (0, 1, 1, 0, 1),
    (0, 1, 1, 1, 0), (0, 1, 2, 0, 0), (0, 2, 0, 0, 0), (0, 2, 0, 0, 1),
    (0, 2, 0, 1, 0), (0, 2, 1, 0, 0), (0, 3, 0, 0, 0), (1, 0, 0, 0, 0),
    (1, 0, 0, 0, 1), (1, 0, 0, 0, 2), (1, 0, 0, 1, 0), (1, 0, 0, 1, 1),
    (1, 0, 0, 2, 0), (1, 0, 1, 0, 0), (1, 0, 1, 0, 1), (1, 0, 1, 1, 0),
    (1, 0, 2, 0, 0), (1, 1, 0, 0, 0), (1, 1, 0, 0, 1), (1, 1, 0, 1, 0),
    (1, 1, 1, 0, 0), (1, 2, 0, 0, 0), (2, 0, 0, 0, 0), (2, 0, 0, 0, 1),
    (2, 0, 0, 1, 0), (2, 0, 1, 0, 0), (2, 1, 0, 0, 0), (3, 0, 0, 0, 0),
)

C_IN = (-14.91974, 1.0031535, 0.77089614, 0.00092089657, -0.0024814056, 0.1498882)

# ============================================================================
# NIVEL de cada frontera.  ✅ = MEDIDA directamente.
# Sin marca = donde se dejo de barrer; se puede ampliar midiendo.
#
#   CAJA_FUGA  W1, W2 0.5-4      borde de barrido
#              L2  0.28 - 10     el 0.28 es MINIMO DEL PDK              ✅
#                                el 10 es borde de barrido
#   CAJA_INY   W6 0.256 - 1.98   borde de barrido los dos
#              L6 0.283 - 1.99   borde de barrido los dos
#              C  802 - 1.94e4   borde de barrido los dos
#   FUGA_MIN   0.30              CONDICION DE VALIDEZ medida: la ley de fuga
#                                solo vale donde I_fuga > 0.30 * Iref     ✅
#   L1_FIJO    0.28              fijarlo cubre el 78 pct del rango de A y el
#                                98 pct de los casos: criterio MEDIDO      ✅
