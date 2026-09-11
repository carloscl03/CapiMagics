import numpy as np
A = np.load('/tmp/stdp/pot_denso.npz')['filas']
W_G = sorted(set(A[:,0])); L_G = sorted(set(A[:,1]))
f = lambda v: [v**3, v**2, v, np.ones_like(v)]      # E3

print('# ley del nucleo de POTENCIACION')
print('# `L` es DISCRETA (LOO dejando fuera una L entera: 43-47 %, peor 140 %);')
print('# dentro de cada L, ley continua en W. Vtr = 3.3 - vpot, en [0.70, 1.30].')
print('# LOO por geometria 3.5-5.2 %')
print()
su = np.array([A[(A[:,0]==w)&(A[:,1]==L_G[0])][0,3] for w in W_G])
c,*_ = np.linalg.lstsq(np.vstack([W_G, np.ones(len(W_G))]).T, su, rcond=None)
print('# el suelo NO depende de L (identico a 4 cifras en las tres)')
print('SUELO_POT = (%+.6e, %+.6e)   # suelo[V] = a*W1 + b ; cruza en W=%.3f'
      % (c[0], c[1], -c[1]/c[0]))
print()
print('NUCLEO_POT = {   # por cada L: 4 coef, cada uno cuadratica en ln(W)')
for l in L_G:
    C = {}
    for w in W_G:
        m = (A[:,0]==w)&(A[:,1]==l); v,s = A[m,2], np.abs(A[m,4])
        u = s>1e-6
        C[w],*_ = np.linalg.lstsq(np.vstack(f(v[u])).T, np.log(s[u]), rcond=None)
    X = np.array([[np.log(w)**2, np.log(w), 1.0] for w in W_G])
    B = [np.linalg.lstsq(X, np.array([C[w][k] for w in W_G]), rcond=None)[0]
         for k in range(4)]
    print('  %.2f: (' % l)
    for k, nom in enumerate(('V^3', 'V^2', 'V  ', '1  ')):
        print('      (%+.6e, %+.6e, %+.6e),   # c_%s' % (*B[k], nom))
    print('  ),')
print('}')
print()
print('# comprobacion en el punto nominal W1=0.55, L1=0.80')
l, w = 0.80, 0.55
C = {}
for ww in W_G:
    m = (A[:,0]==ww)&(A[:,1]==l); v,s = A[m,2], np.abs(A[m,4])
    u = s>1e-6
    C[ww],*_ = np.linalg.lstsq(np.vstack(f(v[u])).T, np.log(s[u]), rcond=None)
X = np.array([[np.log(x)**2, np.log(x), 1.0] for x in W_G])
B = [np.linalg.lstsq(X, np.array([C[x][k] for x in W_G]), rcond=None)[0] for k in range(4)]
lw = np.log(w); cc = [b[0]*lw*lw+b[1]*lw+b[2] for b in B]
for tr in (0.85, 1.00, 1.15, 1.30):
    p = np.exp(cc[0]*tr**3 + cc[1]*tr**2 + cc[2]*tr + cc[3])
    m = (A[:,0]==w)&(A[:,1]==l)
    med = np.abs(A[m][np.argmin(np.abs(A[m][:,2]-tr))][4])
    print('#   Vtr=%.2f  ley %8.2f mV   medido %8.2f mV   %+.1f %%'
          % (tr, p*1e3, med*1e3, 100*(p-med)/med))
