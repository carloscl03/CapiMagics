"""Piloto del barrido del integrador sobre la banda que impone la cadena.

Banda: 74 - 4500 kHz, deducida de EncoderSpec -> NeuronSpec (no inventada).
El techo es el limite FISICO del reset del LIF, no un borde de barrido.

Novedad frente a val3.py: AMPERIMETROS. Una fuente de 0 V en serie en cada
camino, que en ngspice es la forma de leer una corriente de rama sin perturbar
el circuito:
    VAMF  en el camino de FUGA      (M2 hacia avss)
    VAMI  en el camino de INYECCION (M6 desde avdd)

Se comprueban dos cosas antes de barrer nada:
  1. que las corrientes leidas cuadran con el balance de carga
  2. que 400 us bastan para llegar al equilibrio a 74 kHz (30 periodos)
"""
import numpy as np, subprocess

def netlist(p, W1, L1, W2, L2, Ir, W6, L6, Cf, f_kHz):
    T = 1e6 / f_kHz * 1e-9
    return ([
      'IREF avdd nref%s %gn' % (p, Ir * 1e9),
      'XM3%s nref%s nref%s avss avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, L2, W2),
      # amperimetro de FUGA: M2 drena a avss a traves de la fuente de 0 V
      'VAMF%s nf%s avss 0' % (p, p),
      'XM2%s nf%s nref%s vg%s avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L2, W2),
      'XM1%s vg%s vg%s vm%s avdd pfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L1, W1),
      # amperimetro de INYECCION: M6 toma de avdd a traves de la fuente de 0 V
      'VAMI%s ni%s avdd 0' % (p, p),
      'XM6%s vm%s Vext%s ni%s avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L6, W6),
      'C3%s vm%s avss %gf' % (p, p, Cf),
      'VSPK%s Vext%s 0 PULSE(0 3.3 5u 2n 2n 32n %.6gs)' % (p, p, T),
      '.ic v(vm%s)=2.0' % p,
    ], ['v(vm%s)' % p, 'i(vamf%s)' % p, 'i(vami%s)' % p])

def corre(casos, tfin=400e-6, vent=20e-6, paso=2e-9):
    L = ['* piloto integrador',
         '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0']
    vec = []
    for i, c in enumerate(casos):
        n, v = netlist('p%d' % i, *c)
        L += n; vec += v
    # tstart: solo se guarda la ventana final -> el .dat no se dispara
    L += ['.control', 'tran %g %g %g uic' % (paso, tfin, tfin - vent),
          'wrdata pil.dat ' + ' '.join(vec), '.endc', '.end']
    open('pil.spice', 'w').write('\n'.join(L) + '\n')
    r = subprocess.run(['ngspice', '-b', 'pil.spice'], capture_output=True, text=True)
    A = np.loadtxt('pil.dat')
    t = A[:, 0]
    return t, A

# --- geometrias del piloto: el original y el mejorado del knowledge base ----
G = [(1.0, 0.28, 1.0, 0.28, 50e-9, 1.0, 0.28, 5111),
     (1.0, 0.28, 1.0, 1.00, 25e-9, 0.25, 1.0, 5111)]
NOM = ['ORIGINAL', 'MEJORADO']
FS = [74, 268, 1000, 2500, 4500]

print('=== piloto: amperimetros y equilibrio, banda 74-4500 kHz ===')
print()
print('  %-9s %7s %9s %8s %11s %11s %9s' %
      ('diseño', 'f[kHz]', 'vm', 'rizado', 'I_fuga', 'I_iny(med)', 'balance'))
for g, nom in zip(G, NOM):
    for f in FS:
        t, A = corre([g + (f,)])
        vm = A[:, 1]; ifg = A[:, 3]; iny = A[:, 5]
        # balance de carga: lo que entra por M6 debe igualar lo que sale por M2
        qi = np.trapezoid(np.abs(iny), t); qf = np.trapezoid(np.abs(ifg), t)
        print('  %-9s %7d %8.3fV %7.0fmV %10.2fnA %10.2fnA %8.1f%%' %
              (nom, f, vm.mean(), 1000 * (vm.max() - vm.min()),
               1e9 * np.abs(ifg).mean(), 1e9 * np.abs(iny).mean(),
               100 * (qi / qf - 1) if qf > 0 else float('nan')))
    print()
