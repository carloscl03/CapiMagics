"""Leyes medidas de la celda STDP.

Todas validadas con LOO POR GEOMETRIA ENTERA -- se deja fuera una geometria
completa y se predice sin haberla visto, que es lo que le pide el motor. El
indicador de salud es que el error interno y el LOO COINCIDAN; cuando se
separan 12x, la ley no tiene los datos que dice tener.

Lo que NO es interpolable, y por que:

  L4   fijada al minimo (0.28). Entre 0.28 y 0.45 la dependencia con `W` cambia
       de sentido; el doble centrado da rango 2. Es una transicion fisica
       canal corto/largo y ninguna forma de bajo orden la atraviesa.
  L1   DISCRETA. LOO dejando fuera una `W` da 3.5-5.2 %; dejando fuera una `L`
       entera da 43-47 % y hasta 140 % en el peor caso. El motor elige de una
       lista corta, que es lo que se hace en layout.
"""
from __future__ import annotations

from math import exp, log, pi

from . import coeffs as C


# --- utilidades -------------------------------------------------------------
def _cuad_lnW(b, W):
    """Un coeficiente como cuadratica en ln(W)."""
    lw = log(W)
    return b[0] * lw * lw + b[1] * lw + b[2]


def _escala_cw(ncw):
    """`CW` entra como divisor, con la parasita fija de `vw` sumada.

    Verificado: `senal * nCW` es constante al 8 % en un factor 8 de capacidad,
    y ese 8 % es SISTEMATICO. Con la parasita baja a 0.04 %.
    """
    return (C.NCW_REF + C.NCW_PAR) / (ncw + C.NCW_PAR)


# --- nucleo: cuanto cambia el peso por evento -------------------------------
def dvw_dep(vdep, W4, ncw=C.NCW_REF):
    """Cambio de peso [V] por evento anticausal, en funcion de la traza.

    NEGATIVO (deprime). `vdep` en [0.50, 1.00] V, `W4` en la CAJA_W4.
    LOO por geometria 3.05 %, peor 4.51 %. Familia elegida por parsimonia:
    empata en peor caso con una de 4 coeficientes usando 3.
    """
    c = [_cuad_lnW(b, W4) for b in C.NUC_DEP]
    s = exp(c[0] * vdep + c[1] * log(vdep) + c[2])
    return -s * _escala_cw(ncw)


def dvw_pot(vtr, W1, L1, ncw=C.NCW_REF):
    """Cambio de peso [V] por evento causal. POSITIVO (potencia).

    `vtr` es la PROFUNDIDAD de la traza: `3.3 - vpot`, en [0.70, 1.30] V.
    `L1` tiene que ser uno de `L1_DISC`: no se interpola (43-47 % de error).
    LOO por geometria 3.5-5.2 %.
    """
    if L1 not in C.L1_DISC:
        raise ValueError("L1 = %s no es interpolable; usa una de %s"
                         % (L1, C.L1_DISC))
    B = C.NUC_POT[C.L1_DISC.index(L1)]
    c = [_cuad_lnW(b, W1) for b in B]
    s = exp(c[0] * vtr ** 3 + c[1] * vtr ** 2 + c[2] * vtr + c[3])
    return s * _escala_cw(ncw)


# --- el suelo: el termino NO HEBBIANO ---------------------------------------
def suelo_dep(W4, ncw=C.NCW_REF):
    """Deriva por spike PRE aunque no haya nada que aprender [V].

    Inyeccion de carga por la puerta de M3 y por la capacidad de `n2`, que va
    con `W4`. Depende SOLO del pre, asi que el peso deriva con actividad
    presinaptica sola: no es hebbiano.

    Los dos terminos son negativos -> NO CRUZA CERO. Para anularlo hay que
    jugar con la `L` de M3, y ese nulo es por cancelacion: 3 mV de dispersion
    en esquinas, peor caso 1.73 mV (contra 5.51 de la geometria original).
    """
    return (C.SUELO_DEP[0] * W4 + C.SUELO_DEP[1]) * _escala_cw(ncw)


def suelo_pot(W1, ncw=C.NCW_REF):
    """Idem por spike POST [V]. NO depende de `L1` (identico a 4 cifras).

    Aqui los terminos tienen signo opuesto, asi que **se anula solo** en
    `W1 = 0.357 um`. Es el remedio limpio; la depresion no lo tiene.
    """
    return (C.SUELO_POT[0] * W1 + C.SUELO_POT[1]) * _escala_cw(ncw)


