"""Rejilla explicita en pA, no optimizador.

`minimize_scalar(..., method='bounded')` con xatol=1e-5 sobre un rango de 1e-10
no itera: devuelve el primer sondeo de la seccion aurea. Daba +26.39 pA en los
seis casos, incluido uno donde EMPEORA el error de 4.1 % a 24.9 %. Colo porque
26.4 pA coincidia con mi cuenta a mano.
"""
import numpy as np

CU = 54.5e-15
G = np.linspace(-20e-12, 120e-12, 2801)      # paso de 50 fA

for lado, sg in (('dep', -1.0), ('pot', 1.0)):
    A = np.load('L2_%s.npz' % lado)['filas']
    vb, nc, ii, med, esp = A.T
    C = nc * CU

    def peor(f, m=None):
        m = np.ones(len(ii), bool) if m is None else m
        return np.abs(sg * (ii[m] + f) / C[m] / med[m] - 1).max()

    e = np.array([peor(f) for f in G])
    f = G[e.argmin()]
    e0 = np.abs(sg * ii / C / med - 1)
    e1 = np.abs(sg * (ii + f) / C / med - 1)
    print('%s: fuga %+7.2f pA | peor %5.1f %% -> %4.1f %% | mediana %4.1f %% -> %4.1f %%'
          % (lado, f * 1e12, 100 * e0.max(), 100 * e1.max(),
             100 * np.median(e0), 100 * np.median(e1)))

    # LA PRUEBA de que es fisica: cada capacidad por separado debe pedir la
    # misma fuga. Si cada una pide la suya, es un apano.
    for c in sorted(set(nc)):
        m = nc == c
        ec = np.array([peor(f, m) for f in G])
        print('      nC %d solo -> %+7.2f pA   (peor %4.1f %% -> %4.1f %%)'
              % (c, G[ec.argmin()] * 1e12,
                 100 * np.abs(sg * ii[m] / C[m] / med[m] - 1).max(),
                 100 * ec.min()))
