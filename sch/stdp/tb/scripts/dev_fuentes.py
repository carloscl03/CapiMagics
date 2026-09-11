"""Caracterizacion a nivel de DISPOSITIVO de las fuentes de corriente.

No hay espejos: el bias es una TENSION en la puerta. Y como `W` y `L` son dos
variables y no un cociente, lo que hace falta es

    I(Vgs, Vds, W, L)     una ley por tipo de transistor

Las cuatro fuentes de la celda (Idep, Ipot, Itd, Itp) son solo dos
dispositivos evaluados en cuatro puntos: lo que las distingue es su `Vds`.
Asi cuatro medidas se convierten en dos, igual que `I_ref` en el encoder.

REJILLA CONSCIENTE DE LOS BINS. El PDK bina en
    L: 0.28  0.5  1.2  10.0  50.0        W: 0.22  0.5  1.2  10.0  100.0
y casi toda la celda del equipo esta sentada JUSTO en W = 0.5 y L = 10, o sea
en el borde, donde los parametros del modelo son discontinuos. La rejilla
esquiva los cortes a proposito, y cada punto guarda su bin para poder atribuir
un salto al modelo en vez de a la fisica.
"""
import os
import re
import subprocess
import sys
import time

import numpy as np

os.chdir('/tmp/stdp')
PID = os.getpid()
NG = '/foss/tools/bin/ngspice'
PDK = '/foss/pdks/gf180mcuD/libs.tech/ngspice'

CORTES_L = [0.28, 0.5, 1.2, 10.0, 50.0]
CORTES_W = [0.22, 0.5, 1.2, 10.0, 100.0]

L_G = [0.35, 0.75, 1.6, 2.8, 6.0]        # ninguno en un corte
W_G = [0.30, 0.80, 2.0, 5.0, 12.0]
# El barrido de Vgs va DENTRO de una sola invocacion de ngspice: la
# densidad es gratis. Con paso de 0.15 V la corriente cambia 4x entre puntos
# y cualquier interpolacion es adivinar (+10.6 % lineal, -8.7 % en log).
VG_G = np.round(np.arange(0.45, 1.5001, 0.025), 4)   # 43 valores
VD_G = [0.3, 1.2, 2.1, 3.0]

VDD = 3.3


def binde(x, cortes):
    for k in range(len(cortes) - 1):
        if cortes[k] <= x < cortes[k + 1]:
            return k
    return len(cortes) - 1


def corre(tipo, W, L, vds):
    """Un barrido en Vgs a Vds fijo. `Vgs` y `Vds` son MAGNITUDES: para el pfet
    el banco las traduce a tensiones absolutas respecto de avdd."""
    if tipo == 'nfet':
        cuerpo = ['M1 d g 0 0 nfet_03v3 W=%.4gu L=%.4gu nf=1' % (W, L),
                  'VD d 0 %.4f' % vds,
                  'VG g 0 0']
        ctl = ['dc VG %.4f %.4f 0.025' % (VG_G[0], VG_G[-1] + 1e-6)]
    else:
        cuerpo = ['VDD vdd 0 %.4f' % VDD,
                  'M1 d g vdd vdd pfet_03v3 W=%.4gu L=%.4gu nf=1' % (W, L),
                  'VD d 0 %.4f' % (VDD - vds),
                  'VG g 0 0']
        # |Vgs| = VDD - v(g)  ->  se barre v(g) al reves
        ctl = ['dc VG %.4f %.4f 0.025' % (VDD - VG_G[-1], VDD - VG_G[0] + 1e-6)]
    sp, dat = 'dv_%d.spice' % PID, 'dv_%d.dat' % PID
    txt = '\n'.join(
        ['* banco de dispositivo',
         '.include %s/design.ngspice' % PDK,
         '.lib %s/sm141064.ngspice typical' % PDK]
        + cuerpo + ['.control'] + ctl
        + ['wrdata %s i(VD)' % dat, '.endc', '.end']) + '\n'
    open(sp, 'w').write(txt)
    r = subprocess.run([NG, '-b', sp], capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None, r
    return A, r


def main():
    t0 = time.time()
    for tipo in ('nfet', 'pfet'):
        filas = []
        print('\n=== %s ===' % tipo, flush=True)
        print('  %6s %6s %6s %5s %5s %14s'
              % ('W', 'L', 'Vds', 'binW', 'binL', 'I(Vgs=0.90)[A]'), flush=True)
        for W in W_G:
            for L in L_G:
                for vd in VD_G:
                    A, r = corre(tipo, W, L, vd)
                    if A is None:
                        print('  %6.2f %6.2f %6.2f   FALLO: %s'
                              % (W, L, vd,
                                 (r.stderr.strip().splitlines() or ['?'])[-1]),
                              flush=True)
                        continue
                    vg, ii = A[:, 0], np.abs(A[:, 1])
                    # para el pfet el eje viene invertido: se pasa a |Vgs|
                    vgs = vg if tipo == 'nfet' else (VDD - vg)
                    o = np.argsort(vgs)
                    vgs, ii = vgs[o], ii[o]
                    for a, b in zip(vgs, ii):
                        filas.append((W, L, a, vd, b))
                    k = int(np.argmin(np.abs(vgs - 0.90)))
                    print('  %6.2f %6.2f %6.2f %5d %5d %14.5g'
                          % (W, L, vd, binde(W, CORTES_W), binde(L, CORTES_L),
                             ii[k]), flush=True)
                    np.savez('dev_%s.npz' % tipo, filas=np.array(filas, float))
        print('  -> %d puntos  [%.1f min]'
              % (len(filas), (time.time() - t0) / 60), flush=True)


if __name__ == '__main__':
    main()