def w1_suelo_nulo():
    """La `W1` que anula el suelo de potenciacion [um]."""
    return -C.SUELO_POT[1] / C.SUELO_POT[0]


# --- la ventana temporal ----------------------------------------------------
def tau(itd, cdep_uds, lado="dep"):
    """Constante de tiempo efectiva de la ventana [s].

    La traza decae LINEAL (`Itd/Cdep`), pero la lectura es exponencial con
    e-plegado `ETA_VT`, asi que la ventana sale exponencial con

        tau = ETA_VT / (Itd / Cdep)

    NO hay suelo en `Itd`: los 20 pA de fuga que se reportaron eran el
    amperimetro en el extremo equivocado de la pila. Se ha medido a 0.115 nA.
    """
    eta = C.ETA_VT_DEP if lado == "dep" else C.ETA_VT_POT
    return eta * (cdep_uds * C.CU) / itd


def itd_para_tau(t, cdep_uds, lado="dep"):
    """La corriente que da esa ventana [A]."""
    eta = C.ETA_VT_DEP if lado == "dep" else C.ETA_VT_POT
    return eta * (cdep_uds * C.CU) / t


def ventana(dt, itd, cdep_uds, amplitud, lado="dep"):
    """Valor de la ventana STDP a un `dt` [s] dado."""
    return amplitud * exp(-abs(dt) / tau(itd, cdep_uds, lado))


def f_cubierta(itd, cdep_uds, fraccion=0.10, lado="dep"):
    """Frecuencia de disparo por encima de la cual la ventana sigue viva [Hz].

    Por debajo, los intervalos entre spikes son tan largos que la traza ya ha
    decaido. Con `tau = 5.5 us` sale 79 kHz, y la neurona v3 llega a 12.8 kHz:
    la ventana NO cubre el extremo lento salvo que se alargue `tau`.
    """
    return 1.0 / (tau(itd, cdep_uds, lado) * log(1.0 / fraccion))


# --- equilibrio: la condicion que fija el punto de diseno -------------------
def deriva(a_pot, tau_pot, a_dep, tau_dep):
    """Deriva media del peso con pre y post NO correlacionados.

    En STDP aditivo va como `r^2*(A+ tau+ - A- tau-)`. Si no es cero, los pesos
    se van al rail. Esto devuelve el parentesis: CERO es lo que se busca.
    """
    return a_pot * tau_pot - a_dep * tau_dep


# --- impedancias de acoplo --------------------------------------------------
def c_in(n_sinapsis=1, lado="post"):
    """Carga capacitiva [F] que la celda pone sobre la salida de la neurona.

    En el `4x2` cada linea `pre` mueve 2 sinapsis y cada `post` 4. Pasalo como
    `c_load` a `NeuronSpec` en vez de suponerlo -- el motor del LIF tiene
    `c_load_max(w_m7m8)`.
    """
    c = C.C_IN_POST if lado == "post" else C.C_IN_PRE
    return c * n_sinapsis


def c_out(n_sinapsis=4):
    """Capacidad [F] que las sinapsis anaden a la MEMBRANA de la neurona.

    `iout` va a `ifwd`, que es el `Iin` del LIF, o sea la membrana. Se SUMA a
    `Cm`, y en el LIF `Cm` fija el umbral y la excursion (aunque no la
    frecuencia). Con 4 sinapsis son 2.0 fF contra 280: el 0.7 %.
    """
    return C.C_OUT * n_sinapsis


def r_out():
    """Impedancia de salida [ohm] en `iout`.

    763 MOhm: sobre la excursion de membrana (~1.6 V) la corriente entregada
    varia un 0.36 %. La sinapsis entrega carga casi independiente de donde este
    la neurona en su ciclo.
    """
    return C.R_OUT


def retencion_peso():
    """Constante de tiempo con que el peso se olvida [s].

    `vw` es pin del LEF: 550 fF y 144 GOhm -> 79 ms. A las tasas del LIF
    (12.8 kHz a 4.5 MHz) son 10^3 a 10^5 spikes, asi que dentro de un episodio
    de aprendizaje sobra. Pero **los pesos son volatiles**: no hay
    almacenamiento a largo plazo sin refresco.
    """
    return C.R_VW * C.C_VW


# --- cajas ------------------------------------------------------------------
def en_caja_dep(W4, vdep):
    return (C.CAJA_W4[0] <= W4 <= C.CAJA_W4[1]) and (0.50 <= vdep <= 1.00)


def en_caja_pot(W1, vtr):
    return (C.CAJA_W1[0] <= W1 <= C.CAJA_W1[1]) and (0.70 <= vtr <= 1.30)
