import numpy as np

G = np.load('fuga_bar.npz'); vg = G['v']; Ig = G['I']; cg = G['casos']
J = np.load('iny_bar.npz'); ci = J['casos']; V0 = J['V0']; dV = J['dV']
UMB = 100.0


def evalua(fu, d, cap):
    """Devuelve (decadas utiles, pendiente mediana, rizado maximo) en la banda."""
    f_ = lambda x: np.interp(x, vg, fu)
    d_ = lambda x: np.interp(x, V0, d)
    fs = np.logspace(-0.3, 4.4, 400) * 1e3
    vv = np.linspace(0.9, 2.60, 1600)
    pts = []
    for fr in fs:
        r = d_(vv) - f_(vv) / (fr * cap)
        j = np.where(np.diff(np.sign(r)))[0]
        if len(j):
            pts.append((fr, np.interp(0, [r[j[0]], r[j[0] + 1]], [vv[j[0]], vv[j[0] + 1]])))
    if len(pts) < 10:
        return None
    fa = np.array([p[0] for p in pts]); va = np.array([p[1] for p in pts])
    s = 1000 * np.gradient(va, np.log10(fa))
    m = s > UMB
    if m.sum() < 3:
        return None
    riz = 1000 * np.array([d_(x) for x in va[m]])
    return (np.log10(fa[m][-1] / fa[m][0]), np.median(s[m]), riz.max(),
            fa[m][0], fa[m][-1])


res = []
for a in range(len(cg)):
    for b in range(len(ci)):
        r = evalua(np.abs(Ig[:, a]), dV[b], ci[b, 2] * 1e-15)
        if r:
            res.append((r, a, b))

# frente de Pareto: anchura contra resolucion (pendiente/rizado)
pts = [(r[0], r[1] / max(r[2], 1e-9), a, b, r) for r, a, b in res]
front = []
for d, q, a, b, r in sorted(pts, key=lambda x: -x[0]):
    if all(q > f[1] for f in front) or not front:
        front.append((d, q, a, b, r))

print('=== FRENTE DE PARETO: anchura contra resolucion ===')
print('%8s %9s | %6s %6s %7s | %6s %6s %7s | %14s'
      % ('decadas', 'resol', 'L1', 'L2', 'Iref', 'W6', 'L6', 'C[fF]', 'banda [kHz]'))
for d, q, a, b, r in front:
    W1, L1, W2, L2, Ir = cg[a]; W6, L6, Cf = ci[b]
    print('%8.2f %9.1f | %6.2f %6.2f %6.0fn | %6.2f %6.2f %7.0f | %6.0f-%-7.0f'
          % (d, q, L1, L2, Ir * 1e9, W6, L6, Cf, r[3] * 1e-3, r[4] * 1e-3))

print()
for nomb, cc, ii in [('ORIGINAL', (1.0, 0.28, 1.0, 0.28, 5e-08), (1.0, 0.28, 5111.0)),
                     ('el que propuse', (1.0, 0.28, 1.0, 1.0, 2.5e-08), (0.25, 1.0, 5111.0))]:
    a = int(np.where((cg == np.array(cc)).all(1))[0][0])
    b = int(np.where((ci == np.array(ii)).all(1))[0][0])
    r = evalua(np.abs(Ig[:, a]), dV[b], ii[2] * 1e-15)
    print('  %-16s %.2f decadas, pendiente %.0f mV/dec, rizado %.0f mV -> resol %.1f'
          % (nomb, r[0], r[1], r[2], r[1] / r[2]))
print()
print('  la neurona necesita 2.74 decadas (8.2 - 4500 kHz)')
