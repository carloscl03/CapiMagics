"""Cribado v2: añade los L2 que el barrido de banda usa de verdad.

v1 tenia L2 en {0.28, 1, 4, 10} y el barrido de banda usa {0.28, 0.5, 1, 2}.
Los 0.5 y 2.0 los estaba INTERPOLANDO sin haberlos medido, justo en el rango
donde el motor opera.

Y `L2 = 0.28` vuelve a entrar: solo el 19 % de esas geometrias "espeja", pero
el SEGUNDO MEJOR diseño del barrido de banda lo usa (resolucion 18.58). Filtrar
por "el espejo espeja" era importar una expectativa del circuito en vez de
mirar si la celda cumple su funcion.
"""
import itertools, subprocess, sys
import numpy as np

W1S = [0.5, 1.0, 2.0, 4.0]
L1S = [0.28, 1.0, 4.0]
W2S = [0.5, 1.0, 2.0, 4.0]
L2S = [0.28, 0.5, 1.0, 2.0, 4.0, 10.0]      # 0.5 y 2.0 son nuevos
IRS = [5e-9, 12e-9, 25e-9, 50e-9, 100e-9]
casos = list(itertools.product(W1S, L1S, W2S, L2S, IRS))
print('%d geometrias' % len(casos)); sys.stdout.flush()

V, I = None, []
B = 240
for k0 in range(0, len(casos), B):
    blo = casos[k0:k0+B]
    L = ['* criba2', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0', 'VM vm 0 1.0']
    vec = []
    for i, (W1, L1, W2, L2, Ir) in enumerate(blo):
        p = 'b%d' % i
        L += ['I%s avdd %sref %gn' % (p, p, Ir*1e9),
              'XM3_%s %sref %sref avss avss nfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,L2,W2),
              'XM2_%s avss %sref %svg avss nfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,L2,W2),
              'XM1_%s %svg %svg %ss avdd pfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,p,L1,W1),
              'VAM%s vm %ss 0' % (p, p)]
        vec.append('i(vam%s)' % p)
    L += ['.control', 'dc VM 0.90 2.45 0.025', 'wrdata c2.dat ' + ' '.join(vec), '.endc', '.end']
    open('c2.spice', 'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice', '-b', 'c2.spice'], capture_output=True)
    A = np.loadtxt('c2.dat')
    V = A[:, 0]; I.append(np.abs(A[:, 1::2]))
    print('  %d/%d' % (min(k0+B, len(casos)), len(casos))); sys.stdout.flush()
I = np.hstack(I)
np.savez('criba2.npz', v=V, I=I, casos=np.array(casos))
print('guardado criba2.npz: %s' % (I.shape,))
