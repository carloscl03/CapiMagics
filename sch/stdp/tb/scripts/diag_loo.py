"""De donde sale el 23 % del LOO?

Tres candidatos:
  a) EXTRAPOLACION: las geometrias del borde no tienen vecinos a un lado
  b) FORMA de coef(W,L): la ley de potencia no describe como varian
  c) NO SEPARABLE: coef(W,L) no se factoriza en algo simple

Se miran los tres con los datos que hay, antes de medir mas.
"""
import numpy as np

A = np.load('/tmp/stdp/nucleo.npz')['filas']
f = lambda v: [v, np.log(v), np.ones_like(v)]        # M1
GEOM = sorted(set(map(tuple, A[:, :2])))
W_G = sorted(set(g[0] for g in GEOM)); L_G = sorted(set(g[1] for g in GEOM))

def curva(g):
    m = (A[:,0]==g[0]) & (A[:,1]==g[1])
    v, s = A[m,2], np.abs(A[m,4])
    u = s > 1e-6
    return v[u], s[u]

C = {}
for g in GEOM:
    v, s = curva(g)
    C[g],*_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)

print('  --- los coeficientes, geometria a geometria ---')
print('  %10s %10s %10s %10s' % ('W/L', 'c_V', 'c_logV', 'c_1'))
for g in GEOM:
    print('  %10s %10.4f %10.4f %10.4f' % ('%.2f/%.2f'%g, *C[g]))

print('\n  --- (c) separabilidad: doble centrado de cada coeficiente ---')
for k, nom in enumerate(('c_V', 'c_logV', 'c_1')):
    M = np.array([[C[(w,l)][k] for l in L_G] for w in W_G])
    D = M - M.mean(1, keepdims=True) - M.mean(0, keepdims=True) + M.mean()
    sv = np.linalg.svd(M - M.mean(), compute_uv=False)
    print('  %-8s residuo tras doble centrado %8.4f   (rango efectivo: %s)'
          % (nom, np.abs(D).max(), ' '.join('%.3f'%x for x in sv/sv[0])))

print('\n  --- (a) error LOO geometria a geometria ---')
print('  %10s %10s %10s' % ('W/L', 'LOO[%]', 'en borde?'))
for fuera in GEOM:
    dentro = [g for g in GEOM if g != fuera]
    X = np.array([[np.log(g[0]), np.log(g[1]), 1.0] for g in dentro])
    pc = [np.linalg.lstsq(X, np.array([C[g][k] for g in dentro]), rcond=None)[0]
          @ [np.log(fuera[0]), np.log(fuera[1]), 1.0] for k in range(3)]
    v, s = curva(fuera)
    rel = np.abs(np.exp(np.vstack(f(v)).T @ np.array(pc)) - s)/s
    borde = fuera[0] in (W_G[0], W_G[-1]) or fuera[1] in (L_G[0], L_G[-1])
    print('  %10s %10.2f %10s' % ('%.2f/%.2f'%fuera, 100*np.sqrt(np.mean(rel**2)),
                                  'si' if borde else 'NO (centro)'))
