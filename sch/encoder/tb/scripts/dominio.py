"""Cuanto dominio necesitamos DE VERDAD, y cuanta complejidad estamos pagando.

Para cada rango de excursion de Iex que el sistema podria pedir, se mide:
  - que ventana de Vdif hace falta
  - cuantos terminos cuesta la ley para bajar de 1 % de error externo
  - cuanto separa la respuesta (si separa, basta ley de potencia)
"""
import itertools

import numpy as np

C = np.load('caja.npz')
jb = int(np.argmin(np.abs(C['vbias'] - 1.2)))
ie = np.abs(C['iex'][:, jb, :]); vx = C['vx'][:, jb, :]
vd = C['vd']; G = C['casos']
k0 = int(np.argmin(np.abs(vd)))


def sep(M):
    M = np.asarray(M, float)
    D = M - M.mean(1, keepdims=True) - M.mean(0, keepdims=True) + M.mean()
    return 100 * (1 - (D ** 2).sum() / ((M - M.mean()) ** 2).sum())


def base(Z, g, nv):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=nv):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, kk in enumerate(e):
                if kk:
                    t = t * Z[:, j] ** kk
            cols.append(t)
    return np.column_stack(cols)


X = np.log10(G[:, [0, 2, 3, 5]])          # Wd, Wl, Ll, L9
rng = np.random.default_rng(7)
idx = rng.permutation(len(X)); n = int(0.7 * len(X)); tr, te = idx[:n], idx[n:]

print('=== cuanta complejidad cuesta cada dominio ===')
print()
print('%10s %12s %14s %10s %s' % ('excursion', 'ventana Vdif', 'Iex [nA]', 'separa',
                                  'error externo por grado (1/2/3)'))
for exc in (3, 5, 10, 20, 50, 200):
    # ventana simetrica de Vdif que da esa excursion en la geometria mediana
    med = np.argsort(ie[:, k0])[len(ie) // 2]
    best = None
    for w in np.arange(0.02, 0.62, 0.02):
        a = int(np.argmin(np.abs(vd + w))); b = int(np.argmin(np.abs(vd - w)))
        r = ie[med, b] / max(ie[med, a], 1e-15)
        if r >= exc:
            best = (w, a, b); break
    if best is None:
        continue
    w, a, b = best
    lo = np.log10(np.maximum(ie[:, a], 1e-15)); hi = np.log10(np.maximum(ie[:, b], 1e-15))
    ok = np.isfinite(lo) & np.isfinite(hi) & (ie[:, a] > 1e-12)
    m = (vd >= -w) & (vd <= w)
    okS = (ie[:, m] > 1e-12).all(1)
    s = sep(np.log10(ie[okS][:, m]))
    errs = []
    for g in (1, 2, 3):
        B = base(X, g, 4)
        cc = np.linalg.lstsq(B[np.intersect1d(tr, np.where(ok)[0])],
                             lo[np.intersect1d(tr, np.where(ok)[0])], rcond=None)[0]
        t2 = np.intersect1d(te, np.where(ok)[0])
        errs.append((100 * np.abs(10 ** (B[t2] @ cc - lo[t2]) - 1)).mean())
    print('%9.0fx %11s %7.1f-%-7.1f %9.1f%%  %s'
          % (exc, '+-%.2f V' % w, 10 ** lo[okS].mean(), 10 ** hi[okS].mean(), s,
             '  '.join('%.2f%%' % e for e in errs)))
