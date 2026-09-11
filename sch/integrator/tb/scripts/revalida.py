"""Revalidacion con el balance bien calculado. NO se rehace el barrido:
vm, rizado e I_fuga no dependen de como integre; solo cambiaba el test.
"""
import sys, time
import numpy as np
import banco

R = list(np.load('barrido_banda3.npy', allow_pickle=True))
pend = [i for i, r in enumerate(R)
        if r['f'] >= 300 and not r['sat'] and abs(r['bal']) > 1.5]
print('=== revalidando %d puntos con integral con signo ===' % len(pend))
sys.stdout.flush()
t0 = time.time()
for f in sorted(set(R[i]['f'] for i in pend)):
    idx = [i for i in pend if R[i]['f'] == f]
    out = []
    for k in range(0, len(idx), 20):
        sub = idx[k:k+20]
        out += banco.mide([(R[i]['g'], f) for i in sub], nset=12, nmed=8,
                          tag='rv_%d_%d' % (f, k), vic=[R[i]['vm'] for i in sub])
    for i, o in zip(idx, out):
        R[i] = dict(g=R[i]['g'], f=f, sat=False, **o)
    ok = sum(1 for i in idx if abs(R[i]['bal']) <= 1.5)
    print('   %5d kHz  %3d/%d recuperados' % (f, ok, len(idx)))
    sys.stdout.flush()
    np.save('barrido_final.npy', np.array(R, dtype=object))

np.save('barrido_final.npy', np.array(R, dtype=object))
print()
print('=== estado final (%.0f min) ===' % ((time.time()-t0)/60))
print('  %7s %8s %10s %10s %11s' % ('f[kHz]', 'buenos', 'saturados', 'dudosos', 'rizado med'))
tot = [0, 0, 0]
for f in sorted(set(r['f'] for r in R)):
    s = [r for r in R if r['f'] == f]
    ok = [r for r in s if not r['sat'] and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]
    st = [r for r in s if r['sat']]
    du = len(s) - len(ok) - len(st)
    tot[0] += len(ok); tot[1] += len(st); tot[2] += du
    print('  %7d %8d %10d %10d %10.1fmV'
          % (f, len(ok), len(st), du, np.median([r['riz'] for r in ok]) if ok else np.nan))
print('  %7s %8d %10d %10d' % ('TOTAL', *tot))
