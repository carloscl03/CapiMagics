"""Cribado ancho de la fuga, con Iref CRUZADO de verdad.

El barrido viejo fijaba Iref=50 nA en su malla y solo lo movia sobre UNA linea de
geometria (12 puntos de 93). Por eso la ley falla hasta un 12 % en L2=0.28 con
Iref lejos de 50 nA -- que es justo donde opera nuestro barrido de la banda.

Aqui se cruza entero. Es DC, o sea barato: el A/B demostro que C3 y M6 no
cambian nada (0.00 % en todas las geometrias y en todo vm), asi que no hace
falta transitorio para la fuga.

Este es el CRIBADO, no la caracterizacion: sirve para decidir en que rango
caracterizar y no gastar coeficientes en zonas que el motor no va a tocar.
"""
import numpy as np, subprocess, itertools, json

W1S = [0.5, 1.0, 2.0, 4.0]
L1S = [0.28, 1.0, 4.0, 10.0]
W2S = [0.5, 1.0, 2.0, 4.0]
L2S = [0.28, 1.0, 4.0, 10.0]
IRS = [5e-9, 12e-9, 25e-9, 50e-9, 100e-9, 200e-9]
casos = [c for c in itertools.product(W1S, L1S, W2S, L2S, IRS)]
print('%d geometrias (cruce completo, Iref incluido)' % len(casos))

V, I = None, []
B = 200
for k0 in range(0, len(casos), B):
    blo = casos[k0:k0+B]
    L = ['* criba','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3','VSS avss 0 0','VM vm 0 1.0']
    vec = []
    for i, (W1,L1,W2,L2,Ir) in enumerate(blo):
        p = 'b%d' % i
        L += ['I%s avdd %sref %gn' % (p,p,Ir*1e9),
              'XM3_%s %sref %sref avss avss nfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,L2,W2),
              'XM2_%s avss %sref %svg avss nfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,L2,W2),
              'XM1_%s %svg %svg %ss avdd pfet_03v3 L=%gu W=%gu nf=1' % (p,p,p,p,L1,W1),
              'VAM%s vm %ss 0' % (p,p)]
        vec.append('i(vam%s)' % p)
    L += ['.control','dc VM 0.90 2.45 0.025','wrdata cr.dat ' + ' '.join(vec),'.endc','.end']
    open('cr.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','cr.spice'], capture_output=True)
    A = np.loadtxt('cr.dat')
    V = A[:, 0]
    I.append(np.abs(A[:, 1::2]))
    print('  %d/%d' % (min(k0+B, len(casos)), len(casos)), flush=True)
I = np.hstack(I)
C = np.array(casos)
np.savez('criba.npz', v=V, I=I, casos=C)
print()
print('=== que hace el espejo? ===')
k15 = int(np.argmin(np.abs(V-1.5))); k24 = int(np.argmin(np.abs(V-2.4)))
rat = I[k15, :] / C[:, 4]
pla = I[k24, :] / np.maximum(I[k15, :], 1e-18)
print('  I(1.5V)/Iref :  p10 %.3f  mediana %.3f  p90 %.3f' %
      (np.percentile(rat,10), np.median(rat), np.percentile(rat,90)))
print('  I(2.4)/I(1.5):  p10 %.3f  mediana %.3f  p90 %.3f' %
      (np.percentile(pla,10), np.median(pla), np.percentile(pla,90)))
print()
print('=== cuantas geometrias espejan de verdad (0.9 < I/Iref < 1.15)? ===')
ok = (rat > 0.9) & (rat < 1.15)
print('  %d de %d  (%.0f%%)' % (ok.sum(), len(casos), 100*ok.mean()))
for j, nm in enumerate(['W1','L1','W2','L2','Iref']):
    vals = sorted(set(C[:, j]))
    s = '  '.join('%g:%.0f%%' % (v, 100*ok[C[:, j] == v].mean()) for v in vals)
    print('   %-5s %s' % (nm, s))
