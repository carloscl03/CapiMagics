"""La fuga, rehecha con Iref CRUZADO de verdad.

La ley vieja (56 terminos, 2.08 % en su malla) se ajusto sobre `fuga_bar.npz`,
que fija Iref=50 nA en la malla principal y solo lo mueve sobre UNA linea de
geometria: 12 puntos de 93. `Iref` estaba casi confundido, y por eso falla hasta
12 % en L2=0.28 con Iref lejos de 50, que es la esquina donde opera el barrido
de banda. Discrepa un 6.4 % de la medida con amperimetro.

`criba.npz` cruza las cinco variables entero: 4x4x4x4x6 = 1536 geometrias x 63
valores de vm, con amperimetro y en DC (el A/B demostro que C3 y M6 no cambian
nada: 0.00 %).

Validacion por GRUPOS DE GEOMETRIA (20 folds), no por punto.
"""
import itertools, sys, time
import numpy as np

D = np.load('criba.npz'); V = D['v']; I = D['I']; C = D['casos']
print('=== %d geometrias x %d valores de vm ===' % (I.shape[1], len(V)))
print('   vm de %.2f a %.2f;  Iref de %.0f a %.0f nA'
      % (V.min(), V.max(), C[:,4].min()*1e9, C[:,4].max()*1e9))

def arma(mask_geo, vmin=1.0, vmax=2.45, rmin=0.30):
    X, Y, G = [], [], []
    for j in np.where(mask_geo)[0]:
        W1, L1, W2, L2, Ir = C[j]
        y = I[:, j] / Ir
        m = (V >= vmin) & (V <= vmax) & (y > rmin) & np.isfinite(y)
        for k in np.where(m)[0]:
            X.append([np.log10(W1), np.log10(L1), np.log10(W2), np.log10(L2), V[k]])
            Y.append(np.log10(y[k])); G.append(j)
    return np.array(X), np.array(Y), np.array(G)

def kfold(X, Y, G, grado, nf=20):
    E = [e for e in itertools.product(range(grado+1), repeat=5) if sum(e) <= grado]
    B = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
    gs = np.array(sorted(set(G))); rng = np.random.default_rng(3)
    gp = rng.permutation(gs); folds = np.array_split(gp, nf)
    er, pg = [], []
    for fo in folds:
        m = np.isin(G, fo)
        if m.all() or B.shape[1] >= (~m).sum(): return None
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        e = 100*np.abs(10**(B[m]@c - Y[m]) - 1)
        er.append(e)
        for g in fo:
            mg = G == g
            if mg.sum(): pg.append((100*np.abs(10**(B[mg]@c - Y[mg]) - 1)).mean())
    e = np.concatenate(er)
    return B.shape[1], e.mean(), np.percentile(e, 90), max(pg)

TODO = np.ones(len(C), bool)
ESP = np.array([0.9 < I[int(np.argmin(np.abs(V-1.5))), j]/C[j,4] < 1.15 for j in range(len(C))])
UTIL = ESP & (C[:,3] >= 0.9) & (C[:,4] <= 1.05e-7) & (C[:,1] <= 1.05)

print()
print('=== competencia de familias, validacion por grupos de geometria ===')
print('  %-30s %6s %5s %4s %9s %8s %10s'
      % ('region / forma', 'ptos', 'geom', 'coef', 'K-fold', 'p90', 'peor geom'))
sys.stdout.flush()
for nm, mask in (('todo el cribado', TODO), ('solo las que espejan', ESP),
                 ('region util', UTIL)):
    X, Y, G = arma(mask)
    if len(Y) < 500:
        print('  %-30s %6d  pocos datos' % (nm, len(Y))); continue
    for gr in (2, 3):
        r = kfold(X, Y, G, gr)
        if r is None: continue
        print('  %-30s %6d %5d %4d %8.2f%% %7.1f%% %9.1f%%'
              % ('%s, grado %d' % (nm, gr), len(Y), len(set(G)), r[0], r[1], r[2], r[3]))
        sys.stdout.flush()

# --- la ley vieja, evaluada sobre estos datos ------------------------------
print()
print('=== la ley VIEJA (leyes.npz) contra el cribado nuevo ===')
cf = np.load('leyes.npz')['cf']
def base_v(Z, g, nv):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g+1), repeat=nv):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k: t = t*Z[:, j]**k
            cols.append(t)
    return np.column_stack(cols)
for nm, mask in (('todo el cribado', TODO), ('region util', UTIL)):
    X, Y, G = arma(mask)
    e = 100*np.abs(10**(base_v(X, 3, 5)@cf - Y) - 1)
    print('  %-24s  medio %6.2f%%   p90 %6.1f%%   peor %7.1f%%'
          % (nm, e.mean(), np.percentile(e, 90), e.max()))
