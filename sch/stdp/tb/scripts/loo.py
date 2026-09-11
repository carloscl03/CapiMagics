"""Validacion POR GEOMETRIA entera (LOO), no por punto.

Separar puntos al azar deja puntos de la misma geometria a los dos lados: la
ley solo tiene que interpolar en `Vdep`, que es lo facil, y el error sale
optimista. Aqui se deja fuera una geometria ENTERA y se predice sin haberla
visto -- que es lo que le pedira el motor.

Para eso los coeficientes de la familia tienen que depender de (W4, L4): se
ajusta cada coeficiente con una ley de potencia en W y L.
"""
import numpy as np
from itertools import product

A = np.load('/tmp/stdp/nucleo.npz')['filas']
FAM = {
    'E2 (3)': lambda v: [v**2, v, np.ones_like(v)],
    'M1 (3)': lambda v: [v, np.log(v), np.ones_like(v)],
    'E3 (4)': lambda v: [v**3, v**2, v, np.ones_like(v)],
}
GEOM = sorted(set(map(tuple, A[:, :2])))

def curva(g):
    m = (A[:,0]==g[0]) & (A[:,1]==g[1])
    v, s = A[m,2], np.abs(A[m,4])
    u = s > 1e-6
    return v[u], s[u]

print('  LOO por geometria: se deja fuera una entera y se predice\n')
print('  %-10s %12s %12s %12s' % ('familia', 'medio[%]', 'peor geom[%]', 'peor pto[%]'))
for nom, f in FAM.items():
    # 1) coeficientes de cada geometria
    C = {}
    for g in GEOM:
        v, s = curva(g)
        M = np.vstack(f(v)).T
        C[g], *_ = np.linalg.lstsq(M, np.log(s), rcond=None)
    ncoef = len(next(iter(C.values())))
    errs, peor = [], 0.0
    for fuera in GEOM:
        dentro = [g for g in GEOM if g != fuera]
        # 2) cada coeficiente como ley de potencia en W y L
        X = np.array([[np.log(g[0]), np.log(g[1]), 1.0] for g in dentro])
        pred_c = []
        for k in range(ncoef):
            y = np.array([C[g][k] for g in dentro])
            b, *_ = np.linalg.lstsq(X, y, rcond=None)
            pred_c.append(b @ [np.log(fuera[0]), np.log(fuera[1]), 1.0])
        # 3) evaluar en la geometria no vista
        v, s = curva(fuera)
        M = np.vstack(f(v)).T
        rel = np.abs(np.exp(M @ np.array(pred_c)) - s)/s
        e = np.sqrt(np.mean(rel**2)); errs.append(e); peor = max(peor, rel.max())
    print('  %-10s %12.2f %12.2f %12.2f'
          % (nom, 100*np.mean(errs), 100*max(errs), 100*peor))

print('\n  --- y el error INTERNO de la misma familia, para comparar ---')
for nom, f in FAM.items():
    errs = []
    for g in GEOM:
        v, s = curva(g)
        M = np.vstack(f(v)).T
        c,*_ = np.linalg.lstsq(M, np.log(s), rcond=None)
        errs.append(np.sqrt(np.mean((np.abs(np.exp(M@c)-s)/s)**2)))
    print('  %-10s %12.2f' % (nom, 100*np.mean(errs)))
