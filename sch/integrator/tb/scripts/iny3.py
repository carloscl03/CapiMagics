"""Barrido grande de la inyeccion: 200 geometrias muestreadas al azar.

La curva de aprendizaje del barrido de 60 seguia bajando con grado 3 (235 ->
22 % y sin converger), asi que falta DATO, no modelo. Aqui se muestrea de forma
continua en vez de en rejilla, que para ajustar es mas eficiente.
"""
import subprocess

import numpy as np

rng = np.random.default_rng(321)
N = 200
W6 = 10 ** rng.uniform(np.log10(0.25), np.log10(4.0), N)
L6 = 10 ** rng.uniform(np.log10(0.28), np.log10(2.0), N)
Cf = 10 ** rng.uniform(np.log10(800), np.log10(20000), N)
casos = np.column_stack([W6, L6, Cf])
V0 = (1.00, 1.30, 1.60, 1.80, 1.95, 2.05, 2.15, 2.25, 2.35, 2.45)
out = np.zeros((N, len(V0)))

for k, v0 in enumerate(V0):
    L = ['* inyeccion, barrido grande',
         '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0',
         'VSPK Vext 0 PULSE(0 3.3 0.5u 2n 2n 32n 100u)']
    vec = []; ic = []
    for i in range(N):
        p = 'g%d' % i
        L += ['XM6_%s %svm Vext avdd avss nfet_03v3 L=%.4gu W=%.4gu nf=1'
              % (p, p, L6[i], W6[i]),
              'C%s %svm avss %.5gf' % (p, p, Cf[i])]
        vec.append('v(%svm)' % p); ic.append('v(%svm)=%.3f' % (p, v0))
    L += ['.ic ' + ' '.join(ic), '.control', 'tran 0.1n 0.9u uic',
          'wrdata iny3.dat ' + ' '.join(vec), '.endc', '.end']
    open('iny3.spice', 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', 'iny3.spice'], capture_output=True)
    A = np.loadtxt('iny3.dat'); t = A[:, 0]
    a = int(np.argmin(np.abs(t - 0.45e-6))); b = int(np.argmin(np.abs(t - 0.8e-6)))
    for i in range(N):
        out[i, k] = A[b, 1 + 2 * i] - A[a, 1 + 2 * i]
    print('  v0=%.2f listo' % v0, flush=True)

np.savez('iny3.npz', casos=casos, V0=np.array(V0), dV=out)
print()
print('%d geometrias x %d puntos guardadas' % (N, len(V0)))
