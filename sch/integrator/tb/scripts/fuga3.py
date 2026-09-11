"""La fuga sobre el cribado ampliado, y si W1/L1 se pueden fijar.

COBERTURA, como en el encoder: fijar una dimension se decide midiendo cuanto
espacio alcanzable se pierde, no por opinion. Aqui el espacio que importa es
(A, B) de  I_fuga/Iref = A + B*vm : el nivel y la pendiente, que son lo que el
integrador ve.
"""
import itertools, sys
import numpy as np

D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
print('=== %d geometrias x %d vm ===' % (I.shape[1], len(V)))

# --- rasgos (A, B) por geometria ------------------------------------------
m = (V >= 1.0) & (V <= 2.45)
A = np.full(len(C), np.nan); Bs = np.full(len(C), np.nan)
for j in range(len(C)):
    y = I[m, j]/C[j, 4]
    g = np.isfinite(y) & (y > 0.30)
    if g.sum() > 10:
        p = np.polyfit(V[m][g], y[g], 1); Bs[j] = p[0]; A[j] = p[1]
ok = np.isfinite(A)
print('   %d geometrias con rasgos validos' % ok.sum())

def cobertura(mask):
    s = ok & mask
    if s.sum() < 10: return None
    return A[s].min(), A[s].max(), Bs[s].min(), Bs[s].max(), s.sum()

print()
print('=== cobertura de (A, B): que se pierde al fijar W1 y L1? ===')
print('  %-28s %6s %14s %14s' % ('conjunto', 'geom', 'A', 'B'))
tot = cobertura(np.ones(len(C), bool))
print('  %-28s %6d [%5.2f %5.2f] [%5.2f %5.2f]' % ('todas', tot[4], tot[0], tot[1], tot[2], tot[3]))
for nm, msk in (('L1 = 0.28', C[:,1] == 0.28),
                ('L1 = 0.28 y W1 = 1.0', (C[:,1] == 0.28) & (C[:,0] == 1.0)),
                ('L1 = 0.28, W1 en {1,2}', (C[:,1] == 0.28) & np.isin(C[:,0], [1.0, 2.0]))):
    r = cobertura(msk)
    if r is None: continue
    fa = 100*(r[1]-r[0])/(tot[1]-tot[0]); fb = 100*(r[3]-r[2])/(tot[3]-tot[2])
    print('  %-28s %6d [%5.2f %5.2f] [%5.2f %5.2f]   cubre %.0f%% de A, %.0f%% de B'
          % (nm, r[4], r[0], r[1], r[2], r[3], fa, fb))

# --- la ley, con L2 corto DENTRO ------------------------------------------
def arma(mask):
    X, Y, G = [], [], []
    for j in np.where(mask & ok)[0]:
        W1, L1, W2, L2, Ir = C[j]
        y = I[:, j]/Ir
        g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
        for k in np.where(g)[0]:
            X.append([np.log10(W1), np.log10(L1), np.log10(W2), np.log10(L2), V[k]])
            Y.append(np.log10(y[k])); G.append(j)
    return np.array(X), np.array(Y), np.array(G)

def kfold(X, Y, G, grado, nv=5, nf=20):
    E = [e for e in itertools.product(range(grado+1), repeat=nv) if sum(e) <= grado]
    B_ = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
    gs = np.array(sorted(set(G))); rng = np.random.default_rng(3)
    fo = np.array_split(rng.permutation(gs), nf)
    er, pg = [], []
    for f in fo:
        mm = np.isin(G, f)
        c = np.linalg.lstsq(B_[~mm], Y[~mm], rcond=None)[0]
        er.append(100*np.abs(10**(B_[mm]@c - Y[mm]) - 1))
        for g in f:
            q = G == g
            if q.sum(): pg.append((100*np.abs(10**(B_[q]@c - Y[q]) - 1)).mean())
    e = np.concatenate(er)
    return B_.shape[1], e.mean(), np.percentile(e, 90), max(pg)

print()
print('=== la ley, con L2 corto INCLUIDO ===')
print('  %-34s %6s %5s %4s %9s %8s %10s'
      % ('conjunto / grado', 'ptos', 'geom', 'coef', 'K-fold', 'p90', 'peor geom'))
for nm, msk in (('todo el cribado ampliado', np.ones(len(C), bool)),
                ('L1 = 0.28 (fijado)', C[:,1] == 0.28)):
    X, Y, G = arma(msk)
    for gr in (2, 3):
        r = kfold(X, Y, G, gr)
        print('  %-34s %6d %5d %4d %8.2f%% %7.1f%% %9.1f%%'
              % ('%s, g%d' % (nm, gr), len(Y), len(set(G)), r[0], r[1], r[2], r[3]))
        sys.stdout.flush()
