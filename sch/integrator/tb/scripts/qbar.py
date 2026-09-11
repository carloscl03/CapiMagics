"""De que depende q = rizado*C*f/I_fuga?

En el barrido de banda valia 1.00 +- 0.07 sobre 344 puntos. En las geometrias
que el solver elige vale 1.7 a 7.7. Algo lo mueve y no se que.

Diferencias conocidas entre los dos conjuntos:
    barrido de banda   W1=1.0  W2=1.0  Iref 12-100 nA  L2 0.28-2
    lo que elige       W1=4.0  W2=1-4  Iref 5-100 nA   L2 0.28 y 2

Se barre justo eso, con todo medido por amperimetro y el asentamiento validado.
"""
import itertools, sys, time
import numpy as np
import banco

W1S = [1.0, 4.0]
W2S = [1.0, 4.0]
L2S = [0.28, 2.0]
IRS = [5e-9, 25e-9, 100e-9]
CS  = [5111.0, 12000.0]
FS  = [300, 1200, 4500]
GEOS = [(w1, 0.28, w2, l2, ir, 0.26, 2.0, c)
        for w1, w2, l2, ir, c in itertools.product(W1S, W2S, L2S, IRS, CS)]
print('=== %d geometrias x %d frecuencias ===' % (len(GEOS), len(FS)))
sys.stdout.flush()

R = []
for f in FS:
    t0 = time.time()
    out = banco.mide([(g, f) for g in GEOS], nset=12, nmed=8, tag='q%d' % f)
    for _ in range(2):
        mal = [i for i, r in enumerate(out) if not np.isfinite(r['vm']) or abs(r['bal']) > 1.5]
        if not mal: break
        re = banco.mide([(GEOS[i], f) for i in mal], nset=20, nmed=8,
                        tag='qr%d' % f, vic=[out[i]['vm'] for i in mal])
        for i, r in zip(mal, re): out[i] = r
    for g, r in zip(GEOS, out):
        if np.isfinite(r['vm']) and abs(r['bal']) <= 1.5 and r['ifuga'] > 0:
            q = r['riz']*1e-3 * g[7]*1e-15 * f*1e3 / (r['ifuga']*1e-9)
            R.append(dict(g=g, f=f, q=q, **r))
    print('  %5d kHz  %2d/%d validos  %3.0f s' % (f, sum(1 for r in R if r['f'] == f), len(GEOS), time.time()-t0))
    sys.stdout.flush()
np.save('qbar.npy', np.array(R, dtype=object))

print()
print('=== de que depende q? ===')
for nm, k in (('W1', 0), ('W2', 2), ('L2', 3), ('Iref', 4), ('C', 7)):
    print('  %-5s' % nm, end='')
    for v in sorted({r['g'][k] for r in R}):
        s = [r['q'] for r in R if r['g'][k] == v]
        et = ('%.0fn' % (v*1e9)) if nm == 'Iref' else ('%g' % v)
        print('   %s: %.2f (n=%d)' % (et, np.median(s), len(s)), end='')
    print()
print('  f    ', end='')
for f in FS:
    s = [r['q'] for r in R if r['f'] == f]
    if s: print('   %d: %.2f (n=%d)' % (f, np.median(s), len(s)), end='')
print()
print()
qs = [r['q'] for r in R]
print('  q global: mediana %.2f, p10 %.2f, p90 %.2f' %
      (np.median(qs), np.percentile(qs, 10), np.percentile(qs, 90)))
print()
print('  === los que mas se desvian ===')
R.sort(key=lambda r: -abs(np.log(r['q'])))
print('  %6s %6s %6s %7s %8s %7s %9s %9s' % ('W1','W2','L2','Iref','C','f','I_fuga','q'))
for r in R[:6]:
    g = r['g']
    print('  %6.1f %6.1f %6.2f %6.0fn %8.0f %6d %8.2fnA %8.2f'
          % (g[0], g[2], g[3], g[4]*1e9, g[7], r['f'], r['ifuga'], r['q']))
