"""Densificar `W` en las L que el diseno puede usar.

El LOO en W con L fija sale 7.4-15.6 % con solo 5 valores de W. En la depresion,
pasar de 3 a 8 valores de W llevo el LOO de 23 % a 3.05 %. Aqui se hace lo mismo.

Se eligen TRES valores de L, no los cinco:
  0.40  zona de transicion canal corto, donde el LOO en W era peor (14.3 %)
  0.80  mejor compromiso medido, LOO 8.1 %
  2.00  lado suave, LOO 8.5 %
Los extremos (0.29 y 5.00) se dejan: el primero es casi el minimo del proceso y
el segundo da 4.8 mV de senal, demasiado poco para equilibrar la depresion.

`L` sigue siendo DISCRETA -- el LOO dejando fuera una L entera da 43-47 % y
hasta 140 % en el peor caso, o sea que no es interpolable en este rango. Eso no
es un defecto del ajuste: estos transistores cruzan la transicion canal
corto/largo y ninguna forma de bajo orden la atraviesa.

Rejilla de W esquivando los cortes de bin del PDK (0.22, 0.5, 1.2).
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

W_G = [0.23, 0.28, 0.34, 0.42, 0.55, 0.75, 1.10, 1.70]
L_G = [0.40, 0.80, 2.00]
VTR = np.round(np.arange(0.70, 1.3001, 0.03), 4)
NCW = 10

if __name__ == '__main__':
    t0 = time.time()
    filas = []
    print('  %6s %6s %12s %12s %12s'
          % ('W1', 'L1', 'suelo[mV]', 'senal@1.00', 'senal@1.30'), flush=True)
    for L in L_G:
        for W in W_G:
            cel = K.forzado(K.caps(S.dim(K.BASE, ['M1'], W, L), ncw=NCW), 'vpot')
            vals, mal = [], False
            for tr in [0.0] + list(VTR):
                cuerpo = (K.bias() + ['VFvpot vpotf 0 %.4f' % (3.3 - tr)]
                          + K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
                          + K.quieto('vpre', 'nvpre'))
                d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vpot'),
                            cel, extra=' vpotf')
                if not K.arranco_bien(d):
                    mal = True
                    break
                vals.append(float(d['V']['vw'][-1] - K.VW0))
            if mal:
                print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True)
                continue
            suelo, sen = vals[0], np.array(vals[1:]) - vals[0]
            for tr, s in zip(VTR, sen):
                filas.append((W, L, tr, suelo, s))
            k = int(np.argmin(np.abs(VTR - 1.00)))
            print('  %6.2f %6.2f %12.4f %12.4f %12.4f'
                  % (W, L, suelo * 1e3, sen[k] * 1e3, sen[-1] * 1e3), flush=True)
            np.savez('pot_denso.npz', filas=np.array(filas, float))
        print(flush=True)
    print('  %d puntos  [%.1f min]' % (len(filas), (time.time() - t0) / 60),
          flush=True)
