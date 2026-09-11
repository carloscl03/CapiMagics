"""v2: el techo por LEY, no por vecino mas proximo.

v1 asignaba a cada una de las 200 geometrias aleatorias de iny3 el techo de la
geometria mas cercana de mi malla regular de 48. El error mediano en L6 era
0.095 um, y como el techo va de 2.73 a 2.42 entre L6=0.28 y 0.5, eso son ~100 mV
de error en la propia variable del colapso. El test no valia.
"""
import itertools
import numpy as np

T = np.load('techo.npz')
TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE)
Zt = np.log10(TG[ok])
Bt = np.column_stack([np.ones(ok.sum())] + [Zt[:, k]**p for k in (0, 1) for p in (1, 2, 3)])
ct = np.linalg.lstsq(Bt, TE[ok], rcond=None)[0]
print('=== ley del techo: %d coef, error medio %.1f mV sobre su propia malla ==='
      % (len(ct), 1000*np.abs(Bt@ct - TE[ok]).mean()))

def techo_ley(W6, L6):
    z = np.array([np.log10(W6), np.log10(L6)])
    b = np.concatenate([[1.0]] + [[z[k]**p] for k in (0, 1) for p in (1, 2, 3)])
    return float(b @ ct)

J = np.load('iny3.npz'); C = J['casos']; V0 = J['V0']; DV = J['dV']
print('   rango de iny3: W6 %.3f-%.3f, L6 %.3f-%.3f  (malla del techo: 0.25-2.0, 0.28-2.0)'
      % (C[:,0].min(), C[:,0].max(), C[:,1].min(), C[:,1].max()))
X, Y, GID = [], [], []
fuera = 0
for i in range(len(C)):
    W6, L6, Cf = C[i]
    if not (0.25 <= W6 <= 2.0 and 0.28 <= L6 <= 2.0):
        fuera += 1; continue
    tc = techo_ley(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.003 and v < tc - 0.05:
            X.append([np.log10(W6), np.log10(L6), np.log10(Cf), v, np.log10(tc - v)])
            Y.append(np.log10(d)); GID.append(i)
X = np.array(X); Y = np.array(Y); GID = np.array(GID)
print('   %d puntos, %d geometrias  (%d fuera del rango del techo)'
      % (len(Y), len(set(GID)), fuera))
print()

rng = np.random.default_rng(11)
gs = np.array(sorted(set(GID))); gp = rng.permutation(gs)
trg = set(gp[:int(0.7*len(gs))])
tr = np.array([g in trg for g in GID]); te = ~tr

def prueba(nm, cols, grado):
    Z = X[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    if B.shape[1] >= tr.sum():
        print('  %-40s %4d  (mas terminos que datos)' % (nm, B.shape[1])); return
    c = np.linalg.lstsq(B[tr], Y[tr], rcond=None)[0]
    r = 100*np.abs(10**(B[te]@c - Y[te]) - 1)
    print('  %-40s %4d %9.2f%% %10.1f%%' % (nm, B.shape[1], r.mean(), np.percentile(r, 90)))

print('  %-40s %4s %10s %11s' % ('forma', 'coef', 'EXT GEOM', 'p90'))
prueba('LA VIEJA: P5(W6,L6,C,vm)', [0,1,2,3], 5)
prueba('P3(W6,L6,C,vm)', [0,1,2,3], 3)
prueba('COLAPSADA g2: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 2)
prueba('COLAPSADA g3: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 3)
prueba('COLAPSADA g4: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 4)
prueba('COLAPSADA g3 sin C: (W6,L6,lg(techo-vm))', [0,1,4], 3)
