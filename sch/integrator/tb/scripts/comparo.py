"""Comparacion honesta: la ley por COLAPSO contra la ley POLINOMICA.

Las dos se evaluan igual: error de prediccion sobre geometrias que no se han
visto (particion por geometria, 70/30).
"""
import itertools

import numpy as np

D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; casos = D['casos']
C1 = np.load('colapso.npz'); ps = C1['ps']; pg = C1['pg']

cur = []
for a in range(len(casos)):
    y = np.abs(I[:, a]) / casos[a, 4]
    m = (y > 0.3) & (v <= 2.30)
    if m.sum() >= 10:
        cur.append((a, np.log10(casos[a, :4]), v[m], y[m]))

idx = np.arange(len(cur))
rng = np.random.default_rng(21); rng.shuffle(idx)
n = int(0.7 * len(cur)); tr, te = idx[:n], idx[n:]
print('%d curvas: %d de ajuste, %d de test' % (len(cur), len(tr), len(te)))

# --- A) ley por COLAPSO: curva maestra tabulada de los datos de ajuste -------
XX = []; YY = []
for j in tr:
    a, lg, vm, y = cur[j]
    XX.append(vm * 10 ** np.dot(lg, ps)); YY.append(np.log10(y * 10 ** np.dot(lg, pg)))
X = np.concatenate(XX); Y = np.concatenate(YY)
o = np.argsort(X); X, Y = X[o], Y[o]
# curva maestra: mediana movil sobre 60 tramos
b = np.quantile(X, np.linspace(0, 1, 61))
mx = []; my = []
for i in range(60):
    m = (X >= b[i]) & (X <= b[i + 1])
    if m.sum() > 3:
        mx.append(X[m].mean()); my.append(np.median(Y[m]))
mx = np.array(mx); my = np.array(my)

err_col = []
for j in te:
    a, lg, vm, y = cur[j]
    xx = vm * 10 ** np.dot(lg, ps)
    pred = 10 ** (np.interp(xx, mx, my)) / 10 ** np.dot(lg, pg)
    err_col.append((100 * np.abs(pred / y - 1)).mean())

# --- B) ley POLINOMICA en (lgW1, lgL1, lgW2, lgL2, vm) ----------------------
def arma(js):
    Z = []; yy = []
    for j in js:
        a, lg, vm, y = cur[j]
        for k in range(len(vm)):
            Z.append([lg[0], lg[1], lg[2], lg[3], vm[k]]); yy.append(np.log10(y[k]))
    return np.array(Z), np.array(yy)


def base(Z, g):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=5):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for i, k in enumerate(e):
                if k:
                    t = t * Z[:, i] ** k
            cols.append(t)
    return np.column_stack(cols)


Ztr, ytr = arma(tr)
print()
print('%-26s %10s %12s' % ('ley', 'coeficientes', 'error externo'))
print('%-26s %10d %11.2f %%' % ('COLAPSO (L2) + maestra', 8 + len(mx), np.mean(err_col)))
for g in (1, 2, 3):
    Btr = base(Ztr, g)
    c = np.linalg.lstsq(Btr, ytr, rcond=None)[0]
    e = []
    for j in te:
        a, lg, vm, y = cur[j]
        Z = np.column_stack([np.repeat(lg[0], len(vm)), np.repeat(lg[1], len(vm)),
                             np.repeat(lg[2], len(vm)), np.repeat(lg[3], len(vm)), vm])
        pred = 10 ** (base(Z, g) @ c)
        e.append((100 * np.abs(pred / y - 1)).mean())
    print('%-26s %10d %11.2f %%' % ('polinomica grado %d' % g, Btr.shape[1], np.mean(e)))
