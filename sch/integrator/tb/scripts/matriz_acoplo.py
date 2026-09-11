"""Matriz de acoplo del INTEGRADOR, calculada de las leyes.

Siete perillas (W1, W2, L2, Iref, W6, L6, C) contra las salidas que el motor
reporta. Lo que se busca es lo mismo que en el STDP: perillas que yo trate como
palanca de calidad y que en realidad muevan numerador y denominador por igual.

El punto nominal sale de pedirle al motor un diseno tipico.
"""
import sys

import numpy as np

sys.path.insert(0, 'designs/scripts')
from integrator_design import IntegratorSpec, design
from integrator_design import laws as L

d0 = design(IntegratorSpec(f_min=74.0, f_max=4500.0))
P = d0.params
NOM = dict(W1=P['W1'], W2=P['W2'], L2=P['L2'], Iref=P['Iref'] * 1e-9,
           W6=P['W6'], L6=P['L6'], C=P['C'])
F_LO, F_HI = 74.0, 4500.0
print('  punto nominal del motor: ' +
      '  '.join('%s=%.4g' % (k, v) for k, v in NOM.items()))
print()


def sal(p):
    q = dict(NOM)
    q.update(p)
    a = (q['W1'], q['W2'], q['L2'], q['Iref'])
    b = (q['W6'], q['L6'], q['C'])
    vm = L.vm_equilibrio(*a, *b, F_LO)
    return dict(
        res=L.resolucion(*a, *b, F_LO, F_HI),
        sens=L.sensibilidad(*a, *b, F_LO, F_HI),
        riz=L.rizado(vm, *a, q['C'], F_LO),
        techo=L.techo(q['W6'], q['L6']),
        c_in=L.c_in(q['W6'], q['L6']),
        r_out=L.r_out(vm, *a),
        t_resp=L.t_respuesta(vm, *a, q['C']),
        vm=vm)


SAL = ['res', 'sens', 'riz', 'techo', 'c_in', 'r_out', 't_resp', 'vm']
CAB = {'res': 'resol', 'sens': 'sensib', 'riz': 'rizado', 'techo': 'techo',
       'c_in': 'C_in', 'r_out': 'R_out', 't_resp': 't_resp', 'vm': 'vm'}

base = sal({})
print('  INTEGRADOR -- d(ln salida)/d(ln perilla)')
print('  +1 proporcional   ~0 ORTOGONAL   -1 inversa\n')
print('  %-6s' % 'dim' + ''.join('%9s' % CAB[s] for s in SAL))
for k in ('W1', 'W2', 'L2', 'Iref', 'W6', 'L6', 'C'):
    v = NOM[k]
    dd = 1.02
    try:
        hi, lo = sal({k: v * dd}), sal({k: v / dd})
    except Exception as e:
        print('  %-6s  (%s)' % (k, str(e)[:50]))
        continue
    fila = '  %-6s' % k
    for s in SAL:
        if lo[s] <= 0 or hi[s] <= 0:
            fila += '%9s' % '-'
            continue
        e = (np.log(hi[s]) - np.log(lo[s])) / (2 * np.log(dd))
        fila += '%9s' % ('~0' if abs(e) < 0.02 else '%+.2f' % e)
    print(fila)
print()
print('  valores en el nominal:')
for s in SAL:
    print('    %-8s %12.4g' % (CAB[s], base[s]))
