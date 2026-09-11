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
    (-1.452045e+00, -5.454292e+00, -2.183904e+01),
    (+3.246751e-01, +3.629617e+00, +2.346295e+01),
    (+1.415467e+00, +6.001363e+00, +2.221186e+01),
)
# CAJA de `W4`, y QUE la limita. La marca ✅ = frontera MEDIDA:
#   >= 0.22    minimo del PDK                                    ✅
#   <= 1.50    hasta aqui la ley vale: LOO 4.02 por ciento, peor 8.68.
#              HAY datos hasta 4.00 en `nucleo_w_full.npz`, pero ahi
#              el LOO sube a 8.05 y el peor a 27.89.
#   en Vdep=1.0 y W4 ~1.5 la senal SATURA en ~1.63 V: choca con el
#              recorrido del peso. Ese SI es limite fisico        ✅
# Antes decia 0.90, que era solo donde deje de medir: hacia que el
# motor recortase disenos validos por un 1.7 por ciento de amplitud.
CAJA_W4 = (0.22, 1.50)
SUELO_DEP = (-2.786000e-03, -1.477326e-03)   # [V] = a*W4 + b

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
# Dimensionado por la CADENA, no por la celda: `ifwd` recoge n_post
# sinapsis en paralelo y el LIF no admite mas de 2758 nA en ninguna
# geometria, y ese maximo esta en la frontera de W_M5. Con 4 x 252 =
# 1009 nA la neurona sale W=3.09 L=20, con 12 pct de margen.
# (La primera version daba 2231 por
# sinapsis: 8924 con las cuatro, factor 9.8 de exceso.)
IOUT_MAX = 0.166e-6    # [A] por sinapsis; 4 x 166 = 662 contra los
                       # 716 que admite la celda -> ganancia 0.925.
                       # NO se deja en 1.000 exacto: disenar contra
                       # el limite fallo tres veces en esta sesion.
VW_RANGO = (0.80, 2.70)

# ============================================================================
# CAJAS, CON SU NIVEL.  ✅ = frontera MEDIDA directamente.
# Sin marca, es donde se dejo de medir y NO se puede tratar como limite.
# ============================================================================
#
# `W4` -- lectura de la traza de depresion
#   >= 0.22 um   minimo del PDK                                          ✅
#   <= 1.50 um   hasta aqui la ley vale: LOO 4.02 pct, peor 8.68.
#                Hay datos medidos hasta 4.00 en `nucleo_w_full.npz`, pero
#                alli el LOO sube a 8.05 y el peor a 27.89. El corte es una
#                decision de precision, no un limite del circuito.
#   saturacion   con Vdep=1.0 y W4 ~1.5 la senal se aplana en ~1.63 V:
#                choca con el recorrido del peso                         ✅
#
# `W1` -- lectura de la traza de potenciacion
#   >= 0.23 um   primer punto medido (el minimo del PDK es 0.22)
#   <= 1.70 um   ultimo punto medido
#   UTIL <= ~1.28  por encima, A+ se pasa del maximo que la depresion puede
#                igualar (683.5 mV con W4 <= 1.50), asi que no se puede
#                equilibrar. Y ademas el suelo de potenciacion crece
#                +0.77 mV por um de W1: un W1 grande paga termino no hebbiano
#
# `Vdep` -- profundidad de la traza en que se lee
#   >= 0.50 V    por debajo la senal se entierra en el suelo: a 0.40 V el
#                STDP real son 0.050 mV contra 2.832 de inyeccion            ✅
#   <= 1.00 V    por encima la lectura sale de subumbral y la VENTANA pierde
#                la forma exponencial: medido en `barE_2p15.npz`, con
#                Vdep0=1.035 la ventana sale con meseta                      ✅
#
# `itd` -- corriente de decaimiento
#   <= 7.4 nA    ultimo punto medido
#   >= ~16 pA    aqui la fuga del dispositivo (0.8 pA) es el 5 pct de Itd y
#                la ley empieza a irse. Medido bajando hasta 1.6 pA:
#                  Itd 127 pA -> -0.21 pct     Itd 20 pA -> -9.25 pct
#                  Itd 5.4 pA -> -41 pct       Itd 1.6 pA -> -134 pct        ✅
#                El exceso es constante (~2.2 pA) y de el 1.47 pA son el
#                `rshunt` del BANCO, no del circuito: el dispositivo fuga
#                0.73-0.86 pA.
#                -> tau maxima util ~500 us, o sea cubre f >= 0.9 kHz.
#                (El "suelo de 0.4 nA" que se reporto antes era el amperimetro
#                 en el extremo equivocado de la pila: no existia.)
ITD_CAJA = (16e-12, 7.4e-9)
FUGA_VDEP = 0.8e-12        # [A] fuga real del dispositivo, medida sin rshunt
W1_UTIL_MAX = 1.28         # por encima no se puede equilibrar
VDEP_CAJA = (0.50, 1.00)
VTR_CAJA = (0.70, 1.30)
