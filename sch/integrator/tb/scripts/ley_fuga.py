"""Ley de la fuga del integrador: I_leak(vm; W1,L1,W2,L2,Iref).

Lecciones aplicadas del encoder: ajustar solo la region util, por regimen si
hace falta, y validar fuera de muestra con particion por GEOMETRIA (no por
punto), que si no las 66 muestras de una misma geometria se reparten entre
entrenamiento y test y el error sale falsamente bajo.
"""
import itertools

import numpy as np

D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; casos = D['casos']
NOM = ['W1', 'L1', 'W2', 'L2', 'Iref']

# region util: donde el circuito conduce de verdad y vm esta en su ventana fisica
VLO, VHI = 0.95, 2.30

filas = []
for a in range(len(casos)):
    W1, L1, W2, L2, Ir = casos[a]
    y = np.abs(I[:, a])
    for k, vm in enumerate(v):
        if VLO <= vm <= VHI and y[k] > 1e-12:
            filas.append((a, W1, L1, W2, L2, Ir, vm, y[k]))
F = np.array(filas)
print('%d muestras utiles, de %d geometrias' % (len(F), len(set(F[:, 0]))))

geo = F[:, 0].astype(int)
X = np.column_stack([np.log10(F[:, 1]), np.log10(F[:, 2]), np.log10(F[:, 3]),
                     np.log10(F[:, 4]), np.log10(F[:, 5]), F[:, 6]])
y = np.log10(F[:, 7])

# particion POR GEOMETRIA
gs = np.unique(geo)
rng = np.random.default_rng(11); rng.shuffle(gs)
ntr = int(0.7 * len(gs))
tr = np.isin(geo, gs[:ntr]); te = np.isin(geo, gs[ntr:])
print('%d geometrias de ajuste, %d de test' % (ntr, len(gs) - ntr))


def base(Z, grado):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(grado + 1), repeat=6):
        if 0 < sum(e) <= grado:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)


print()
print('%8s %10s %10s %10s' % ('grado', 'terminos', 'ajuste', 'EXTERNO'))
mejor = None
for g in (1, 2, 3):
    B = base(X, g)
    c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
    e = lambda m: (100 * np.abs(10 ** (B[m] @ c - y[m]) - 1)).mean()
    print('%8d %10d %9.2f%% %9.2f%%' % (g, B.shape[1], e(tr), e(te)))
    if mejor is None or e(te) < mejor[0]:
        mejor = (e(te), g, B.shape[1])

print()
print('la ley de potencia (grado 1), en claro:')
B = base(X, 1)
c = np.linalg.lstsq(B, y, rcond=None)[0]
print('  lg I_fuga = %+.4f %s %+.4f vm'
      % (c[0], ' '.join('%+.4f lg%s' % (x, n) for x, n in zip(c[1:6], NOM)), c[6]))
