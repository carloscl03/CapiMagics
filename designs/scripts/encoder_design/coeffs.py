"""Coeficientes medidos del encoder de CapiMagics (GF180MCU).

GENERADO por sch/encoder/tb/scripts/gen_coeffs.py -- no editar a mano.
Procedencia y método: sch/encoder/results/encoder_knowledge_base.md

Barridos: siete.npz (800 geometrías, leyes directas y viabilidad),
mcley7.npz (150 x 200 tiradas Monte Carlo, desviación),
esquinas7.npz (400 geometrías x 5 esquinas x 3 temperaturas),
ro_fijo.npz (el espejo real con fuente independiente),
iref2.npz (900 divisores de bias, 3.24 décadas).

Error externo medido (validación 70/30, fuera de muestra):
    Iex(-)      0.65 %
    ganancia    0.26 %
    V(a)        0.12 %
    viabilidad  1.28 %
    sigma_Vos   5.6 %
    ro salida   0.09 %
    I_ref       3.15 %
    esquinas    15.2 % (peor caso del factor único; la deriva real es 5x)
"""

# --- dimensiones fijas de la celda ---------------------------------------
LD = 1.600   # um, largo del par de entrada M1/M2
W9 = 0.260   # um, ancho de la cola M9

# --- caja de validez (Wd, Wl, Ll, L9) en um -------------------------------
CAJA = ((0.260, 1.796), (0.300, 2.699), (0.280, 0.620), (0.801, 3.781))
VBIAS_NOMINAL = 1.2   # V
VDIF_MIN, VDIF_MAX = -0.14, 0.14   # V, donde se miden Iex(-) e Iex(+)

# --- punto de referencia del desarrollo -----------------------------------
# Las tres leyes principales se escriben POTENCIA x CORRECCION alrededor de
# este punto. Es una reescritura EXACTA (discrepancia 1e-14), elegida para
# que se lean: la constante es el valor aquí y los exponentes son los de la
# ley de potencia local. REF es FIJO; no es el nominal que deriva el solver.
REF = (0.725, 0.947, 0.394, 1.811)   # Wd, Wl, Ll, L9 en um

# --- base polinómica: exponentes de lg10(v/REF) ---------------------------
# cúbica completa en 4 variables = 35 términos. Los 4 de grado 1 salen
# aparte (son los exponentes) y la constante también; quedan 30 de
# corrección, que son los términos de grado 2 y 3.
EXPONENTES = (
    (0, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 2), (0, 0, 0, 3), (0, 0, 1, 0),
    (0, 0, 1, 1), (0, 0, 1, 2), (0, 0, 2, 0), (0, 0, 2, 1), (0, 0, 3, 0),
    (0, 1, 0, 0), (0, 1, 0, 1), (0, 1, 0, 2), (0, 1, 1, 0), (0, 1, 1, 1),
    (0, 1, 2, 0), (0, 2, 0, 0), (0, 2, 0, 1), (0, 2, 1, 0), (0, 3, 0, 0),
    (1, 0, 0, 0), (1, 0, 0, 1), (1, 0, 0, 2), (1, 0, 1, 0), (1, 0, 1, 1),
    (1, 0, 2, 0), (1, 1, 0, 0), (1, 1, 0, 1), (1, 1, 1, 0), (1, 2, 0, 0),
    (2, 0, 0, 0), (2, 0, 0, 1), (2, 0, 1, 0), (2, 1, 0, 0), (3, 0, 0, 0),
)

# índices de EXPONENTES que son corrección (grado >= 2)
CORRECCION = (2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,)

# Iex a Vdif = -0.14 V.  En REF: 8.007e-08 A
#   IEX_MIN = IEX_MIN_0 * (Wd/0.725)^-0.46797 (Wl/0.947)^-0.86524
#              * (Ll/0.394)^+2.50952 (L9/1.811)^-1.60885 * 10^correccion
IEX_MIN_0 = 8.0067074e-08
IEX_MIN_EXP = (-0.46796509, -0.86524365, 2.5095229, -1.6088519)
IEX_MIN_COR = (
    -0.24988293, 0.54976594, 1.0562665, -0.15077018,
    -6.5009387, -3.3925701, 14.960593, 0.32728094,
    0.06042024, 0.15338327, -0.73845423, -1.4304659,
    -0.036161026, -0.1287088, -0.18912522, 0.14528555,
    -0.47151147, 0.34915361, 0.28260813, 0.067872248,
    -0.79105998, 0.087952183, 0.10242607, -0.19508058,
    -0.029897578, -0.29972388, 0.12954173, 0.15210452,
    0.048831148, -0.0064886231,
)

# dV(x)/dVdif en el centro.  En REF: 0.4004 
#   GAIN = GAIN_0 * (Wd/0.725)^+0.45189 (Wl/0.947)^-0.43638
#              * (Ll/0.394)^+0.53311 (L9/1.811)^+0.02431 * 10^correccion
GAIN_0 = 0.40042334
GAIN_EXP = (0.45189016, -0.43638221, 0.5331072, 0.024308063)
GAIN_COR = (
    0.033638748, -0.0047639095, -0.29204818, -0.20417224,
    0.073024549, 0.40378039, 0.44001343, 0.28251068,
    0.11602552, -0.29904382, -0.3608365, 0.39314188,
    0.092683668, 0.1275725, -0.24494929, 0.11792844,
    -0.22050592, -0.10162851, 0.0025148001, 0.0017707913,
    -0.048016627, -0.0032609023, 0.013547218, 0.0061673081,
    -0.0048101993, -0.026877127, -0.11984392, -0.0038260484,
    0.0034266327, -0.090206238,
)

