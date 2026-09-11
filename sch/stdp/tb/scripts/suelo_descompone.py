"""De donde sale el suelo de inyeccion?

Estrechar M3 de W=0.50 a 0.22 (2.3x) solo baja el suelo un 17.5 %, y cambiar su
`L` no hace nada. Si fuera carga de puerta de M3 deberia haber caido a la
tercera parte. O sea que la mayor parte del suelo NO ES M3.

El spike pre mueve DOS puertas: `vpre` (M3, la mitad de depresion) y `nvpre`
(M8, la mitad de POTENCIACION). Hipotesis: el grueso del suelo es acoplo
cruzado desde la otra mitad.

Se descompone pulsando cada uno por separado:

    a) vpre y nvpre     el caso real
    b) solo vpre        lo que aporta M3
    c) solo nvpre       lo que aporta el cruce

Si a ~ b + c, los dos caminos son independientes y se puede atribuir. Y si `c`
domina, estrechar los interruptores NO arregla el termino no hebbiano -- lo que
cambiaria la prioridad del plan.
"""
import os
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S


def suelo(W, L, pulsa_vpre=True, pulsa_nvpre=True):
    """Suelo de depresion con `vdep` forzado a 0: no hay traza que leer, asi
    que todo lo que salga es artefacto."""
    base = S.dim(K.BASE, ['M3'], W, L)
    cel = K.forzado(K.caps(base, ncw=S.NCW), 'vdep')
    p = []
    p += (['VVPRE vpre 0 PULSE(0 3.3 %.6g 1n 1n %.6g 1)' % (K.T0, K.DTP0)]
          if pulsa_vpre else ['VVPRE vpre 0 0'])
    p += (['VNVPRE nvpre 0 PULSE(3.3 0 %.6g 1n 1n %.6g 1)' % (K.T0, K.DTP0)]
          if pulsa_nvpre else ['VNVPRE nvpre 0 3.3'])
    cuerpo = K.bias() + ['VFvdep vdepf 0 0.0'] + p + K.quieto('vpost', 'nvpost')
    d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep'), cel,
                extra=' vdepf')
    if not K.arranco_bien(d):
        return None
    return float(d['V']['vw'][-1] - K.VW0) * 1e3


if __name__ == '__main__':
    print('  %6s %6s %10s %10s %10s %10s %8s'
          % ('W(M3)', 'L(M3)', 'a: ambos', 'b: vpre', 'c: nvpre', 'b+c', 'a-(b+c)'))
    for W, L in ((0.50, 0.63), (0.22, 0.28), (2.00, 0.63), (0.50, 2.00)):
        a = suelo(W, L, True, True)
        b = suelo(W, L, True, False)
        c = suelo(W, L, False, True)
        if None in (a, b, c):
            print('  %6.2f %6.2f   RECHAZADO' % (W, L))
            continue
        print('  %6.2f %6.2f %10.4f %10.4f %10.4f %10.4f %8.4f'
              % (W, L, a, b, c, b + c, a - (b + c)))
    print()
    print('  (mV sobre CW = %d unidades)' % S.NCW)
