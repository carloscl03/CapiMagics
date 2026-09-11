"""Competicion de formas para las leyes de INTERFAZ del encoder.

Nunca compitieron contra nada: son leyes de potencia porque la potencia
ajustaba razonablemente. Son las peores del paquete (5.6 %, 9.4 %, 15.1 %).

Se prueban formas con distinto grado por variable, como se hizo con las cubicas.
"""
import itertools

import numpy as np

# --- sigma_Vos, del Monte Carlo de desapareamiento -------------------------
M = np.load('mcley7.npz') if False else None
D = np.load('mcley_sigma.npz')
Xs = np.log10(D['geos']); ys = np.log10(D['sig'])

# --- ro de salida, del barrido del espejo ----------------------------------
Rx = np.load('rox_proc.npz')
Xr = Rx['X']; yr = Rx['y']

# --- I_ref del bias --------------------------------------------------------
Ir = np.load('iref_proc.npz')
Xi = Ir['X']; yi = Ir['y']


def compite(X, y, nombres, titulo, cands):
    print('=== %s ===' % titulo)
    print('  %d muestras, %d variables' % (len(y), X.shape[1]))
    print()
    rng = np.random.default_rng(3)
    idx = rng.permutation(len(y)); n = int(0.7 * len(y)); tr, te = idx[:n], idx[n:]
    print('  %-34s %9s %11s' % ('forma', 'terminos', 'EXTERNO'))
    for nom, gr in cands:
        exps = [e for e in itertools.product(*[range(g + 1) for g in gr])
                if sum(e) <= max(gr)]
        B = np.column_stack([np.prod(X ** np.array(e), axis=1) for e in exps])
        if B.shape[1] >= n:
            print('  %-34s %9d   (mas terminos que datos)' % (nom, B.shape[1]))
            continue
        c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
        e = (100 * np.abs(10 ** (B[te] @ c - y[te]) - 1)).mean()
        print('  %-34s %9d %10.2f%%' % (nom, B.shape[1], e))
    print()


compite(Xs, ys, ['Wd', 'Wl', 'Ll', 'L9'], 'sigma_Vos  (hoy: potencia, 5.6 %)',
        [('potencia               (1,1,1,1)', (1, 1, 1, 1)),
         ('cuadratica             (2,2,2,2)', (2, 2, 2, 2)),
         ('cuad solo en Wd y Ll   (2,1,2,1)', (2, 1, 2, 1)),
         ('cubica en Ll           (1,1,3,1)', (1, 1, 3, 1)),
         ('cubica completa        (3,3,3,3)', (3, 3, 3, 3))])

compite(Xr, yr, ['Wo', 'Lo', 'Iex'], 'ro de salida  (hoy: potencia, 9.4 %)',
        [('potencia               (1,1,1)', (1, 1, 1)),
         ('cuadratica             (2,2,2)', (2, 2, 2)),
         ('cuad solo en Iex       (1,1,2)', (1, 1, 2)),
         ('cubica en Iex          (1,1,3)', (1, 1, 3)),
         ('cubica completa        (3,3,3)', (3, 3, 3))])

compite(Xi, yi, ['Wn', 'Ln', 'Wp', 'Lp'], 'I_ref del bias  (hoy: potencia, 15.1 %)',
        [('potencia               (1,1,1,1)', (1, 1, 1, 1)),
         ('cuadratica             (2,2,2,2)', (2, 2, 2, 2)),
         ('cuad solo en las L     (1,2,1,2)', (1, 2, 1, 2)),
         ('cubica completa        (3,3,3,3)', (3, 3, 3, 3))])
