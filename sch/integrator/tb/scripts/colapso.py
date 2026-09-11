"""Busqueda de colapso en la fuga del integrador. SIN imponer forma.

No se supone ninguna ecuacion. Se busca si existe un reescalado

    Y = y * g(geo)        X = vm * s(geo)

con g y s leyes de potencia en (W1, L1, W2, L2), tal que TODAS las curvas
caigan sobre una misma curva maestra. Si existe, la curva maestra se lee de los
datos y la ley queda: y = f(vm*s)/g, con f tabulada o ajustada despues.

La medida de colapso es la dispersion vertical de la nube reescalada respecto a
su propia mediana movil: si las curvas se superponen, es pequeña.
"""
import numpy as np

D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; casos = D['casos']

# datos crudos por geometria, en el regimen conducido
cur = []
for a in range(len(casos)):
    y = np.abs(I[:, a]) / casos[a, 4]
    m = (y > 0.3) & (v <= 2.30)
    if m.sum() >= 10:
        cur.append((np.log10(casos[a, :4]), v[m], y[m]))
print('%d curvas' % len(cur))


def disper(ps, pg):
    """Dispersion de la nube tras reescalar. Menor = mejor colapso."""
    XX = []; YY = []
    for lg, vm, y in cur:
        s = 10 ** np.dot(lg, ps)
        g = 10 ** np.dot(lg, pg)
        XX.append(vm * s); YY.append(np.log10(y * g))
    X = np.concatenate(XX); Y = np.concatenate(YY)
    o = np.argsort(X); X, Y = X[o], Y[o]
    n = 40
    bordes = np.quantile(X, np.linspace(0, 1, n + 1))
    d = []
    for i in range(n):
        m = (X >= bordes[i]) & (X <= bordes[i + 1])
        if m.sum() > 5:
            d.append(np.std(Y[m]))
    return np.mean(d) if d else 9e9


rng = np.random.default_rng(3)
mejor = (disper(np.zeros(4), np.zeros(4)), np.zeros(4), np.zeros(4))
print('  sin reescalar: dispersion %.4f decadas' % mejor[0])

for _ in range(3000):                       # busqueda global
    ps = rng.uniform(-1.5, 1.5, 4); pg = rng.uniform(-1.5, 1.5, 4)
    d = disper(ps, pg)
    if d < mejor[0]:
        mejor = (d, ps, pg)
for paso in (0.3, 0.1, 0.03, 0.01):         # refinado local
    for _ in range(600):
        ps = mejor[1] + rng.normal(0, paso, 4)
        pg = mejor[2] + rng.normal(0, paso, 4)
        d = disper(ps, pg)
        if d < mejor[0]:
            mejor = (d, ps, pg)

d, ps, pg = mejor
NOM = ['W1', 'L1', 'W2', 'L2']
print()
print('  MEJOR COLAPSO: dispersion %.4f decadas (%.1f %%)' % (d, 100 * (10 ** d - 1)))
print('     eje X:  vm * %s' % ' '.join('%s^%+.3f' % (n, p) for n, p in zip(NOM, ps)))
print('     eje Y:  y  * %s' % ' '.join('%s^%+.3f' % (n, p) for n, p in zip(NOM, pg)))
np.savez('colapso.npz', ps=ps, pg=pg, disp=d)
