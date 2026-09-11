"""Revalidar tambien 74 y 150 kHz: su balance seguia con la integral vieja."""
import sys, time
import numpy as np
import banco

R = list(np.load('barrido_final.npy', allow_pickle=True))
pend = [i for i, r in enumerate(R)
        if r['f'] < 300 and not r.get('sat') and abs(r['bal']) > 1.5]
print('=== revalidando %d puntos de baja frecuencia ===' % len(pend)); sys.stdout.flush()
t0 = time.time()
for f in sorted(set(R[i]['f'] for i in pend)):
    idx = [i for i in pend if R[i]['f'] == f]
    out = []
    for k in range(0, len(idx), 20):
        sub = idx[k:k+20]
        out += banco.mide([(R[i]['g'], f) for i in sub], nset=12, nmed=8,
                          tag='rb_%d_%d' % (f, k), vic=[R[i]['vm'] for i in sub])
    for i, o in zip(idx, out):
        R[i] = dict(g=R[i]['g'], f=f, sat=False, **o)
    print('   %5d kHz  %3d/%d recuperados'
          % (f, sum(1 for i in idx if abs(R[i]['bal']) <= 1.5), len(idx)))
    sys.stdout.flush()
    np.save('barrido_final.npy', np.array(R, dtype=object))
np.save('barrido_final.npy', np.array(R, dtype=object))
b = sum(1 for r in R if not r.get('sat') and abs(r['bal']) <= 1.5)
s = sum(1 for r in R if r.get('sat'))
print()
print('=== TOTAL: %d buenos, %d saturados, %d dudosos  (%.0f min) ==='
      % (b, s, len(R) - b - s, (time.time() - t0) / 60))
