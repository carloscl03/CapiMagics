"""Competencia de familias COMPLETA para la fuga, mas las dos herramientas
que no habia usado en el integrador: curva de aprendizaje y separabilidad.
"""
import itertools
import numpy as np

D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
msk = C[:, 1] == 0.28
GJ = np.where(msk)[0]
X, Y, G = [], [], []
for j in GJ:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(g)[0]:
        X.append([np.log10(W1), np.log10(W2), np.log10(L2), V[k]])
        Y.append(np.log10(y[k])); G.append(j)
X = np.array(X); Y = np.array(Y); G = np.array(G)
gs = np.array(sorted(set(G)))

def kf(B, nf=20, seed=3):
    rng = np.random.default_rng(seed)
    er, pg = [], []
    for f in np.array_split(rng.permutation(gs), nf):
        m = np.isin(G, f)
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
        for g in f:
            q = G == g
            if q.sum(): pg.append((100*np.abs(10**(B[q]@c - Y[q]) - 1)).mean())
    return B.shape[1], np.concatenate(er).mean(), max(pg)

def poli(cols, grado):
    Z = X[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    return np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])

print('=== competencia de familias para la fuga ===')
print('  %-42s %5s %9s %11s' % ('familia', 'coef', 'K-fold', 'peor geom'))
for nm, B in (
    ('polinomio g2 (W1,W2,L2,vm)', poli([0,1,2,3], 2)),
    ('polinomio g3', poli([0,1,2,3], 3)),
    ('polinomio g4', poli([0,1,2,3], 4)),
):
    n, e, w = kf(B); print('  %-42s %5d %8.2f%% %10.1f%%' % (nm, n, e, w))

# familia A + B*vm con A,B polinomios en la geometria
for gr in (2, 3):
    Bg = poli([0,1,2], gr)
    B = np.column_stack([Bg, Bg*X[:, 3:4]])
    n, e, w = kf(B)
    print('  %-42s %5d %8.2f%% %10.1f%%' % ('A + B*vm, con A,B de grado %d' % gr, n, e, w))
# con vm cuadratico
Bg = poli([0,1,2], 2)
B = np.column_stack([Bg, Bg*X[:,3:4], Bg*X[:,3:4]**2])
n, e, w = kf(B); print('  %-42s %5d %8.2f%% %10.1f%%' % ('A + B*vm + D*vm^2, A..D grado 2', n, e, w))

# colapso: depende solo de W2/L2?
Zc = np.column_stack([X[:,0], X[:,1]-X[:,2], X[:,3]])
E = [e for e in itertools.product(range(4), repeat=3) if sum(e) <= 3]
B = np.column_stack([np.prod(Zc**np.array(e), axis=1) for e in E])
n, e, w = kf(B); print('  %-42s %5d %8.2f%% %10.1f%%' % ('COLAPSO: (W1, W2/L2, vm) g3', n, e, w))
Zc2 = np.column_stack([X[:,1]-X[:,2], X[:,3]])
E2 = [e for e in itertools.product(range(4), repeat=2) if sum(e) <= 3]
B = np.column_stack([np.prod(Zc2**np.array(e), axis=1) for e in E2])
n, e, w = kf(B); print('  %-42s %5d %8.2f%% %10.1f%%' % ('COLAPSO: solo (W2/L2, vm) g3', n, e, w))

# --- curva de aprendizaje --------------------------------------------------
print()
print('=== curva de aprendizaje (g3, 35 coef): falta dato o falta modelo? ===')
B = poli([0,1,2,3], 3)
rng = np.random.default_rng(5); gp = rng.permutation(gs)
te = np.isin(G, gp[:len(gs)//4])
for frac in (0.1, 0.25, 0.5, 0.75, 1.0):
    sub = gp[len(gs)//4:][:max(2, int(frac*0.75*len(gs)))]
    tr = np.isin(G, sub)
    c = np.linalg.lstsq(B[tr], Y[tr], rcond=None)[0]
    e = 100*np.abs(10**(B[te]@c - Y[te]) - 1)
    print('   %3d geometrias de entrenamiento -> %.2f%%' % (len(sub), e.mean()))

# --- separabilidad por doble centrado --------------------------------------
print()
print('=== separabilidad: es lg(I/Iref) = f(geom) + g(vm)? ===')
vs = np.unique(np.round(X[:, 3], 4))
M = np.full((len(gs), len(vs)), np.nan)
for a, g in enumerate(gs):
    q = G == g
    for b, v in enumerate(vs):
        r = q & (np.abs(X[:, 3]-v) < 1e-6)
        if r.sum(): M[a, b] = Y[r].mean()
ok = ~np.isnan(M).any(1)
Mo = M[ok]
Dc = Mo - Mo.mean(1, keepdims=True) - Mo.mean(0, keepdims=True) + Mo.mean()
s = np.linalg.svd(Dc, compute_uv=False)
print('   %d geometrias x %d vm; residuo tras doble centrado:' % (Mo.shape[0], Mo.shape[1]))
print('   norma del residuo / norma de la matriz centrada: %.3f'
      % (np.linalg.norm(Dc)/np.linalg.norm(Mo - Mo.mean())))
print('   primeros valores singulares: %s' % np.round(s[:4]/s[0], 3))
