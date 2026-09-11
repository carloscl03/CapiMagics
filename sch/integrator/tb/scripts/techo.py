"""El TECHO de la inyeccion, medido de verdad.

QUE SALIO MAL ANTES. Estime el techo de `iny3.npz`, cuya malla de V0 acababa en
2.45 V: 57 de 200 casos NUNCA cruzaban cero dentro de la malla y se
extrapolaban, y el ultimo intervalo era 2.35->2.45, asi que TODOS los techos se
apelotonaban ahi. No medi el techo, medi el borde de mi barrido.

AQUI: se barre V0 hasta 3.25 V (cerca de Vdd) con paso de 50 mV, en lote (todas
las geometrias en un netlist por cada V0). El cruce se interpola entre el ultimo
dV positivo y el primero negativo.

El techo importa por dos cosas:
  - es el limite de lectura de cada geometria (saturacion) -> contrato de
    IntegradorSpec
  - si dV colapsa al reescalar por (techo - vm), la inyeccion tendria forma
    corta en vez de 126 terminos
"""
import itertools, subprocess, sys
import numpy as np

W6S = [0.25, 0.5, 1.0, 2.0]
L6S = [0.28, 0.5, 1.0, 2.0]
CS  = [2000.0, 5111.0, 12000.0]
GEOS = [(w, l, c) for w, l, c in itertools.product(W6S, L6S, CS)]
V0S = np.arange(1.60, 3.2501, 0.05)
ANCHO = 33.0          # ns, el ancho tipico medido del spike del LIF

print('=== techo de la inyeccion: %d geometrias x %d valores de V0 ==='
      % (len(GEOS), len(V0S)))
print('   V0 hasta %.2f V (antes la malla acababa en 2.45 y por eso fallaba)' % V0S[-1])
sys.stdout.flush()

DV = np.full((len(GEOS), len(V0S)), np.nan)
for k, v0 in enumerate(V0S):
    L = ['* techo', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
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
          'wrdata te.dat ' + ' '.join(vec), '.endc', '.end']
    open('te.spice', 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', 'te.spice'], capture_output=True)
    try:
        A = np.loadtxt('te.dat')
    except Exception:
        print('  V0=%.2f fallo' % v0); continue
    t = A[:, 0]
    for i in range(len(GEOS)):
        vm = A[:, 1 + 2*i]
        antes = vm[t < 0.99e-6]
        desp = vm[(t > 1.3e-6) & (t < 1.5e-6)]
        if len(antes) and len(desp):
            DV[i, k] = 1000*(desp.mean() - antes[-1])
    if k % 8 == 0:
        print('  V0 = %.2f V  (%d/%d)' % (v0, k+1, len(V0S))); sys.stdout.flush()

np.savez('techo.npz', geos=np.array(GEOS), v0=V0S, dv=DV)
print()
print('=== el techo, por geometria ===')
print('  %6s %6s %8s %10s %12s' % ('W6', 'L6', 'C[fF]', 'TECHO[V]', 'cruza?'))
tech = np.full(len(GEOS), np.nan)
for i, (W6, L6, Cf) in enumerate(GEOS):
    d = DV[i]; m = np.isfinite(d)
    if m.sum() < 3:
        print('  %6.2f %6.2f %8.0f      sin datos' % (W6, L6, Cf)); continue
    j = np.where((d[:-1] > 0) & (d[1:] <= 0))[0]
    if len(j):
        a = j[0]
        tech[i] = V0S[a] + (V0S[a+1]-V0S[a]) * d[a]/(d[a]-d[a+1])
        print('  %6.2f %6.2f %8.0f %9.3f %12s' % (W6, L6, Cf, tech[i], 'si'))
    else:
        print('  %6.2f %6.2f %8.0f %9s %12s  (dV min %.3f mV)'
              % (W6, L6, Cf, '>%.2f' % V0S[-1], 'NO', np.nanmin(d)))
np.savez('techo.npz', geos=np.array(GEOS), v0=V0S, dv=DV, techo=tech)
n = np.isfinite(tech).sum()
print()
print('  cruzan %d de %d;  techo de %.3f a %.3f V'
      % (n, len(GEOS), np.nanmin(tech), np.nanmax(tech)) if n else '  ninguno cruza')
