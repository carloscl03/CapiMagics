"""El nucleo de la POTENCIACION: el plano W x L de M1, denso en la traza.

Por que aqui SI se barre el plano entero, al contrario que en M4:

  En M4 el optimo estaba en el minimo del proceso y ganaba en los tres ejes a
  la vez, asi que `L` dejaba de ser grado de libertad y la region util era un
  punto. Aqui NO hay punto que gane en todo:

      M1          e-plegado   senal max
      0.22/0.28     94.8 mV     87.5 mV
      0.22/1.50    246.1         7.0
      0.22/6.00    541.8         3.3

  Un factor 5.7 de suavidad cuesta un factor 27 de senal. El compromiso lo
  decide la razon A+/A- que quiera el sistema, no la celda -- y el STDP
  biologico es asimetrico a proposito. Asi que se mide todo el plano y el
  motor elige, igual que `IntegratorSpec` recibe su `tradeoff`.

La traza de potenciacion BAJA desde avdd, asi que se parametriza por su
PROFUNDIDAD:  Vtr = 3.3 - vpot.  Con vb_pot = 1.30 la celda llega a Vtr ~ 1.2.

Rejilla consciente de los bins del PDK (cortes en W: 0.22 0.5 1.2 10;
en L: 0.28 0.5 1.2 10). Ninguno de los valores cae en un corte.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

W_G = [0.23, 0.40, 0.80, 1.80, 4.00]
L_G = [0.29, 0.40, 0.80, 2.00, 5.00]
VTR = np.round(np.arange(0.70, 1.3001, 0.03), 4)      # profundidad de la traza
NCW = 10

if __name__ == '__main__':
    t0 = time.time()
    filas = []
    print('  %6s %6s %12s %12s %12s'
          % ('W1', 'L1', 'suelo[mV]', 'senal@1.00', 'senal@1.30'), flush=True)
    for W in W_G:
        for L in L_G:
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
            np.savez('nucleo_pot.npz', filas=np.array(filas, float))
    print('  %d puntos  [%.1f min]' % (len(filas), (time.time() - t0) / 60),
          flush=True)
