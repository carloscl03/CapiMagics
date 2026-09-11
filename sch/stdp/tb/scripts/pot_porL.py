"""Una ley en W para cada L, en vez de una superficie en (W,L).

El LOO sobre el plano da 30 % con las cuatro familias y con termino de
interaccion. Pero la estructura medida dice que los ejes son casi
independientes: `L` gobierna suavidad/senal y `W` gobierna senal/suelo.

Si el LOO en W (a L fija) es bueno, entonces `L` no es una variable continua
de la ley sino una ELECCION DISCRETA del motor, con una ley en W para cada
valor. Es una salida legitima: el motor elige L de una lista corta.
"""
import numpy as np

A = np.load('/tmp/stdp/nucleo_pot.npz')['filas']
W_G = sorted(set(A[:, 0])); L_G = sorted(set(A[:, 1]))
f = lambda v: [v**2, v, np.ones_like(v)]              # E2

def curva(w, l):
    m = (A[:,0]==w) & (A[:,1]==l)
    v, s = A[m,2], np.abs(A[m,4])
    u = s > 1e-6
    return v[u], s[u]

print('  LOO dejando fuera una W entera, con L FIJA\n')
print('  %8s %10s %12s %12s' % ('L', 'LOO[%]', 'peor W[%]', 'interno[%]'))
for l in L_G:
    C = {}
    for w in W_G:
        v, s = curva(w, l)
        C[w],*_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)
    ei, el = [], []
    for w in W_G:
        v, s = curva(w, l); M = np.vstack(f(v)).T
        ei.append(np.sqrt(np.mean((np.abs(np.exp(M@C[w])-s)/s)**2)))
    for fuera in W_G:
        dentro = [w for w in W_G if w != fuera]
        X = np.array([[np.log(w)**2, np.log(w), 1.0] for w in dentro])
        pc = [np.linalg.lstsq(X, np.array([C[w][k] for w in dentro]), rcond=None)[0]
              @ [np.log(fuera)**2, np.log(fuera), 1.0] for k in range(3)]
        v, s = curva(fuera, l); M = np.vstack(f(v)).T
        el.append(np.sqrt(np.mean((np.abs(np.exp(M@np.array(pc))-s)/s)**2)))
    print('  %8.2f %10.2f %12.2f %12.2f'
          % (l, 100*np.mean(el), 100*max(el), 100*np.mean(ei)))

print('\n  --- y al reves: LOO dejando fuera una L entera, con W fija ---')
print('  %8s %10s %12s' % ('W', 'LOO[%]', 'peor L[%]'))
for w in W_G:
    C = {}
    for l in L_G:
        v, s = curva(w, l)
        C[l],*_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)
    el = []
    for fuera in L_G:
        dentro = [l for l in L_G if l != fuera]
        X = np.array([[np.log(l)**2, np.log(l), 1.0] for l in dentro])
        pc = [np.linalg.lstsq(X, np.array([C[l][k] for l in dentro]), rcond=None)[0]
              @ [np.log(fuera)**2, np.log(fuera), 1.0] for k in range(3)]
        v, s = curva(w, fuera); M = np.vstack(f(v)).T
        el.append(np.sqrt(np.mean((np.abs(np.exp(M@np.array(pc))-s)/s)**2)))
    print('  %8.2f %10.2f %12.2f' % (w, 100*np.mean(el), 100*max(el)))
