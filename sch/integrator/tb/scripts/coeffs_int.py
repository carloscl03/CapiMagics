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

# --- la INYECCION: dV = 10^(INYECCION . base(lgW6,lgL6,lgC,lg(techo-vm)))
# La variable NO es vm, es la DISTANCIA AL TECHO. Con eso, 35 terminos
# sustituyen a los 126 de la version anterior, y el peor caso por
# geometria pasa de 43.7 %% a 11.4 %%.
INYECCION = (
    -2.9135404, -3.3344448, -0.045412404, 3.6757171,
    2.3450879, 2.5478874, -0.3074985, -0.58959057,
    -0.29111742, 0.031927941, 1.5184711, 1.8070496,
    1.135156, -0.7842745, -0.28199385, 0.053013648,
    0.67613309, 1.1058185, -0.26340979, 0.34634478,
    -2.1573038, -2.5434635, -1.0971452, 1.1444137,
    0.6022484, -0.10328505, 1.2269907, -0.1180575,
    -0.18652211, 0.61332691, -0.10760381, -0.42134114,
    -0.0098826193, 0.097639791, -0.053999363,
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
BANDA_CADENA = (74.0, 4500.0)   # kHz
