"""Competencia de familias, ahora con 21 puntos por geometria en vez de 4.

Y con CURVA DE APRENDIZAJE: si el error no baja al dar mas puntos, falta
modelo; si baja, faltaban datos. Es lo que distingue un ajuste de un
sobreajuste, y con 4 puntos no se podia mirar.

Validacion POR GEOMETRIA entera, nunca por punto.
"""
import numpy as np

A = np.load('/tmp/stdp/nucleo.npz')['filas']    # W, L, v, suelo, senal
FAM = {
    'E1 exp      (2)':   lambda v: [v, np.ones_like(v)],
    'E2 exp+cuad (3)':   lambda v: [v**2, v, np.ones_like(v)],
    'E3 exp+cub  (4)':   lambda v: [v**3, v**2, v, np.ones_like(v)],
    'P1 potencia (2)':   lambda v: [np.log(v), np.ones_like(v)],
    'M1 mixta    (3)':   lambda v: [v, np.log(v), np.ones_like(v)],
    'M2 mixta+c  (4)':   lambda v: [v**2, v, np.log(v), np.ones_like(v)],
}
GEOM = sorted(set(map(tuple, A[:, :2])))

def datos(g, vmax=1.0):
    m = (A[:,0]==g[0]) & (A[:,1]==g[1]) & (A[:,2]<=vmax+1e-9)
    v, s = A[m,2], np.abs(A[m,4])
    u = s > 1e-6
    return v[u], s[u]

print('  error relativo medio, ajuste en log, 21 puntos por geometria\n')
print('  %-18s' % 'familia' + ''.join('%9s' % ('%.2f/%.2f'%g) for g in GEOM[:5]) + '%9s'%'peor')
for nom, f in FAM.items():
    errs = []
    for g in GEOM:
        v, s = datos(g)
        M = np.vstack(f(v)).T
        c,*_ = np.linalg.lstsq(M, np.log(s), rcond=None)
        rel = np.abs(np.exp(M@c) - s)/s
        errs.append(np.sqrt(np.mean(rel**2)))
    print('  %-18s' % nom + ''.join('%9.2f' % (100*e) for e in errs[:5])
          + '%9.2f' % (100*max(errs)))

print('\n  --- curva de aprendizaje (geometria 0.22/0.28, familia E2) ---')
v, s = datos(GEOM[0])
print('  %8s %12s' % ('puntos', 'error[%]'))
for n in (4, 6, 8, 11, 15, 21):
    idx = np.linspace(0, len(v)-1, n).astype(int)
    vv, ss = v[idx], s[idx]
    M = np.vstack(FAM['E2 exp+cuad (3)'](vv)).T
    c,*_ = np.linalg.lstsq(M, np.log(ss), rcond=None)
    # se evalua sobre TODOS los puntos, no solo los usados
    Mt = np.vstack(FAM['E2 exp+cuad (3)'](v)).T
    rel = np.abs(np.exp(Mt@c) - s)/s
    print('  %8d %12.2f' % (n, 100*np.sqrt(np.mean(rel**2))))
