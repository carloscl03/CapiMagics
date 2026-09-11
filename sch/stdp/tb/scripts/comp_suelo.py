"""Se suman las dos mejoras del suelo, o interfieren?

M3 y M4 lo bajan por caminos DISTINTOS:
  M3  menos carga inyectada por su propia puerta
  M4  menos capacidad en `n2`, que es con quien `vw` comparte carga

Medidas por separado (a nCW=10):
  hoy            M3 0.50/0.63 + M4 0.50/0.63  ->  -2.87 mV
  solo M3 mejor  M3 0.30/6.00                 ->  ?
  solo M4 mejor  M4 0.22/0.28                 ->  -2.09 mV
  las dos                                     ->  ?

En el integrador tres leyes buenas por separado componian 43 mV de error. No se
asume la suma: se mide.

Y si la composicion es limpia, el plano completo W(M3) x W(M4) no hace falta.
"""
import os
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

NCW = 10
HOY = (0.50, 0.63)
M3_MEJOR = (0.30, 6.00)
M4_MEJOR = (0.22, 0.28)


def caso(m3, m4, vdep=0.0):
    """Suelo (vdep=0) o senal, con M3 y M4 en las geometrias dadas."""
    base = S.dim(K.BASE, ['M3'], *m3)
    base = S.dim(base, ['M4'], *m4)
    cel = K.forzado(K.caps(base, ncw=NCW), 'vdep')
    cuerpo = (K.bias() + ['VFvdep vdepf 0 %.4f' % vdep]
              + K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
              + K.quieto('vpost', 'nvpost'))
    d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep'), cel,
                extra=' vdepf')
    if not K.arranco_bien(d):
        return None
    return float(d['V']['vw'][-1] - K.VW0) * 1e3


if __name__ == '__main__':
    print('  suelo de inyeccion [mV], CW = %d unidades\n' % NCW)
    print('  %-22s %-14s %-14s %10s %12s'
          % ('caso', 'M3 (W/L)', 'M4 (W/L)', 'suelo', 'senal@0.85'))
    combos = [('hoy', HOY, HOY),
              ('solo M3 mejorado', M3_MEJOR, HOY),
              ('solo M4 mejorado', HOY, M4_MEJOR),
              ('los dos', M3_MEJOR, M4_MEJOR)]
    r = {}
    for nom, m3, m4 in combos:
        s = caso(m3, m4)
        g = caso(m3, m4, 0.85)
        r[nom] = s
        print('  %-22s %-14s %-14s %10s %12s'
              % (nom, '%.2f/%.2f' % m3, '%.2f/%.2f' % m4,
                 'RECH' if s is None else '%.4f' % s,
                 'RECH' if g is None else '%.2f' % (g - s)))

    if all(r[k] is not None for k in r):
        h, a, b, ab = r['hoy'], r['solo M3 mejorado'], r['solo M4 mejorado'], r['los dos']
        da, db = a - h, b - h                     # lo que aporta cada uno
        print()
        print('  cambio de M3 solo   %+8.4f mV' % da)
        print('  cambio de M4 solo   %+8.4f mV' % db)
        print('  suma esperada       %+8.4f mV  ->  suelo %8.4f' % (da + db, h + da + db))
        print('  medido con los dos  %+8.4f mV  ->  suelo %8.4f' % (ab - h, ab))
        e = (ab - (h + da + db))
        print()
        print('  INTERFERENCIA: %+.4f mV  (%.1f %% de la suma)'
              % (e, 100 * e / abs(da + db) if da + db else float('nan')))
        print('  -> %s' % ('composicion LIMPIA, no hace falta barrer el plano'
                           if abs(e) < 0.15 * abs(da + db) else
                           'NO se suman: hay que barrer W(M3) x W(M4)'))
