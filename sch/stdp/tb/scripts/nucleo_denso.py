"""La ley del nucleo, con densidad suficiente para elegir familia.

`L3_dep` tiene pasos de 0.1 V en `Vdep`, o sea SOLO 4 puntos en la region util
[0.55, 0.95]. Con 4 puntos una familia de 4 coeficientes da 0.00 % de error --
interpolacion exacta, no ajuste. No se puede competir nada.

Aqui:
  Vdep   0.50 a 1.00 en pasos de 0.025   -> 21 puntos
  M4     la esquina donde vive el optimo medido (W y L pequenas). No se
         caracteriza W=8, que ya sabemos que da -24 mV de suelo y nunca se
         pondria: caracterizar solo la region que usaremos.

Se guarda la CURVA ENTERA por geometria, no tres numeros resumidos -- que fue
el error de `lec_dep`: los tres numeros son una linealizacion local, no una ley.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

VDEP = np.round(np.arange(0.500, 1.0001, 0.025), 4)
W_G = [0.22, 0.35, 0.50]
L_G = [0.28, 0.45, 0.63]
NCW = 10


def curva(W4, L4):
    cel = K.forzado(K.caps(S.dim(K.BASE, ['M4'], W4, L4), ncw=NCW), 'vdep')
    out = []
    for v in [0.0] + list(VDEP):          # el 0.0 es el suelo
        cuerpo = (K.bias() + ['VFvdep vdepf 0 %.4f' % v]
                  + K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
                  + K.quieto('vpost', 'nvpost'))
        d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep'), cel,
                    extra=' vdepf')
        if not K.arranco_bien(d):
            return None
        out.append(float(d['V']['vw'][-1] - K.VW0))
    return np.array(out)


if __name__ == '__main__':
    t0 = time.time()
    filas = []
    print('  %6s %6s %12s %12s %12s'
          % ('W4', 'L4', 'suelo[mV]', 'senal@0.75', 'senal@1.00'), flush=True)
    for W in W_G:
        for L in L_G:
            c = curva(W, L)
            if c is None:
                print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True)
                continue
            suelo, sen = c[0], c[1:] - c[0]
            for v, s in zip(VDEP, sen):
                filas.append((W, L, v, suelo, s))
            k75 = int(np.argmin(np.abs(VDEP - 0.75)))
            print('  %6.2f %6.2f %12.4f %12.4f %12.4f'
                  % (W, L, suelo * 1e3, sen[k75] * 1e3, sen[-1] * 1e3), flush=True)
            np.savez('nucleo.npz', filas=np.array(filas, float))
    print('  %d puntos  [%.1f min]' % (len(filas), (time.time() - t0) / 60),
          flush=True)
