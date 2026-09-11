"""Igual que forma3, pero ajustando EN LOG, que es lo que dice el metodo.

El intento anterior usaba minimos cuadrados en espacio lineal sobre una curva
que recorre tres decadas: los puntos de 1276 mV se comian todo el peso y los de
2.9 mV no existian para el ajuste. Salia 95 % de error y suelo = 0.

Aqui el suelo va por rejilla y la exponencial se ajusta en log, donde el
residuo ES el error relativo.
"""
import os

import numpy as np

os.chdir('/tmp/stdp')


def ajusta(v, y, con_suelo=True, con_lineal=False):
    """y = suelo + A*exp(v/e)  [+ B*v].  Rejilla en suelo, lineal en log."""
    mejor = None
    suelos = (np.linspace(-8e-3, 2e-3, 401) if con_suelo else [0.0])
    for s in suelos:
        d = y - s
        if np.any(np.sign(d) != np.sign(d[-1])) or np.any(np.abs(d) < 1e-12):
            continue                      # el suelo no puede cruzar los datos
        ld = np.log(np.abs(d))
        base = [v, np.ones_like(v)]
        if con_lineal:
            base.append(v ** 2)           # curvatura en log = termino extra
        M = np.vstack(base).T
        c, *_ = np.linalg.lstsq(M, ld, rcond=None)
        pred = s + np.sign(d[-1]) * np.exp(M @ c)
        rel = np.abs(pred - y) / np.maximum(np.abs(y), 1e-9)
        sc = float(np.sqrt(np.mean(rel ** 2)))
        if mejor is None or sc < mejor[0]:
            mejor = (sc, s, 1000.0 / abs(c[0]), c, pred)
    return mejor


A = np.load('L3_dep.npz')['filas']
print('  error RELATIVO medio, ajustando en log\n')
print('  %5s %14s %14s %14s %12s %12s'
      % ('nCW', '3 param [%]', '2 param [%]', '4 param [%]',
         'suelo aj[mV]', 'suelo med'))
for c in sorted(set(A[:, 1])):
    m = A[:, 1] == c
    v, y = A[m, 0], A[m, 3]
    o = np.argsort(v)
    v, y = v[o], y[o]
    r3 = ajusta(v, y, True, False)
    r2 = ajusta(v, y, False, False)
    r4 = ajusta(v, y, True, True)
    print('  %5d %14.2f %14.2f %14.2f %12.4f %12.4f'
          % (c, 100 * r3[0], 100 * r2[0], 100 * r4[0], r3[1] * 1e3, y[0] * 1e3))

print()
print('  --- residuo punto a punto, 3 parametros, nCW=10 ---')
m = A[:, 1] == 10
v, y = A[m, 0], A[m, 3]
o = np.argsort(v)
v, y = v[o], y[o]
sc, s, ef, c, pred = ajusta(v, y)
print('  suelo %.4f mV   e-plegado %.1f mV   error medio %.2f %%'
      % (s * 1e3, ef, 100 * sc))
print('  %8s %14s %14s %10s' % ('Vdep', 'medido[mV]', 'ajuste[mV]', 'err[%]'))
for a, b, p in zip(v, y, pred):
    print('  %8.2f %14.4f %14.4f %10.1f'
          % (a, b * 1e3, p * 1e3, 100 * (p - b) / abs(b)))
