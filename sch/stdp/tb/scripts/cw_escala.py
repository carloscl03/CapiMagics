"""Entra CW como simple divisor?  DVw = Q(Vdep,W4) / CW ?

Las dos leyes del nucleo estan ajustadas a nCW=10 FIJO. Si CW solo divide,
la ley vale para cualquier CW sin remedir. Si no, falta una variable.

Test: senal * nCW tiene que ser CONSTANTE a igual Vdep.
"""
import numpy as np

for lado, col in (('dep', 4), ('pot', 4)):
    A = np.load('/tmp/stdp/L3_%s.npz' % lado)['filas']
    CW = sorted(set(A[:, 1]))
    print('\n  === %s ===' % lado.upper())
    print('  %8s' % 'Vdep' + ''.join('%12s' % ('nCW=%d' % c) for c in CW)
          + '%12s %10s' % ('senal*nCW', 'disp'))
    for v in sorted(set(A[:, 0])):
        fila, prod = [], []
        for c in CW:
            m = (np.abs(A[:, 0] - v) < 1e-9) & (A[:, 1] == c)
            if m.sum() == 0:
                fila.append(np.nan); continue
            s = abs(A[m, col][0])
            fila.append(s * 1e3)
            if s > 5e-5:                      # solo donde hay senal de verdad
                prod.append(s * c)
        if not prod or np.isnan(fila).any():
            continue
        d = 100 * (max(prod) - min(prod)) / np.mean(prod)
        print('  %8.2f' % v + ''.join('%12.3f' % x for x in fila)
              + '%12.4f %9.1f %%' % (np.mean(prod) * 1e3, d))
