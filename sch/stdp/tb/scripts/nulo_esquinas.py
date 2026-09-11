"""Comprobar el nulo del suelo, NO caracterizar esquinas.

La salida no es una ley ni entra en el motor: es una tabla de cuanto se mueve
un punto. El criterio de Euler -- caracterizar solo la region que usaremos --
se aplica al espacio de diseno, que elegimos nosotros. La esquina y la
temperatura no las elegimos, pero tampoco hace falta modelarlas: basta saber si
el hallazgo sobrevive.

Lo que hay que decidir:
  el nulo  (W=0.30, L=6.00)  da +0.12 mV de suelo contra los -5.48 de hoy.
  Sale de que dos efectos opuestos se cancelan, y una resta de dos numeros
  grandes es justo lo que se evapora al mover cualquier cosa.

  si se mueve  +-1 mV  -> seguimos 5x mejor que hoy, la recomendacion vale
  si se mueve  +-6 mV  -> es un espejismo y hay que elegir otro punto
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

PDK = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
NG = '/foss/tools/bin/ngspice'
PID = os.getpid()

GEOM = [('hoy', 0.50, 0.63), ('vecino', 0.50, 3.00), ('el nulo', 0.30, 6.00)]
ESQ = ['typical', 'ss', 'ff']
TEMP = [0, 27, 85]


def suelo(W, L, esquina, temp):
    base = S.dim(K.BASE, ['M3'], W, L)
    cel = K.forzado(K.caps(base, ncw=S.NCW), 'vdep')
    cuerpo = (K.bias() + ['VFvdep vdepf 0 0.0']
              + K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
              + K.quieto('vpost', 'nvpost'))
    ctl = K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep')
    sp, dat = 'nu_%d.spice' % PID, 'nu_%d.dat' % PID
    cab = ['* nulo vs esquina',
           '.include %s/design.ngspice' % PDK,
           '.lib %s/sm141064.ngspice %s' % (PDK, esquina),
           '.option rshunt=1e12',
           '.temp %d' % temp,
           K.B.MIM, cel, 'X1 %s vdepf stdp' % K.PUERTOS,
           'VDD avdd 0 3.3', 'VSS avss 0 0', 'VIO iout 0 0.9']
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl).replace('SALIDA', dat) + '\n')
    subprocess.run([NG, '-b', sp], capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None
    vw = A[:, 1 + 2 * K.NODOS.index('vw')]
    if abs(vw[0] - K.VW0) > 2e-3:          # la guarda de siempre
        return None
    return float(vw[-1] - K.VW0) * 1e3


if __name__ == '__main__':
    print('  suelo de inyeccion [mV], CW = %d unidades\n' % S.NCW)
    print('  %-9s %7s' % ('geometria', 'T[C]') + ''.join('%10s' % e for e in ESQ)
          + '%12s' % 'rango')
    res = {}
    for nom, W, L in GEOM:
        for t in TEMP:
            fila = []
            for e in ESQ:
                v = suelo(W, L, e, t)
                fila.append(v)
            ok = [x for x in fila if x is not None]
            res[(nom, t)] = ok
            print('  %-9s %7d' % (nom if t == TEMP[0] else '', t)
                  + ''.join('%10s' % ('  RECH' if x is None else '%.3f' % x)
                            for x in fila)
                  + '%12s' % ('-' if not ok else '%.3f' % (max(ok) - min(ok))))
        print()
    print('  --- resumen: dispersion total de cada geometria ---')
    for nom, W, L in GEOM:
        todos = [x for t in TEMP for x in res[(nom, t)]]
        if todos:
            print('  %-9s W=%.2f L=%.2f   min %8.3f   max %8.3f   '
                  'rango %7.3f mV   |max| %7.3f'
                  % (nom, W, L, min(todos), max(todos),
                     max(todos) - min(todos), max(abs(x) for x in todos)))
