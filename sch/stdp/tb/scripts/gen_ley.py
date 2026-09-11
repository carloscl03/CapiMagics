"""Coeficientes finales de la ley del nucleo, y su forma legible."""
import numpy as np

A = np.load('/tmp/stdp/nucleo_w.npz')['filas']
W_G = sorted(set(A[:, 0]))
f = lambda v: [v, np.log(v), np.ones_like(v)]        # M1

C = {}
for w in W_G:
    m = A[:, 0] == w
    v, s = A[m, 2], np.abs(A[m, 4])
    u = s > 1e-6
    C[w], *_ = np.linalg.lstsq(np.vstack(f(v[u])).T, np.log(s[u]), rcond=None)

X = np.array([[np.log(w)**2, np.log(w), 1.0] for w in W_G])
B = [np.linalg.lstsq(X, np.array([C[w][k] for w in W_G]), rcond=None)[0]
     for k in range(3)]
su = np.array([A[A[:, 0] == w][0, 3] for w in W_G])
cs, *_ = np.linalg.lstsq(np.vstack([W_G, np.ones(len(W_G))]).T, su, rcond=None)

print('# ley del nucleo de la depresion, L(M4) = 0.28 um fijo')
print('# valida para W4 en [%.2f, %.2f] um y Vdep en [0.50, 1.00] V' % (W_G[0], W_G[-1]))
print('# LOO por geometria 3.05 %, peor 4.51 %')
print()
print('SUELO_W  = (%+.6e, %+.6e)      # suelo[V] = a*W4 + b' % (cs[0], cs[1]))
print('NUCLEO_W = (')
for k, nom in enumerate(('c_V   ', 'c_logV', 'c_1   ')):
    print('    (%+.6e, %+.6e, %+.6e),   # %s' % (*B[k], nom))
print(')')
print()
print('# def dvw(vdep, w4):')
print('#     s = SUELO_W[0]*w4 + SUELO_W[1]')
print('#     lw = log(w4); c = [b[0]*lw*lw + b[1]*lw + b[2] for b in NUCLEO_W]')
print('#     return s - exp(c[0]*vdep + c[1]*log(vdep) + c[2])')
print()
print('# --- forma corta, en el punto nominal W4 = 0.22 ---')
lw = np.log(0.22)
c = [b[0]*lw*lw + b[1]*lw + b[2] for b in B]
print('#   suelo  = %+.3f mV  %+.3f mV por um de W4' % (cs[1]*1e3, cs[0]*1e3))
print('#   DVw(V) = -exp(%+.3f*V %+.3f*ln(V) %+.3f)   [V]' % (c[0], c[1], c[2]))
for v in (0.60, 0.75, 0.90, 1.00):
    print('#     Vdep=%.2f  ->  %8.2f mV' % (v, -1e3*np.exp(c[0]*v + c[1]*np.log(v) + c[2])))
