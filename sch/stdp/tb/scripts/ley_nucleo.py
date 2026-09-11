"""La ley del nucleo con L(M4) fija: competencia, LOO por geometria y suelo.

8 valores de W, 21 de Vdep. Ahora el LOO deja fuera una W ENTERA y predice sin
haberla visto, que es lo que le pedira el motor.
"""
import numpy as np

A = np.load('/tmp/stdp/nucleo_w.npz')['filas']     # W, L, v, suelo, senal
W_G = sorted(set(A[:, 0]))
FAM = {
    'E1 exp      (2)': lambda v: [v, np.ones_like(v)],
    'E2 exp+cuad (3)': lambda v: [v**2, v, np.ones_like(v)],
    'M1 mixta    (3)': lambda v: [v, np.log(v), np.ones_like(v)],
    'E3 exp+cub  (4)': lambda v: [v**3, v**2, v, np.ones_like(v)],
}

def curva(w):
    m = A[:, 0] == w
    v, s = A[m, 2], np.abs(A[m, 4])
    u = s > 1e-6
    return v[u], s[u]

print('  %-18s %10s %10s %12s %12s'
      % ('familia', 'int[%]', 'LOO[%]', 'peor LOO[%]', 'peor pto[%]'))
for nom, f in FAM.items():
    C = {}
    for w in W_G:
        v, s = curva(w)
        C[w], *_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)
    n = len(C[W_G[0]])
    # interno
    ei = []
    for w in W_G:
        v, s = curva(w)
        M = np.vstack(f(v)).T
        ei.append(np.sqrt(np.mean((np.abs(np.exp(M @ C[w]) - s) / s) ** 2)))
    # LOO por W entera: cada coeficiente como cuadratica en log W
    el, peor = [], 0.0
    for fuera in W_G:
        dentro = [w for w in W_G if w != fuera]
        X = np.array([[np.log(w) ** 2, np.log(w), 1.0] for w in dentro])
        pc = [np.linalg.lstsq(X, np.array([C[w][k] for w in dentro]),
                              rcond=None)[0] @ [np.log(fuera) ** 2, np.log(fuera), 1.0]
              for k in range(n)]
        v, s = curva(fuera)
        rel = np.abs(np.exp(np.vstack(f(v)).T @ np.array(pc)) - s) / s
        el.append(np.sqrt(np.mean(rel ** 2))); peor = max(peor, rel.max())
    print('  %-18s %10.2f %10.2f %12.2f %12.2f'
          % (nom, 100*np.mean(ei), 100*np.mean(el), 100*max(el), 100*peor))

print('\n  --- el SUELO como ley en W ---')
su = np.array([A[A[:, 0] == w][0, 3] for w in W_G])
for nom, X in (('lineal en W', np.vstack([W_G, np.ones(len(W_G))]).T),
               ('potencia', np.vstack([np.log(W_G), np.ones(len(W_G))]).T)):
    y = su if nom == 'lineal en W' else np.log(np.abs(su))
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ c if nom == 'lineal en W' else -np.exp(X @ c)
    rel = np.abs(pred - su) / np.abs(su)
    print('  %-14s error %6.2f %%   peor %6.2f %%   %s'
          % (nom, 100*np.sqrt(np.mean(rel**2)), 100*rel.max(),
             ('suelo = %+.4f + %.4f*W mV' % (c[1]*1e3, c[0]*1e3))
             if nom == 'lineal en W' else ('exponente %.3f' % c[0])))