# tensión del nodo a (cola).  En REF: 0.582 V
#   VA = VA_0 + VA_EXP . lg10(v/REF) + correccion   (sin logaritmo)
VA_0 = 0.58200751
VA_EXP = (0.18935471, 0.00042423053, -0.00030999095, 0.23386629)
VA_COR = (
    -0.10371343, -0.055236692, 0.0020044617, -0.0070982203,
    -0.0022511753, 0.011918898, 0.0024527205, -0.00060394104,
    -0.0030838603, 0.0006841424, -0.00070587884, 0.0019870866,
    2.7165147e-05, -0.00050717875, -0.0079903042, -0.00054501954,
    -0.22154385, 0.090578972, 0.00014780207, -0.0080795996,
    -0.0093718243, -0.00014717456, 0.00020628526, -0.0017552754,
    0.00036183479, -0.011354124, 0.087334212, -0.0010632967,
    0.00074395881, -0.064961779,
)

# --- ley de viabilidad ----------------------------------------------------
# lg10(Iex(+)/Iex(-)) = VIABILIDAD . (1, lgIa, lgG, lgIa^2, lgG^2, lgIa*lgG)
VIABILIDAD = (-2.4710404, -0.43038227, -2.3047641, 0.0086695793, 0.49598801, -0.51768761)

# --- desviación de entrada ------------------------------------------------
# lg10(sigma_Vos [V]) = SIGMA_VOS . (1, lgWd, lgWl, lgLl, lgL9)
SIGMA_VOS = (-2.230747, -0.43624446, -0.025822197, -1.0680803, -0.027569735)

# --- espejo de salida y su impedancia -------------------------------------
WO, LO = 0.93, 1.86   # um, el espejo M5-M8 (fijo en esta celda)
# lg10(ro [ohm]) = polinomio de grado 3 en u = lg10(Iex [A]), ESPEJO FIJO.
# Medido con Wo/Lo fijos y la corriente controlada aparte (ro_fijo.npz).
RO_SALIDA = (-0.02719683, -0.59296355, -5.1168729, -7.0375384)

# --- corriente del divisor de bias M10/M11 --------------------------------
# lg10(I_ref [A]) = I_REF . base EXPONENTES de (lgWn, lgLn, lgWp, lgLp)
I_REF = (-4.705777, -0.73341686, -0.060680917, -0.0057256871, 0.65792909, 0.23424646, -0.046129717, -0.034221131, 0.068438854, -0.11628749, -0.33760543, 0.20486896, -0.025907012, -0.19494013, 0.054081226, -0.042894555, -0.087480675, 0.039350423, -0.029948553, -0.020715901, 0.35369151, -0.23974671, 0.040180855, 0.2265823, -0.075179625, 0.053311483, 0.2320347, -0.061894887, 0.041897469, 0.029368893, -0.058211629, 0.015118344, -0.0059702549, -0.026353253, -0.077523873)

# Caja PROPIA del divisor, distinta de la de la etapa diferencial.
CAJA_BIAS = ((0.22, 4.00), (0.28, 25.00), (0.22, 4.00), (0.28, 25.00))

# --- capacidad de entrada -------------------------------------------------
# lg10(C_in [F]) = C_IN . (1, lgWd, lgWl, lgLl, lgL9)
C_IN = (-14.470695, 0.93402724, -0.010449574, 0.011964494, -0.090444968)

# --- esquinas: factor sobre (Iex, ganancia) respecto de typical/27C -------
ESQUINAS = {
    ("typical",  -40): (0.9362, 1.0406),
    ("typical",   27): (1.0000, 1.0000),
    ("typical",  125): (1.0506, 0.9699),
    ("ff",      -40): (1.8740, 1.0383),
    ("ff",       27): (1.8208, 0.9894),
    ("ff",      125): (1.7313, 0.9446),
    ("ss",      -40): (0.3761, 1.0443),
    ("ss",       27): (0.4797, 1.0153),
    ("ss",      125): (0.5861, 0.9976),
    ("fs",      -40): (1.5493, 1.1151),
    ("fs",       27): (1.5401, 1.0601),
    ("fs",      125): (1.5167, 1.0140),
    ("sf",      -40): (0.5127, 0.9757),
    ("sf",       27): (0.6123, 0.9527),
    ("sf",      125): (0.7024, 0.9354),
}

# ============================================================================
# NIVEL de cada frontera.  ✅ = MEDIDA directamente.
# Sin marca = donde se dejo de barrer; NO es un limite del circuito y se puede
# ampliar midiendo. (En `stdp_design` pasar CAJA_W4 de 0.90 a 1.50 fue eso, y
# desbloqueo disenos que el motor rechazaba.)
#
#   Wd  0.260 - 1.796    los dos son borde de barrido
#   Wl  0.300 - 2.699    idem
#   Ll  0.280 - 0.620    el 0.280 es el MINIMO DEL PDK                  ✅
#                        el 0.620 es borde de barrido
#   L9  0.801 - 3.781    los dos son borde de barrido
#
# Historia que conviene no repetir: el suelo de Ll estuvo en 0.30 por un error
# mio (confundi el L minimo con el W minimo). Corregirlo a 0.28 bajo el area
# un 26 pct. Una frontera sin nivel declarado se hereda sin revisar.
#
# CAJA_BIAS: los 0.22 y 0.28 son minimos del PDK                        ✅
# Los 4.00 y 25.00 son borde de barrido -- y esta caja YA fallo una vez por no
# cubrir su propio punto de uso (llegaba a Ln<=3 y la recomendacion era Ln=10).
