"""Impedancia de salida y capacidad de entrada del integrador, para el motor.

R_OUT se saca de la DERIVADA DE LOS DATOS MEDIDOS (criba2.npz), no de la
derivada de la ley: el polinomio ajusta valores al 7 % pero su pendiente
amplifica el ruido del ajuste -- probado, daba 0.50, 46.03 y 2.15 GOhm al
mover vm, que es absurdo.

    R_out = 1 / (dI_fuga/dvm)

C_IN es la puerta de M6, que el spike del LIF tiene que mover. Medida con .ac.
"""
import itertools, subprocess, sys
import numpy as np

# ---------- R_out, de los datos ----------
D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
msk = C[:, 1] == 0.28
X, Y, G = [], [], []
for j in np.where(msk)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]
    m = (V >= 1.1) & (V <= 2.35) & np.isfinite(y) & (y > 0.3*Ir)
    if m.sum() < 10: continue
    v = V[m]; g = np.gradient(y[m], v)          # dI/dvm de la MEDIDA
    for k in range(len(v)):
        if g[k] > 0:
            X.append([np.log10(W1), np.log10(W2), np.log10(L2), v[k], np.log10(Ir)])
            Y.append(np.log10(1.0/g[k])); G.append(j)
X = np.array(X); Y = np.array(Y); G = np.array(G)
print('=== R_out: %d puntos, %d geometrias ===' % (len(Y), len(set(G))))
print('  rango: %.3f a %.1f GOhm' % (10**Y.min()/1e9, 10**Y.max()/1e9))

E = [e for e in itertools.product(range(3), repeat=5) if sum(e) <= 2]
B = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
gs = np.array(sorted(set(G))); rng = np.random.default_rng(3)
er = []
for f in np.array_split(rng.permutation(gs), 10):
    m = np.isin(G, f)
    c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
    er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
CR = np.linalg.lstsq(B, Y, rcond=None)[0]
print('  cuadratica de %d coef: %.1f %% K-fold por geometria' % (len(CR), np.concatenate(er).mean()))
np.save('cr_out.npy', CR); np.save('cr_out_exp.npy', np.array(E))
print()
print('  contra lo del knowledge base:')
for ir, med in ((5e-9, '1.74-1.82'), (25e-9, '0.37-0.40')):
    z = np.array([0.0, np.log10(2.0), 0.0, 1.8, np.log10(ir)])
    r = 10**sum(k*np.prod(z**np.array(e)) for k, e in zip(CR, E))
    print('    Iref=%2.0fnA  ley %.2f GOhm   KB %s' % (ir*1e9, r/1e9, med))

# ---------- C_in, medida ----------
print()
W6S = [0.26, 0.5, 1.0, 2.0, 4.0]; L6S = [0.28, 0.5, 1.0, 2.0, 4.0]
casos = list(itertools.product(W6S, L6S))
L = ['* C_in', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
     'VDD avdd 0 3.3', 'VSS avss 0 0']
vec = []
for i, (W6, L6) in enumerate(casos):
    p = 'k%d' % i
    L += ['VIN%s %se 0 DC 1.65 AC 1' % (p, p),
          'XM6_%s %sm %se avdd avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, L6, W6),
          'C%s %sm avss 5111f' % (p, p), 'VMM%s %sm 0 2.0' % (p, p)]
    vec.append('i(vin%s)' % p)
L += ['.control', 'ac lin 1 1k 1k',
      'wrdata ci2.dat ' + ' '.join('abs(%s)/(2*3.14159265*1000)' % x for x in vec),
      '.endc', '.end']
open('ci2.spice', 'w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice', '-b', 'ci2.spice'], capture_output=True)
A = np.loadtxt('ci2.dat')
Cin = np.abs(A[1::2]) if A.ndim == 1 else np.abs(A[0, 1::2])
Xc = np.log10(np.array(casos)); Yc = np.log10(Cin)
Bc = np.column_stack([np.ones(len(Yc)), Xc, Xc[:, :1]*Xc[:, 1:2], Xc**2])
CC = np.linalg.lstsq(Bc, Yc, rcond=None)[0]
e = 100*np.abs(10**(Bc@CC - Yc) - 1)
print('=== C_in: %d geometrias, de %.3f a %.2f fF ===' % (len(Cin), 1e15*Cin.min(), 1e15*Cin.max()))
print('  ley de %d coef: %.2f %% medio, %.2f %% peor' % (len(CC), e.mean(), e.max()))
np.save('cc_in.npy', CC)
print('  C_in(0.26, 2.0) = %.3f fF   (la geometria que elige el motor)'
      % (1e15*10**(np.array([1, np.log10(0.26), np.log10(2.0),
                             np.log10(0.26)*np.log10(2.0),
                             np.log10(0.26)**2, np.log10(2.0)**2]) @ CC)))
