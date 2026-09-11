"""LOO POR GEOMETRIA, no por punto.

Hasta ahora todo el integrador iba con UNA particion 70/30, que depende de la
semilla. LOO deja fuera una geometria entera cada vez y promedia: no hay semilla
que valga y el estimador es mucho mas estable.

Por geometria, no por punto: dejar fuera un punto suelto deja los demas de la
misma geometria dentro, y la ley solo tendria que interpolar en vm.
"""
import itertools, sys, time
import numpy as np

T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE); Zt = np.log10(TG[ok])
Bt = np.column_stack([np.ones(ok.sum())] + [Zt[:, k]**p for k in (0,1) for p in (1,2,3)])
ct = np.linalg.lstsq(Bt, TE[ok], rcond=None)[0]
def techo_ley(W6, L6):
    z = [np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]] + [[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ ct)

J = np.load('iny3.npz'); C = J['casos']; V0 = J['V0']; DV = J['dV']
X, Y, GID = [], [], []
for i in range(len(C)):
    W6, L6, Cf = C[i]
    if not (0.25 <= W6 <= 2.0 and 0.28 <= L6 <= 2.0):
        continue
    tc = techo_ley(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.003 and v < tc - 0.05:
            X.append([np.log10(W6), np.log10(L6), np.log10(Cf), v, np.log10(tc-v)])
            Y.append(np.log10(d)); GID.append(i)
X = np.array(X); Y = np.array(Y); GID = np.array(GID)
G = np.array(sorted(set(GID)))
print('=== LOO por geometria: %d puntos, %d geometrias ===' % (len(Y), len(G)))
sys.stdout.flush()

def loo(nm, cols, grado):
    Z = X[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    t0 = time.time(); er = []
    for g in G:
        m = GID == g
        if B.shape[1] >= (~m).sum():
            return
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
    e = np.concatenate(er)
    # tambien el peor caso POR GEOMETRIA, que es lo que ve el motor
    pg = np.array([x.mean() for x in er])
    print('  %-40s %4d %9.2f%% %10.1f%% %9.1f%% %6.0fs'
          % (nm, B.shape[1], e.mean(), np.percentile(e, 90), pg.max(), time.time()-t0))
    sys.stdout.flush()

print('  %-40s %4s %10s %11s %10s %6s'
      % ('forma', 'coef', 'LOO medio', 'LOO p90', 'peor geom', 't'))
loo('LA VIEJA: P5(W6,L6,C,vm)', [0,1,2,3], 5)
loo('P3(W6,L6,C,vm)', [0,1,2,3], 3)
loo('COLAPSADA g2', [0,1,2,4], 2)
loo('COLAPSADA g3', [0,1,2,4], 3)
loo('COLAPSADA g4', [0,1,2,4], 4)
