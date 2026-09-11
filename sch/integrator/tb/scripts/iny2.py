"""Barrido fino de la inyeccion, con puntos DENSOS cerca del techo.

El barrido anterior tenia 5 puntos de vm (1.0 a 2.6) y la interpolacion se
rompia justo donde la curva se dobla, cerca del techo. Aqui 10 puntos, mas
juntos arriba, y mas valores de L6 (que es quien mueve el techo).
"""
import subprocess

import numpy as np

casos = []
for W6 in (0.25, 0.5, 1.0, 2.0, 4.0):
    for L6 in (0.28, 0.5, 1.0, 2.0):
        for Cf in (1000, 5111, 20000):
            casos.append((W6, L6, Cf))
V0 = (1.00, 1.30, 1.60, 1.80, 1.95, 2.05, 2.15, 2.25, 2.35, 2.45)
out = np.zeros((len(casos), len(V0)))

for k, v0 in enumerate(V0):
    L = ['* inyeccion fina',
         '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0',
         'VSPK Vext 0 PULSE(0 3.3 0.5u 2n 2n 32n 100u)']
    vec = []; ic = []
    for i, (W6, L6, Cf) in enumerate(casos):
        p = 'g%d' % i
        L += ['XM6_%s %svm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, L6, W6),
              'C%s %svm avss %gf' % (p, p, Cf)]
        vec.append('v(%svm)' % p); ic.append('v(%svm)=%.3f' % (p, v0))
    L += ['.ic ' + ' '.join(ic), '.control', 'tran 0.1n 0.9u uic',
          'wrdata iny2.dat ' + ' '.join(vec), '.endc', '.end']
    open('iny2.spice', 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', 'iny2.spice'], capture_output=True)
    A = np.loadtxt('iny2.dat'); t = A[:, 0]
    a = int(np.argmin(np.abs(t - 0.45e-6))); b = int(np.argmin(np.abs(t - 0.8e-6)))
    for i in range(len(casos)):
        out[i, k] = A[b, 1 + 2 * i] - A[a, 1 + 2 * i]
    print('  v0=%.2f listo' % v0)

np.savez('iny2.npz', casos=np.array(casos), V0=np.array(V0), dV=out)
print()
print('%d geometrias x %d puntos de vm' % (len(casos), len(V0)))
print()
print('=== el techo, por L6 (donde el salto se anula) ===')
for L6 in (0.28, 0.5, 1.0, 2.0):
    te = []
    for i, (W6, L6i, Cf) in enumerate(casos):
        if L6i != L6:
            continue
        d = out[i]
        m = d > 0.002
        if m.sum() >= 2:
            p = np.polyfit(np.array(V0)[m], d[m], 1)
            te.append(-p[1] / p[0])
    if te:
        print('  L6 = %.2f um  ->  techo %.3f +- %.3f V' % (L6, np.mean(te), np.std(te)))
