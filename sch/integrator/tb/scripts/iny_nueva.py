"""La forma colapsada, ajustada sobre iny3.npz -- el terreno de la ley vieja.

Dos preguntas:
  1. La ley vieja (126 terminos, 4.14 %) se valido POR PUNTO o POR GEOMETRIA?
     Si fue por punto, su 4.14 % es optimista: puntos de la misma geometria a
     los dos lados hacen que la ley solo tenga que interpolar en vm.
  2. Reemplaza la forma colapsada a la de 126 en su propio terreno?

El techo de cada geometria se toma de `techo.npz` (medido hasta 3.25 V), no del
borde de la malla de iny3 (que acababa en 2.45 y era lo que fallaba).
"""
import itertools
import numpy as np

T = np.load('techo.npz')
TG, TE = T['geos'], T['techo']
def techo(W6, L6, Cf):
    d = (TG[:,0]-W6)**2 + (TG[:,1]-L6)**2 + ((TG[:,2]-Cf)/1e4)**2
    return TE[int(np.argmin(d))]

J = np.load('iny3.npz'); C = J['casos']; V0 = J['V0']; DV = J['dV']
X, Y, GID = [], [], []
for i in range(len(C)):
    W6, L6, Cf = C[i]
    tc = techo(W6, L6, Cf)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.003 and v < tc - 0.02:
            X.append([np.log10(W6), np.log10(L6), np.log10(Cf), v, np.log10(tc - v)])
            Y.append(np.log10(d)); GID.append(i)
X = np.array(X); Y = np.array(Y); GID = np.array(GID)
print('=== %d puntos, %d geometrias de iny3.npz ===' % (len(Y), len(set(GID))))
print('   (de %d posibles; se quitan los que estan sobre el techo)' % DV.size)
print()

rng = np.random.default_rng(11)
gs = np.array(sorted(set(GID))); gp = rng.permutation(gs)
trg = set(gp[:int(0.7*len(gs))])
tr_g = np.array([g in trg for g in GID]); te_g = ~tr_g
idx = rng.permutation(len(Y)); n = int(0.7*len(Y))
tr_p = np.zeros(len(Y), bool); tr_p[idx[:n]] = True; te_p = ~tr_p

def prueba(nm, cols, grado):
    Z = X[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    out = []
    for et, tr, te in (('punto', tr_p, te_p), ('GEOM', tr_g, te_g)):
        if B.shape[1] >= tr.sum():
            out.append(float('nan')); continue
        c = np.linalg.lstsq(B[tr], Y[tr], rcond=None)[0]
        out.append((100*np.abs(10**(B[te]@c - Y[te]) - 1)).mean())
    print('  %-40s %4d %9.2f%% %11.2f%%' % (nm, B.shape[1], out[0], out[1]))

print('  %-40s %4s %10s %12s' % ('forma', 'coef', 'ext PUNTO', 'ext GEOMETRIA'))
prueba('LA VIEJA: P5(W6,L6,C,vm)', [0,1,2,3], 5)
prueba('P3(W6,L6,C,vm)', [0,1,2,3], 3)
prueba('COLAPSADA g2: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 2)
prueba('COLAPSADA g3: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 3)
prueba('COLAPSADA g4: (W6,L6,C,lg(techo-vm))', [0,1,2,4], 4)
