"""Cerro el LOO en W con 8 valores? Criterio fijado ANTES: bajar del 5 %."""
import numpy as np

A = np.load('/tmp/stdp/pot_denso.npz')['filas']
W_G = sorted(set(A[:,0])); L_G = sorted(set(A[:,1]))
FAM = {'E2 (3)': lambda v: [v**2, v, np.ones_like(v)],
       'M1 (3)': lambda v: [v, np.log(v), np.ones_like(v)],
       'E3 (4)': lambda v: [v**3, v**2, v, np.ones_like(v)]}

def curva(w, l):
    m = (A[:,0]==w)&(A[:,1]==l); v,s = A[m,2], np.abs(A[m,4])
    u = s>1e-6; return v[u], s[u]

print('  LOO dejando fuera una W entera, 8 valores de W\n')
print('  %8s %-10s %10s %12s %12s' % ('L','familia','LOO[%]','peor W[%]','interno[%]'))
for l in L_G:
    for nom, f in FAM.items():
        C = {}
        for w in W_G:
            v,s = curva(w,l)
            C[w],*_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)
        n = len(C[W_G[0]])
        ei = [np.sqrt(np.mean((np.abs(np.exp(np.vstack(f(curva(w,l)[0])).T@C[w])
              - curva(w,l)[1])/curva(w,l)[1])**2)) for w in W_G]
        el = []
        for fuera in W_G:
            dentro = [w for w in W_G if w != fuera]
            X = np.array([[np.log(w)**2, np.log(w), 1.0] for w in dentro])
            pc = [np.linalg.lstsq(X, np.array([C[w][k] for w in dentro]), rcond=None)[0]
                  @ [np.log(fuera)**2, np.log(fuera), 1.0] for k in range(n)]
            v,s = curva(fuera,l); M = np.vstack(f(v)).T
            el.append(np.sqrt(np.mean((np.abs(np.exp(M@np.array(pc)))-s)**2/s**2)))
        print('  %8.2f %-10s %10.2f %12.2f %12.2f'
              % (l, nom, 100*np.mean(el), 100*max(el), 100*np.mean(ei)))
    print()

print('  --- el suelo como ley en W (deberia cruzar cero) ---')
for l in L_G:
    su = np.array([A[(A[:,0]==w)&(A[:,1]==l)][0,3] for w in W_G])
    X = np.vstack([W_G, np.ones(len(W_G))]).T
    c,*_ = np.linalg.lstsq(X, su, rcond=None)
    rel = np.abs(X@c - su)/np.maximum(np.abs(su),1e-9)
    print('  L=%.2f   suelo = %+.4f %+.4f*W mV   cruza en W=%.3f   err %.2f %%'
          % (l, c[1]*1e3, c[0]*1e3, -c[1]/c[0], 100*np.median(rel)))
