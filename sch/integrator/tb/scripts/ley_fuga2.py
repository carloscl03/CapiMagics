"""Ley de la fuga, version 2: normalizada por Iref y restringida al regimen.

El primer intento fallo (1554 % externo, y el exponente de Iref con el signo
invertido) porque la region incluia el CODO DE ENCENDIDO, donde la corriente
sube ordenes de magnitud en pocos mV. Aqui:

  * se ajusta el COCIENTE I_fuga/Iref, que quita el escalado trivial
  * se excluye el codo: solo puntos con I_fuga > 0.5*Iref
  * la particion de validacion sigue siendo POR GEOMETRIA
"""
import itertools

import numpy as np

D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; casos = D['casos']
NOM = ['W1', 'L1', 'W2', 'L2']

filas = []
for a in range(len(casos)):
    W1, L1, W2, L2, Ir = casos[a]
    y = np.abs(I[:, a])
    for k, vm in enumerate(v):
        if y[k] > 0.5 * Ir and vm <= 2.30:
            filas.append((a, W1, L1, W2, L2, Ir, vm, y[k] / Ir))
F = np.array(filas)
geo = F[:, 0].astype(int)
print('%d muestras en regimen, de %d geometrias' % (len(F), len(set(geo))))
print('  el cociente I/Iref va de %.2f a %.2f' % (F[:, 7].min(), F[:, 7].max()))

X = np.column_stack([np.log10(F[:, 1]), np.log10(F[:, 2]), np.log10(F[:, 3]),
                     np.log10(F[:, 4]), F[:, 6]])
y = np.log10(F[:, 7])

gs = np.unique(geo)
rng = np.random.default_rng(11); rng.shuffle(gs)
ntr = int(0.7 * len(gs))
tr = np.isin(geo, gs[:ntr]); te = np.isin(geo, gs[ntr:])
print('  %d geometrias de ajuste, %d de test' % (ntr, len(gs) - ntr))


def base(Z, g):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=5):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)


print()
print('%8s %10s %10s %10s' % ('grado', 'terminos', 'ajuste', 'EXTERNO'))
for g in (1, 2, 3):
    B = base(X, g)
    c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
    f = lambda m: (100 * np.abs(10 ** (B[m] @ c - y[m]) - 1)).mean()
    p95 = lambda m: np.percentile(100 * np.abs(10 ** (B[m] @ c - y[m]) - 1), 95)
    print('%8d %10d %9.2f%% %9.2f%%   (p95 externo %.1f%%)'
          % (g, B.shape[1], f(tr), f(te), p95(te)))

print()
B = base(X, 1)
c = np.linalg.lstsq(B, y, rcond=None)[0]
print('la ley de potencia (grado 1):')
print('  lg(I_fuga/Iref) = %+.4f %s %+.4f vm'
      % (c[0], ' '.join('%+.4f lg%s' % (x, n) for x, n in zip(c[1:5], NOM)), c[5]))
print()
print('  o sea: I_fuga = Iref * 10^(...)  -- el escalado con Iref es EXACTO por construccion')
