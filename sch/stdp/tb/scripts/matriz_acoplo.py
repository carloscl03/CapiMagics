"""Matriz de acoplo del STDP, CALCULADA de las leyes, no escrita de memoria.

Cada celda es `d(ln salida) / d(ln perilla)` en el punto nominal: +1 quiere
decir proporcional, ~0 ortogonal, -1 inversa. Es el formato de la matriz del
LIF, que es lo que permite ver de un vistazo que perilla toca que cosa.
"""
import sys

import numpy as np

sys.path.insert(0, 'designs/scripts')
from stdp_design import coeffs as C, laws as L, solver as S

NOM = dict(W4=0.297, W1=0.357, L1=0.40, ncw=10, ncdep=2, itd=1.4646e-9)


def sal(p):
    q = dict(NOM)
    q.update(p)
    a_dep = abs(L.dvw_dep(S.VDEP0_NOM, q['W4'], q['ncw']))
    a_pot = L.dvw_pot(S.VTR0_NOM, q['W1'], q['L1'], q['ncw'])
    sd = abs(L.suelo_dep(q['W4'], q['ncw']))
    sp = abs(L.suelo_pot(q['W1'], q['ncw']))
    return dict(A_dep=a_dep, A_pot=a_pot,
                tau=L.tau(q['itd'], q['ncdep']),
                suelo_d=sd, suelo_p=sp if sp > 1e-9 else 0.0,
                senal_suelo=a_dep / sd)


SAL = ['A_dep', 'A_pot', 'tau', 'suelo_d', 'suelo_p', 'senal_suelo']
CAB = {'A_dep': 'A-', 'A_pot': 'A+', 'tau': 'tau', 'suelo_d': 'suelo-',
       'suelo_p': 'suelo+', 'senal_suelo': 'S/ruido'}

print('  d(ln salida)/d(ln perilla) en el punto nominal')
print('  +1 = proporcional   ~0 = ORTOGONAL   -1 = inversa\n')
print('  %-8s' % 'perilla' + ''.join('%10s' % CAB[s] for s in SAL))
for nom, k in (('W4', 'W4'), ('W1', 'W1'), ('CW', 'ncw'),
               ('Cdep', 'ncdep'), ('Itd', 'itd')):
    v = NOM[k]
    d = 1.02
    hi, lo = sal({k: v * d}), sal({k: v / d})
    fila = '  %-8s' % nom
    for s in SAL:
        if lo[s] <= 0 or hi[s] <= 0:
            fila += '%10s' % '-'
            continue
        e = (np.log(hi[s]) - np.log(lo[s])) / (2 * np.log(d))
        fila += '%10s' % ('~0' if abs(e) < 0.02 else '%+.2f' % e)
    print(fila)

print()
print('  Las que NO son continuas, y por eso no salen arriba:')
print('    L1     DISCRETA (0.40 / 0.80 / 2.00). A+ cae 2.4x de 0.40 a 0.80')
print('           y otro 2.6x hasta 2.00; el suelo+ NO la nota (4 cifras)')
print('    L(M3)  solo mueve el suelo-, y lo CRUZA POR CERO. Es la unica')
print('           palanca sobre el termino no hebbiano de la depresion')
print('    M9     fija el techo n5, o sea el maximo de Vdep0: 0.568 a 0.879 V')
print('    M12    solo la VELOCIDAD de llegar al techo: 83.8 a 96.4 pct en 33 ns')
print('    M5     el rango de Iout Y la parasita de vw (27 fF de sus 7.5 um2)')
