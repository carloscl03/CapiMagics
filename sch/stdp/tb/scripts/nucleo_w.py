"""La ley del nucleo con L(M4) FIJADA al minimo.

Por que se fija, y medido -- no opinado:

  1. El optimo de M4 esta en L = 0.28 y gana en los TRES ejes a la vez:
     e-plegado 123.1 mV (vs 74.8), suelo -2.09 mV (vs -2.87), senal 499.9 (vs
     238.9). No hay nada que negociar hacia L mas larga.

  2. Entre L=0.28 y L=0.45 hay una transicion fisica: la dependencia con W
     CAMBIA DE SENTIDO (c_V va de -16.4 a -19.0 con W a L=0.28, y de -20.9 a
     -20.3 a L=0.45). Con doble centrado el residuo es 0.89-1.24 y los valores
     singulares 1.000/0.155-0.353: rango 2, NO separable. Ninguna ley de
     potencia describe eso.

  3. Con L fija la interaccion desaparece por construccion y los coeficientes
     vuelven a ser monotonos y suaves en W.

Asi que `L` no es variable de diseno para M4: es una constante del problema.
Caracterizar hasta 0.63 seria modelar una region que no se va a usar.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

L4 = 0.28                                  # el minimo del proceso
W_G = [0.22, 0.26, 0.30, 0.36, 0.44, 0.55, 0.70, 0.90]
VDEP = np.round(np.arange(0.500, 1.0001, 0.025), 4)
NCW = 10

if __name__ == '__main__':
    t0 = time.time()
    filas = []
    print('  L(M4) fijo en %.2f um\n' % L4, flush=True)
    print('  %6s %12s %12s %12s'
          % ('W4', 'suelo[mV]', 'senal@0.75', 'senal@1.00'), flush=True)
    for W in W_G:
        cel = K.forzado(K.caps(S.dim(K.BASE, ['M4'], W, L4), ncw=NCW), 'vdep')
        vals = []
        mal = False
        for v in [0.0] + list(VDEP):
            cuerpo = (K.bias() + ['VFvdep vdepf 0 %.4f' % v]
                      + K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
                      + K.quieto('vpost', 'nvpost'))
            d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep'),
                        cel, extra=' vdepf')
            if not K.arranco_bien(d):
                mal = True
                break
            vals.append(float(d['V']['vw'][-1] - K.VW0))
        if mal:
            print('  %6.2f   RECHAZADO' % W, flush=True)
            continue
        suelo, sen = vals[0], np.array(vals[1:]) - vals[0]
        for v, s in zip(VDEP, sen):
            filas.append((W, L4, v, suelo, s))
        k = int(np.argmin(np.abs(VDEP - 0.75)))
        print('  %6.2f %12.4f %12.4f %12.4f'
              % (W, suelo * 1e3, sen[k] * 1e3, sen[-1] * 1e3), flush=True)
        np.savez('nucleo_w.npz', filas=np.array(filas, float))
    print('  %d puntos  [%.1f min]' % (len(filas), (time.time() - t0) / 60),
          flush=True)
