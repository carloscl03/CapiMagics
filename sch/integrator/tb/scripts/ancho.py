"""Cuanto depende la inyeccion del ANCHO del spike?

Los 32 ns estan copiados en TODOS mis bancos y nunca los medi: son una
suposicion mia, no un dato de la neurona. Y el LIF tiene F_MAX=4500 kHz porque
"el reset no completa por debajo de ~215 ns", lo que sugiere que su pulso real
es mucho mas ancho.

Si dV depende fuerte del ancho, toda la caracterizacion de la inyeccion esta
hecha con un estimulo que la neurona no produce.
"""
import numpy as np, subprocess

G = [((1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111), 'ORIGINAL  W6=1.0/0.28'),
     ((1.0,0.28,1.0,1.00,25e-9,0.25,1.0,5111), 'MEJORADO  W6=0.25/1.0')]
ANCHOS = [8, 16, 32, 64, 128, 215, 400]

def dv(g, a, vini=1.8):
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    L=['*','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM2 avss nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'XM6 vm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 1u 2n 2n %gn 100u)'%a,
       '.ic v(vm)=%.3f'%vini,'.control','tran 0.2n 2u uic',
       'wrdata an.dat v(vm)','.endc','.end']
    open('an.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','an.spice'], capture_output=True)
    A = np.loadtxt('an.dat'); t = A[:,0]; vm = A[:,1]
    v0 = vm[t < 0.99e-6][-1]
    v1 = vm[(t > 1.5e-6) & (t < 1.6e-6)].mean()
    return 1000*(v1 - v0)

for g, nom in G:
    print('=== %s ===' % nom)
    print('  %10s %12s %12s' % ('ancho[ns]', 'dV [mV]', 'vs 32 ns'))
    b = None
    for a in ANCHOS:
        d = dv(g, a)
        if a == 32:
            b = d
        print('  %10d %11.2f %11s' % (a, d, ('%+.0f%%' % (100*(d/b-1))) if b else ''))
    print()
