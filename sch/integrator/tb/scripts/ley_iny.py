"""Ley de la inyeccion. El colapso fallo (54 %), asi que: polinomio con dominio,
y prueba de particion por regimen.

Validacion POR GEOMETRIA, como en la fuga.
"""
import itertools

import numpy as np

D = np.load('iny2.npz')
casos = D['casos']; V0 = D['V0']; dV = D['dV']

filas = []
for i in range(len(casos)):
    W6, L6, Cf = casos[i]
    for k, vm in enumerate(V0):
        if dV[i, k] > 0.003:
            filas.append((i, W6, L6, Cf, vm, dV[i, k]))
F = np.array(filas)
geo = F[:, 0].astype(int)
print('%d muestras de %d geometrias' % (len(F), len(set(geo))))

X = np.column_stack([np.log10(F[:, 1]), np.log10(F[:, 2]), np.log10(F[:, 3]), F[:, 4]])
y = np.log10(F[:, 5])

gs = np.unique(geo)
rng = np.random.default_rng(9); rng.shuffle(gs)
n = int(0.7 * len(gs))
tr = np.isin(geo, gs[:n]); te = np.isin(geo, gs[n:])
print('  %d geometrias de ajuste, %d de test' % (n, len(gs) - n))


def base(Z, g):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=4):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)


print()
print('=== todo junto ===')
print('%8s %10s %10s %10s' % ('grado', 'terminos', 'ajuste', 'EXTERNO'))
for g in (1, 2, 3):
    B = base(X, g)
    c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
    f = lambda m: (100 * np.abs(10 ** (B[m] @ c - y[m]) - 1)).mean()
    print('%8d %10d %9.2f%% %9.2f%%' % (g, B.shape[1], f(tr), f(te)))

print()
print('=== partido por REGIMEN de condensador ===')
print('%10s %8s %8s %10s %10s' % ('C [fF]', 'n geom', 'grado', 'ajuste', 'EXTERNO'))
for Cv in (1000, 5111, 20000):
    m = np.abs(F[:, 3] - Cv) < 1
    if m.sum() < 40:
        continue
    Xs = X[m][:, :3]                       # sin lgC: es constante en el regimen
    Xs = np.column_stack([Xs[:, 0], Xs[:, 1], X[m][:, 3]])
    ys = y[m]; gs_ = geo[m]
    u = np.unique(gs_); r = np.random.default_rng(4); r.shuffle(u)
    nn = int(0.7 * len(u))
    t1 = np.isin(gs_, u[:nn]); t2 = np.isin(gs_, u[nn:])

    def b3(Z, g):
        cols = [np.ones(len(Z))]
        for e in itertools.product(range(g + 1), repeat=3):
            if 0 < sum(e) <= g:
                t = np.ones(len(Z))
                for j, k in enumerate(e):
                    if k:
                        t = t * Z[:, j] ** k
                cols.append(t)
        return np.column_stack(cols)

    for g in (1, 2, 3):
        B = b3(Xs, g)
        c = np.linalg.lstsq(B[t1], ys[t1], rcond=None)[0]
        f = lambda mm: (100 * np.abs(10 ** (B[mm] @ c - ys[mm]) - 1)).mean()
        print('%10.0f %8d %8d %9.2f%% %9.2f%%' % (Cv, len(u), g, f(t1), f(t2)))
    print()
