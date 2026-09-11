"""Constantes medidas de la celda STDP. NO editar a mano.

Se regeneran con `sch/stdp/tb/scripts/gen_coeffs_stdp.py` a partir de los
`.npz` de `sch/stdp/results/`. Caracterizacion completa y validacion en
`sch/stdp/results/stdp_knowledge_base.md`.

Todo esto esta medido sobre el netlist ARREGLADO
(`designs/libs/snn_analog/stdp/stdp_propuesta.spice`), no sobre el original:
sin unir `n3` y `n4` la potenciacion no conduce.
"""

# --- generado por sch/stdp/tb/scripts/gen_coeffs_stdp.py, no editar a mano ---

# nucleo de DEPRESION, familia M1: log s = c_V*V + c_logV*ln(V) + c_1
# cada coeficiente es una cuadratica en ln(W4). L4 FIJA = 0.28 um.
NUC_DEP = (
    (+4.349992e-01, -2.128562e+00, -2.074077e+01),
    (-8.902535e-01, +1.475265e+00, +2.274034e+01),
    (-3.021607e-01, +2.972607e+00, +2.121030e+01),
)
CAJA_W4 = (0.22, 0.90)
SUELO_DEP = (-2.775747e-03, -1.481682e-03)   # [V] = a*W4 + b

# nucleo de POTENCIACION, familia E3, por cada L1 DISCRETA
L1_DISC = (0.40, 0.80, 2.00)
NUC_POT = (
    (   # L1 = 0.40
        (-8.666822e-01, -5.748919e-01, +7.907478e+00),
        (+2.537657e+00, +9.879283e-02, -3.544633e+01),
        (-2.557215e+00, +1.969006e+00, +5.447213e+01),
        (+9.843524e-01, -5.805006e-01, -2.863983e+01),
    ),
    (   # L1 = 0.80
        (+5.269779e-01, +1.500034e+00, -6.469351e+00),
        (-1.524595e+00, -5.912489e+00, +1.162216e+01),
        (+1.339606e+00, +7.758459e+00, +4.039926e+00),
        (-2.452870e-01, -2.418751e+00, -1.192154e+01),
    ),
    (   # L1 = 2.00
        (+7.377913e-01, +8.639781e-01, -1.303014e+01),
        (-2.200821e+00, -3.988731e+00, +3.549414e+01),
        (+2.049600e+00, +5.895829e+00, -2.493628e+01),
        (-4.867880e-01, -1.853406e+00, -1.169532e+00),
    ),
)
CAJA_W1 = (0.23, 1.70)
SUELO_POT = (+7.666903e-04, -2.738296e-04)   # [V] = a*W1 + b ; cruza en W1=0.357

# --- geometrias FIJAS, y por que -------------------------------------------
# L4 esta fijada al minimo del proceso porque el optimo esta ahi y gana en los
# TRES ejes a la vez (e-plegado 123.1 mV contra 74.8, suelo -2.09 contra -2.87,
# senal 499.9 contra 238.9). Ademas entre 0.28 y 0.45 hay una transicion fisica
# donde la dependencia con W cambia de sentido: la ley NO vale fuera.
L4_FIJO = 0.28

# CW de referencia con que se ajustaron los nucleos, en unidades de unitcap.
NCW_REF = 10
CU = 54.5e-15          # un unitcap de 5x5 um
# Parasita FIJA en `vw` que no escala con el array: 0.50 unidades = 27 fF.
# Medida por separado en las dos mitades (0.500 y 0.490): es fisica.
# Resulta ser la PUERTA DE M5:  C0 = 3.26*area_puerta + 2.77 fF
NCW_PAR = 0.50

# --- decaimiento: fisico, sin coeficientes ---------------------------------
# pendiente = Itd / Cdep, con Itd medida en la ENTRADA de la pila.
# -1.7 % contra lo predicho. NO hay fuga ni suelo en Itd: los 20 pA que se
# reportaron eran el amperimetro en el extremo equivocado de la pila.
ETA_VT_DEP = 73.9e-3   # [V] e-plegado del nucleo de depresion
ETA_VT_POT = 138.0e-3  # [V] idem potenciacion

# --- techo de la traza ------------------------------------------------------
# NO lo fija `Vpost - Vth` sino `n5`: la traza carga hasta igualarlo y M12 se
# queda sin Vds. Medido 0.8712 V en las 25 geometrias de M12 (identico a 4
# decimales). Quien lo mueve es M9, de 0.5679 a 0.8793 V.
TECHO_NOMINAL = 0.8712

# --- impedancias de acoplo (analisis .ac a 1 MHz) --------------------------
C_IN_PRE = 1.33e-15    # [F] por sinapsis, sumando vpre + nvpre
C_IN_POST = 1.33e-15   # [F] por sinapsis, sumando vpost + nvpost
C_OUT = 0.504e-15      # [F] por sinapsis en `iout`: SE SUMA A Cm de la neurona
R_OUT = 7.626e8        # [ohm] en `iout`
C_VW = 550.4e-15       # [F] en `vw`, que es pin del LEF
R_VW = 1.436e11        # [ohm] idem -> tau = 79 ms de RETENCION DEL PESO

# --- lectura del peso -------------------------------------------------------
# El M5 original (pfet con la puerta en vw) tiene el SIGNO INVERTIDO: potenciar
# reducia la corriente que recibe la membrana. Estos numeros son de la lectura
# corregida (transconductor nfet + espejo pfet).
IOUT_MAX = 2.231e-6    # [A]
VW_RANGO = (0.80, 2.70)
