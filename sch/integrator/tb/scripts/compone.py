"""Las dos leyes compuestas, contra transitorios de ngspice ya medidos.

  fuga:      I = Iref * P3(lgW1,lgL1,lgW2,lgL2,vm)      valida si I > 0.7*Iref
  inyeccion: dV = P5(lgW6,lgL6,lgC,vm)
  balance:   dV(vm) = I(vm)/(f*C)   ->  vm de equilibrio
"""
import itertools

import numpy as np


def base(Z, g, nv):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=nv):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)


# --- ley de la fuga ---------------------------------------------------------
D = np.load('fuga_bar.npz'); v = D['v']; I = D['I']; cas = D['casos']
fl = []
for a in range(len(cas)):
    y = np.abs(I[:, a]) / cas[a, 4]
    m = (y > 0.7) & (v <= 2.30)
    for k in np.where(m)[0]:
        fl.append([np.log10(cas[a, 0]), np.log10(cas[a, 1]), np.log10(cas[a, 2]),
                   np.log10(cas[a, 3]), v[k], np.log10(y[k])])
FL = np.array(fl)
Bf = base(FL[:, :5], 3, 5)
cf = np.linalg.lstsq(Bf, FL[:, 5], rcond=None)[0]

# --- ley de la inyeccion ----------------------------------------------------
E = np.load('iny3.npz'); cs = E['casos']; V0 = E['V0']; dV = E['dV']
il = []
for i in range(len(cs)):
    for k, vm in enumerate(V0):
        if dV[i, k] > 0.003:
            il.append([np.log10(cs[i, 0]), np.log10(cs[i, 1]), np.log10(cs[i, 2]),
                       vm, np.log10(dV[i, k])])
IL = np.array(il)
Bi = base(IL[:, :4], 5, 4)
ci = np.linalg.lstsq(Bi, IL[:, 4], rcond=None)[0]
print('leyes ajustadas: fuga %d coef, inyeccion %d coef' % (len(cf), len(ci)))


def fuga(vm, W1, L1, W2, L2, Iref):
    Z = np.column_stack([np.full_like(vm, np.log10(W1)), np.full_like(vm, np.log10(L1)),
                         np.full_like(vm, np.log10(W2)), np.full_like(vm, np.log10(L2)), vm])
    return Iref * 10 ** (base(Z, 3, 5) @ cf)


def iny(vm, W6, L6, Cf_):
    Z = np.column_stack([np.full_like(vm, np.log10(W6)), np.full_like(vm, np.log10(L6)),
                         np.full_like(vm, np.log10(Cf_)), vm])
    return 10 ** (base(Z, 5, 4) @ ci)


def equilibrio(g, f_kHz):
    W1, L1, W2, L2, Iref, W6, L6, Cf_ = g
    vv = np.linspace(1.0, 2.45, 900)
    r = iny(vv, W6, L6, Cf_) - fuga(vv, W1, L1, W2, L2, Iref) / (f_kHz * 1e3 * Cf_ * 1e-15)
    j = np.where(np.diff(np.sign(r)))[0]
    if not len(j):
        return np.nan
    return np.interp(0, [r[j[0]], r[j[0] + 1]], [vv[j[0]], vv[j[0] + 1]])


MED = [('ORIGINAL', (1.0, 0.28, 1.0, 0.28, 50e-9, 1.0, 0.28, 5111), {268: 2.208, 1500: 2.343}),
       ('mejorado 25n', (1.0, 0.28, 1.0, 1.00, 25e-9, 0.25, 1.0, 5111), {268: 1.794, 1500: 2.004}),
       ('mejorado 12n', (1.0, 0.28, 1.0, 1.00, 12e-9, 0.25, 1.0, 5111), {268: 1.904, 1500: 2.055})]
print()
print('%-14s %8s %12s %12s %9s' % ('diseño', 'f [kHz]', 'LEYES', 'ngspice', 'error'))
err = []
for nom, g, med in MED:
    for f, real in med.items():
        p = equilibrio(g, f)
        e = 1000 * (p - real)
        err.append(abs(e))
        print('%-14s %8d %11.3f V %11.3f V %7.0f mV' % (nom, f, p, real, e))
print()
print('  error medio %.0f mV, peor %.0f mV' % (np.mean(err), np.max(err)))
print('  (la version interpolada daba +-4 %% cerca y 25-59 %% lejos)')
np.savez('leyes.npz', cf=cf, ci=ci)
