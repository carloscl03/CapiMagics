"""Cuanta CAJA necesitamos, y cuanta complejidad cuesta.

Las leyes del encoder se ajustan a Iex en dos puntos de Vdif fijos, asi que su
complejidad no viene del estimulo sino del espacio de GEOMETRIAS. La pregunta
util es: encogiendo la caja, cuanto se simplifican las leyes y cuanto alcance
se pierde.
"""
import itertools

import numpy as np

D = np.load('siete.npz')
G = D['geos']; R = D['res']
ok0 = (R[:, 3] > 0.15) & np.isfinite(R).all(1) & (R[:, 0] > 0)
X0 = np.log10(G)
CEN = X0[ok0].mean(0)


def base(Z, g):
    E = [e for e in itertools.product(range(g + 1), repeat=4) if sum(e) <= g]
    return np.column_stack([np.prod(Z ** np.array(e), axis=1) for e in E])


print('=== encogiendo la caja alrededor de su centro ===')
print()
print('%8s %9s %14s %16s %s'
      % ('fraccion', 'n geom', 'Iex(-) [nA]', 'alcance (iex,G)', 'error externo g1/g2/g3'))
ref = None
for frac in (1.0, 0.7, 0.5, 0.35, 0.25):
    m = ok0 & (np.abs(X0 - CEN) <= frac * np.abs(X0[ok0] - CEN).max(0)).all(1)
    if m.sum() < 60:
        print('%8.2f %9d  (pocas)' % (frac, m.sum()))
        continue
    Xs = X0[m]; ys = np.log10(R[m, 0]); gs = np.log10(R[m, 2])
    rng = np.random.default_rng(3); idx = rng.permutation(m.sum())
    n = int(0.7 * m.sum()); tr, te = idx[:n], idx[n:]
    e = []
    for g in (1, 2, 3):
        B = base(Xs, g)
        c = np.linalg.lstsq(B[tr], ys[tr], rcond=None)[0]
        e.append((100 * np.abs(10 ** (B[te] @ c - ys[te]) - 1)).mean())
    # alcance: cuantas celdas de (lgIex, lgG) distintas se pueden pedir
    cel = set(zip(np.floor(ys / 0.05).astype(int), np.floor(gs / 0.05).astype(int)))
    if ref is None:
        ref = len(cel)
    print('%8.2f %9d %6.1f-%-7.1f %8d (%3.0f%%)  %s'
          % (frac, m.sum(), 1e9 * 10 ** ys.min(), 1e9 * 10 ** ys.max(),
             len(cel), 100 * len(cel) / ref, '  '.join('%6.2f%%' % x for x in e)))
