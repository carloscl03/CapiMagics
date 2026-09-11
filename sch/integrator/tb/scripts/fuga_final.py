"""La fuga, version final: L1 fijo en 0.28 -> 4 variables, no 5."""
import itertools
import numpy as np

D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
msk = C[:, 1] == 0.28
X, Y, G = [], [], []
for j in np.where(msk)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(g)[0]:
        X.append([np.log10(W1), np.log10(W2), np.log10(L2), V[k]])
        Y.append(np.log10(y[k])); G.append(j)
X = np.array(X); Y = np.array(Y); G = np.array(G)

def kf(grado, nf=20):
    E = [e for e in itertools.product(range(grado+1), repeat=4) if sum(e) <= grado]
    B = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
    gs = np.array(sorted(set(G))); rng = np.random.default_rng(3)
    er, pg = [], []
    for f in np.array_split(rng.permutation(gs), nf):
        m = np.isin(G, f)
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
        for g in f:
            q = G == g
            if q.sum(): pg.append((100*np.abs(10**(B[q]@c - Y[q]) - 1)).mean())
    e = np.concatenate(er)
    return E, B, B.shape[1], e.mean(), np.percentile(e, 90), max(pg)

print('=== la fuga con L1 = 0.28 fijo: 4 variables ===')
print('  (a = lg10 W1, b = lg10 W2, c = lg10 L2, vm)')
print()
print('  %-12s %5s %10s %8s %11s' % ('forma', 'coef', 'K-fold', 'p90', 'peor geom'))
mejor = None
for gr in (2, 3, 4):
    E, B, n, m_, p, w = kf(gr)
    print('  %-12s %5d %9.2f%% %7.1f%% %10.1f%%' % ('grado %d' % gr, n, m_, p, w))
    if mejor is None or w < mejor[5]:
        mejor = (gr, E, B, n, m_, w)
gr, E, B, n, m_, w = mejor
c = np.linalg.lstsq(B, Y, rcond=None)[0]
np.save('cf_final.npy', c)
np.save('cf_final_exp.npy', np.array(E))
print()
print('  elegida: grado %d, %d coeficientes, %.2f%% K-fold, %.1f%% peor geometria' % (gr, n, m_, w))
print('  %d geometrias, %d puntos' % (len(set(G)), len(Y)))
print()
print('  CAJA:  W1 %s' % sorted(set(C[msk][:, 0])))
print('         L1 = 0.28 (FIJO)')
print('         W2 %s' % sorted(set(C[msk][:, 2])))
print('         L2 %s' % sorted(set(C[msk][:, 3])))
print('         Iref %s nA' % sorted(set(np.round(C[msk][:, 4]*1e9, 1))))
print('         vm 1.00-2.45 V,  valida donde I_fuga > 0.30*Iref')
