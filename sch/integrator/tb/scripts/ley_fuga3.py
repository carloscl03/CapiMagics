"""Ley de la fuga, version 3: forma de Early en dos etapas.

Un espejo con modulacion de canal da  I/Iref = A + B*vm, con B ~ 1/L.
Eso es LINEAL en vm, no polinomico en su logaritmo -- por eso las versiones
1 y 2 se quedaban en 2-13 %.

Etapa 1: para cada geometria, ajustar I/Iref = A + B*vm.
Etapa 2: ajustar A y B como leyes de potencia de la geometria.

La forma la sugiere la fisica; los EXPONENTES los ponen los datos.
"""
import numpy as np

D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; casos = D['casos']
NOM = ['W1', 'L1', 'W2', 'L2']

A_ = []; B_ = []; G_ = []; res1 = []
for a in range(len(casos)):
    W1, L1, W2, L2, Ir = casos[a]
    y = np.abs(I[:, a]) / Ir
    m = (y > 0.5) & (v <= 2.30)
    if m.sum() < 10:
        continue
    p = np.polyfit(v[m], y[m], 1)          # y = p[0]*vm + p[1]
    pred = np.polyval(p, v[m])
    res1.append((100 * np.abs(pred / y[m] - 1)).mean())
    B_.append(p[0]); A_.append(p[1]); G_.append((W1, L1, W2, L2))
A_ = np.array(A_); B_ = np.array(B_); G_ = np.array(G_)
print('ETAPA 1: I/Iref = A + B*vm, ajustada por geometria')
print('  %d geometrias, error medio del ajuste lineal: %.2f %%' % (len(A_), np.mean(res1)))
print('  A de %.3f a %.3f     B de %.4f a %.4f /V' % (A_.min(), A_.max(), B_.min(), B_.max()))
print()

X = np.log10(G_)
rng = np.random.default_rng(5); idx = rng.permutation(len(A_))
n = int(0.7 * len(A_)); tr, te = idx[:n], idx[n:]
u = np.ones(len(A_))
B1 = np.column_stack([u, X])
B2 = np.column_stack([u, X] + [X[:, i] * X[:, j] for i in range(4) for j in range(i, 4)])

print('ETAPA 2: A y B como leyes de la geometria')
print('%6s %10s %10s %10s' % ('salida', 'terminos', 'ajuste', 'EXTERNO'))
CO = {}
for nom, yy in (('A', np.log10(A_)), ('B', np.log10(np.maximum(B_, 1e-6)))):
    for et, Bm in (('potencia', B1), ('cuadratica', B2)):
        c = np.linalg.lstsq(Bm[tr], yy[tr], rcond=None)[0]
        f = lambda m: (100 * np.abs(10 ** (Bm[m] @ c - yy[m]) - 1)).mean()
        print('%6s %10d %9.2f%% %9.2f%%' % (nom if et == 'potencia' else '',
                                            Bm.shape[1], f(tr), f(te)))
        if et == 'potencia':
            CO[nom] = np.linalg.lstsq(B1, yy, rcond=None)[0]
    print()

for nom in ('A', 'B'):
    c = CO[nom]
    print('  lg %s = %+.4f %s' % (nom, c[0],
          ' '.join('%+.4f lg%s' % (x, n) for x, n in zip(c[1:], NOM))))

# error de la ley COMPUESTA sobre los puntos originales, geometrias de test
print()
Ap = 10 ** (B1 @ CO['A']); Bp = 10 ** (B1 @ CO['B'])
err = []
for j in te:
    W1, L1, W2, L2 = G_[j]
    a = int(np.where((casos[:, 0] == W1) & (casos[:, 1] == L1) &
                     (casos[:, 2] == W2) & (casos[:, 3] == L2))[0][0])
    Ir = casos[a, 4]
    y = np.abs(I[:, a]) / Ir
    m = (y > 0.5) & (v <= 2.30)
    pred = Ap[j] + Bp[j] * v[m]
    err.append((100 * np.abs(pred / y[m] - 1)).mean())
print('LEY COMPUESTA sobre geometrias de test: %.2f %% de error medio' % np.mean(err))
