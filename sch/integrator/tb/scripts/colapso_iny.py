"""Colapsa la inyeccion al reescalar por (techo - vm)?

Si si, la ley de 126 terminos se reduce mucho. Si no, se queda como esta -- pero
al menos ahora el techo esta bien medido y sirve de contrato de saturacion.

Validacion externa POR GEOMETRIA, como siempre.
"""
import itertools
import numpy as np

D = np.load('techo.npz')
G, V0, DV, TE = D['geos'], D['v0'], D['dv'], D['techo']

# --- 1. el techo depende solo de L6? ---------------------------------------
print('=== ley del techo ===')
X = np.log10(G); y = TE
for nm, cols in (('solo L6', [1]), ('L6 y W6', [0, 1]), ('las tres', [0, 1, 2])):
    Z = X[:, cols]
    B = np.column_stack([np.ones(len(y))] + [Z[:, k]**p for k in range(Z.shape[1])
                                             for p in (1, 2, 3)])
    c = np.linalg.lstsq(B, y, rcond=None)[0]
    e = 1000*np.abs(B@c - y)
    print('  %-10s %2d coef   error medio %.1f mV, peor %.1f mV' % (nm, B.shape[1], e.mean(), e.max()))

# --- 2. colapso de dV -------------------------------------------------------
P = []
for i in range(len(G)):
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.05 and v < TE[i] - 0.02:
            P.append([np.log10(G[i,0]), np.log10(G[i,1]), np.log10(G[i,2]),
                      v, np.log10(TE[i]-v), np.log10(d), i])
P = np.array(P)
print()
print('=== colapso de dV: %d puntos, %d geometrias ===' % (len(P), len(G)))
gid = P[:, 6].astype(int)
rng = np.random.default_rng(9); gg = rng.permutation(len(G))
trg = set(gg[:int(0.7*len(G))])
tr = np.array([g in trg for g in gid]); te = ~tr

def prueba(nm, cols, grado):
    Z = P[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    c = np.linalg.lstsq(B[tr], P[tr, 5], rcond=None)[0]
    r = 100*np.abs(10**(B[te]@c - P[te, 5]) - 1)
    print('  %-38s %4d coef %8.2f%%  peor %7.1f%%' % (nm, B.shape[1], r.mean(), np.percentile(r, 90)))

print('  %-38s %4s %9s %12s' % ('forma', 'coef', 'EXTERNO', 'p90'))
prueba('SIN colapsar: (W6,L6,C,vm) grado 3', [0,1,2,3], 3)
prueba('SIN colapsar: (W6,L6,C,vm) grado 5', [0,1,2,3], 5)
prueba('COLAPSADO: (W6,L6,C,lg(techo-vm)) g2', [0,1,2,4], 2)
prueba('COLAPSADO: (W6,L6,C,lg(techo-vm)) g3', [0,1,2,4], 3)
prueba('COLAPSADO: (W6,C,lg(techo-vm)) g3', [0,2,4], 3)
prueba('COLAPSADO SOLO (W6, lg(techo-vm)) g3', [0,4], 3)
prueba('COLAPSADO SOLO lg(techo-vm) g3', [4], 3)
