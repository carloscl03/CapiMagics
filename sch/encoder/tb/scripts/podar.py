"""Cuantos terminos hacen falta de verdad?

Nunca se comprobo. Se anaden terminos por orden de utilidad (seleccion hacia
adelante sobre el error EXTERNO, no sobre el ajuste) y se mira donde deja de
mejorar.
"""
import itertools

import numpy as np


def base_exp(g, nv):
    return [e for e in itertools.product(range(g + 1), repeat=nv) if sum(e) <= g]


def construye(Z, exps):
    return np.column_stack([np.prod(Z ** np.array(e), axis=1) for e in exps])


def poda(Z, y, exps, tr, te, tope, nom, nombres):
    """Seleccion hacia adelante. Devuelve la curva error(n_terminos)."""
    elegidos = []
    resto = list(range(len(exps)))
    curva = []
    for paso in range(tope):
        mejor = None
        for j in resto:
            cand = elegidos + [j]
            B = construye(Z, [exps[k] for k in cand])
            c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
            e = (100 * np.abs(10 ** (B[te] @ c - y[te]) - 1)).mean()
            if mejor is None or e < mejor[0]:
                mejor = (e, j)
        elegidos.append(mejor[1]); resto.remove(mejor[1])
        curva.append(mejor[0])
    print('=== %s ===' % nom)
    print('  terminos:  ' + '  '.join('%d' % (i + 1) for i in range(0, tope, 2)))
    print('  error:     ' + '  '.join('%.2f' % curva[i] for i in range(0, tope, 2)))
    print()
    print('  los primeros 12 terminos elegidos:')
    for i, j in enumerate(elegidos[:12]):
        e = exps[j]
        t = ' * '.join('%s^%d' % (nombres[k], e[k]) for k in range(len(e)) if e[k])
        print('     %2d. %-28s -> %.2f %%' % (i + 1, t if t else '1 (constante)', curva[i]))
    return elegidos, curva


# --- ENCODER: Iex(-) --------------------------------------------------------
D = np.load('siete.npz'); G = D['geos']; R = D['res']
ok = (R[:, 3] > 0.15) & np.isfinite(R).all(1) & (R[:, 0] > 0)
X = np.log10(G[ok]); y = np.log10(R[ok, 0])
rng = np.random.default_rng(3); idx = rng.permutation(ok.sum())
n = int(0.7 * ok.sum()); tr, te = idx[:n], idx[n:]
exps = base_exp(3, 4)
poda(X, y, exps, tr, te, 20, 'ENCODER Iex(-): cubica de %d terminos' % len(exps),
     ['Wd', 'Wl', 'Ll', 'L9'])
