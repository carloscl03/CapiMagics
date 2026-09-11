"""Competicion de familias para las leyes del encoder.

No hay una curva por geometria (cada una da un escalar), asi que la competicion
es entre FORMAS: en vez de la base polinomica completa de grado 3 (35 terminos),
se prueban formas con distinto grado POR VARIABLE.

La idea sale del propio ranking de terminos: Ll aparece con Ll^3, Ll^2 y Ll
entre los primeros, mientras Wd, Wl y L9 entran suave. Si eso es asi, bastara
polinomio alto en Ll y potencia simple en las demas.
"""
import itertools

import numpy as np

D = np.load('siete.npz'); G = D['geos']; R = D['res']
ok = (R[:, 3] > 0.15) & np.isfinite(R).all(1) & (R[:, 0] > 0)
X = np.log10(G[ok])
SAL = {'Iex(-)': np.log10(R[ok, 0]), 'Iex(+)': np.log10(R[ok, 1]),
       'ganancia': np.log10(R[ok, 2])}
rng = np.random.default_rng(3); idx = rng.permutation(ok.sum())
n = int(0.7 * ok.sum()); tr, te = idx[:n], idx[n:]


def base(grados):
    """Base con grado maximo distinto por variable, y grado total acotado."""
    exps = []
    for e in itertools.product(*[range(g + 1) for g in grados]):
        if sum(e) <= max(grados):
            exps.append(e)
    return np.column_stack([np.prod(X ** np.array(e), axis=1) for e in exps]), exps


CAND = [
    ('potencia pura            ', (1, 1, 1, 1)),
    ('cubica solo en Ll        ', (1, 1, 3, 1)),
    ('cubica en Ll y L9        ', (1, 1, 3, 3)),
    ('cubica en Ll, cuad resto ', (2, 2, 3, 2)),
    ('cuadratica completa      ', (2, 2, 2, 2)),
    ('cubica en Ll y Wd        ', (3, 1, 3, 1)),
    ('cubica completa (la usada)', (3, 3, 3, 3)),
]

print('=== COMPETICION DE FORMAS para las leyes del encoder ===')
print()
print('%-28s %8s %10s %10s %10s'
      % ('forma  (grado por variable)', 'terminos', 'Iex(-)', 'Iex(+)', 'ganancia'))
for nom, gr in CAND:
    B, exps = base(gr)
    fila = ''
    for k, y in SAL.items():
        c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
        e = (100 * np.abs(10 ** (B[te] @ c - y[te]) - 1)).mean()
        fila += '%9.2f%% ' % e
    print('%-28s %8d %s' % (nom, B.shape[1], fila))
print()
print('  orden de las variables: (Wd, Wl, Ll, L9)')
