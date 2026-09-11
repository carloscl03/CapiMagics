"""Primer analisis de los 470 puntos. Metodo del encoder y el integrador:
mirar los DATOS antes de proponer forma, y validar POR GEOMETRIA.
"""
import os
import sys

import numpy as np

os.chdir('/tmp/stdp')
CU = 54.5e-15


def carga(n):
    try:
        return np.load(n)['filas']
    except Exception as e:
        print('  (%s: %s)' % (n, e))
        return None


def sep(t):
    print('\n' + '=' * 72)
    print(t)
    print('=' * 72)


# ---------------------------------------------------------------- L2 -------
sep('L2 / L2p -- el decaimiento:  pendiente = I/C ?')
for lado in ('dep', 'pot'):
    A = carga('L2_%s.npz' % lado)
    if A is None:
        continue
    vb, nc, ii, med, esp = A.T
    r = med / esp
    print('  %s : %2d puntos | cociente medida/esperada  mediana %.4f  '
          'dispersion %.4f  peor %.4f'
          % (lado, len(A), np.median(r), r.std(), np.abs(r - 1).max()))
    print('       I recorre %.3g - %.3g nA sobre %d valores de C'
          % (ii.min() * 1e9, ii.max() * 1e9, len(set(nc))))
    k = int(np.argmax(np.abs(r - 1)))
    print('       peor punto: vb %.3f  nC %d  I %.4f nA  '
          'medida %.4g  esperada %.4g  -> %+.1f %%'
          % (vb[k], nc[k], ii[k] * 1e9, med[k], esp[k],
             100 * (r[k] - 1)))

# ---------------------------------------------------------------- L1 -------
sep('L1 / L1p -- la amplitud:  satura con Dtp?  colapsa con Q/C?')
for lado in ('dep', 'pot'):
    A = carga('L1_%s.npz' % lado)
    if A is None:
        continue
    vb, dtp, nc, ii, qq, pred, v0 = A.T
    ok = v0 > 1e-3
    bal = (pred[ok] - v0[ok]) / v0[ok]
    print('  %s : %3d puntos | balance de carga Q/C vs V0:  mediana %+.2f %%  '
          'p95 %+.2f %%' % (lado, len(A), 100 * np.median(bal),
                            100 * np.percentile(np.abs(bal), 95)))
    print('       V0 recorre %.4f - %.4f V ; I  %.3g - %.3g uA'
          % (v0.min(), v0.max(), ii.min() * 1e6, ii.max() * 1e6))
    # saturacion: cuanto sube V0 de Dtp=100ns a 200ns, a igual vb y nc
    d = {}
    for row in A:
        d[(row[0], row[2], row[1])] = row[6]
    subs = []
    for (b, c, t), v in d.items():
        if abs(t - 100e-9) < 1e-12 and (b, c, 200e-9) in d:
            v2 = d[(b, c, 200e-9)]
            if v > 1e-3:
                subs.append(v2 / v)
    if subs:
        print('       V0(200ns)/V0(100ns):  mediana %.4f  -> %s'
              % (np.median(subs),
                 'SATURADA' if np.median(subs) < 1.05 else 'aun creciendo'))

# ---------------------------------------------------------------- L3 -------
sep('L3 / L3p -- el nucleo:  suelo + exponencial')
for lado in ('dep', 'pot'):
    A = carga('L3_%s.npz' % lado)
    if A is None:
        continue
    v, ncw, ip, dvw, sen = A.T
    print('  %s : %3d puntos' % (lado, len(A)))
    for c in sorted(set(ncw)):
        m = ncw == c
        suelo = dvw[m][0]
        print('     nCW %2d (%6.1f fF) : suelo %9.4f mV   max |senal| %10.4f mV'
              % (c, c * CU * 1e15, suelo * 1e3, np.abs(sen[m]).max() * 1e3))
    # el suelo escala como 1/CW?
    su = np.array([dvw[ncw == c][0] for c in sorted(set(ncw))])
    cc = np.array(sorted(set(ncw)))
    print('     suelo * nCW  =', np.round(su * cc * 1e3, 4),
          ' -> constante?' if su[0] != 0 else '')
    # pendiente subumbral: e-plegado en mV de traza
    for c in sorted(set(ncw))[:1]:
        m = (ncw == c) & (np.abs(sen) > 5e-3) & (np.abs(sen) < 0.5)
        if m.sum() >= 3:
            k = np.polyfit(v[m], np.log(np.abs(sen[m])), 1)[0]
            print('     e-plegado subumbral: %.1f mV de traza  (%d puntos)'
                  % (1000 / abs(k), m.sum()))

# ------------------------------------------------------- simetria -----------
sep('SIMETRIA -- las dos mitades hacen lo mismo?')
for nom, col in (('L2', 3), ('L3', 4)):
    a = carga('%s_dep.npz' % nom)
    b = carga('%s_pot.npz' % nom)
    if a is None or b is None:
        continue
    print('  %s : |max senal|  dep %10.4g   pot %10.4g   cociente %.3f'
          % (nom, np.abs(a[:, col]).max(), np.abs(b[:, col]).max(),
             np.abs(b[:, col]).max() / np.abs(a[:, col]).max()))
