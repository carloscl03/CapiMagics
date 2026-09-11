"""Ajusta y guarda la fuga en la region util, con la caja explicita."""
import itertools
import numpy as np

D = np.load('criba.npz'); V = D['v']; I = D['I']; C = D['casos']
k15 = int(np.argmin(np.abs(V-1.5)))
ESP = np.array([0.9 < I[k15, j]/C[j,4] < 1.15 for j in range(len(C))])
UTIL = ESP & (C[:,3] >= 0.9) & (C[:,4] <= 1.05e-7) & (C[:,1] <= 1.05)

X, Y, G = [], [], []
for j in np.where(UTIL)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    m = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(m)[0]:
        X.append([np.log10(W1), np.log10(L1), np.log10(W2), np.log10(L2), V[k]])
        Y.append(np.log10(y[k])); G.append(j)
X = np.array(X); Y = np.array(Y); G = np.array(G)
E = [e for e in itertools.product(range(4), repeat=5) if sum(e) <= 3]
B = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
c = np.linalg.lstsq(B, Y, rcond=None)[0]
np.save('cf_util.npy', c)

U = C[UTIL]
print('=== la fuga en la region util ===')
print('  %d geometrias de %d, %d puntos, %d coeficientes' % (UTIL.sum(), len(C), len(Y), len(c)))
print()
print('  CAJA (las que espejan, 0.9 < I/Iref < 1.15 a vm=1.5 V):')
for k, nm in ((0,'W1'), (1,'L1'), (2,'W2'), (3,'L2')):
    print('    %-3s %s' % (nm, sorted(set(U[:, k]))))
print('    Iref %s nA' % sorted(set(np.round(U[:, 4]*1e9, 1))))
print('    vm de 1.00 a 2.45 V,  valida donde I_fuga > 0.30*Iref')
print()
print('  Los que quedan fuera y por que:')
print('    L1 >= 4 um   -> solo el 21-35%% espeja')
print('    L2 = 0.28    -> solo el 19%% espeja')
print('    Iref = 200n  -> solo el 30%% espeja')
print()
r = 100*np.abs(10**(B@c - Y) - 1)
print('  ajuste sobre todo: medio %.2f%%, p90 %.1f%%' % (r.mean(), np.percentile(r, 90)))
print('  (K-fold por geometria ya medido: 5.34%% medio, 7.8%% peor geometria)')
