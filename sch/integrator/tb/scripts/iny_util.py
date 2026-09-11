"""La inyeccion, medida DENSA donde el motor opera de verdad.

La ley actual sale de `iny3.npz`: 200 geometrias aleatorias por W6 0.26-3.98,
L6 0.28-2.0, C 802-19396. Da 4.03 % de LOO ahi. Pero la validacion de 84 puntos
dice que el motor SIEMPRE elige L6 = 2.0, W6 en {0.26, 0.5} y C en {5111,
12000} -- una esquina con poquisimos puntos de apoyo. Y ahi sobreestima dV un
35 %, que se traduce en los -43 mV de sesgo en vm.

Mismo remedio que con la fuga cuando descubrimos que Iref estaba confundido:
barrer donde el motor opera, no donde heredamos la caja.

Un spike aislado por punto, con vm forzado. Ancho 33 ns (el medido del LIF).
"""
import itertools, subprocess, sys
import numpy as np

W6S = [0.26, 0.35, 0.50, 0.70, 1.00]
L6S = [1.00, 1.40, 2.00, 2.80]
CS  = [3000.0, 5111.0, 8000.0, 12000.0, 18000.0]
GEOS = list(itertools.product(W6S, L6S, CS))
V0S = np.arange(1.00, 2.2501, 0.05)
ANCHO = 33.0

print('=== %d geometrias x %d valores de vm = %d puntos ==='
      % (len(GEOS), len(V0S), len(GEOS)*len(V0S)))
sys.stdout.flush()

DV = np.full((len(GEOS), len(V0S)), np.nan)
for k, v0 in enumerate(V0S):
    L = ['* iny_util', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0']
    vec = []
    for i, (W6, L6, Cf) in enumerate(GEOS):
        p = 'g%d' % i
        L += ['XM6%s vm%s Vext%s avdd avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, L6, W6),
              'C3%s vm%s avss %gf' % (p, p, Cf),
              'VSPK%s Vext%s 0 PULSE(0 3.3 1u 2n 2n %gn 100u)' % (p, p, ANCHO),
              '.ic v(vm%s)=%.4f' % (p, v0)]
        vec.append('v(vm%s)' % p)
    L += ['.control', 'tran 0.5n 1.6u 0.9u uic',
          'wrdata iu.dat ' + ' '.join(vec), '.endc', '.end']
    open('iu.spice', 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', 'iu.spice'], capture_output=True)
    try:
        A = np.loadtxt('iu.dat')
    except Exception:
        print('  V0=%.2f fallo' % v0); continue
    t = A[:, 0]
    for i in range(len(GEOS)):
        vm = A[:, 1 + 2*i]
        a = vm[t < 0.99e-6]
        b = vm[(t > 1.3e-6) & (t < 1.5e-6)]
        if len(a) and len(b):
            DV[i, k] = b.mean() - a[-1]
    if k % 5 == 0:
        print('  V0 = %.2f  (%d/%d)' % (v0, k+1, len(V0S))); sys.stdout.flush()
    np.savez('iny_util.npz', geos=np.array(GEOS), v0=V0S, dv=DV)

np.savez('iny_util.npz', geos=np.array(GEOS), v0=V0S, dv=DV)
n = np.isfinite(DV) & (DV > 0)
print()
print('=== %d puntos con dV > 0 de %d ===' % (n.sum(), DV.size))
print('  dV de %.4f a %.4f mV' % (1000*DV[n].min(), 1000*DV[n].max()))
