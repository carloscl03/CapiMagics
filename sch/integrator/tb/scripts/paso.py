"""El 'fallo' de balance a frecuencia alta, es el circuito o mi paso de tiempo?

A partir de 1200 kHz los que no cierran tienen la MISMA constante de tiempo que
los que si (240 vs 234 us), asi que no es asentamiento. Fallan por poco
(mediana 2.9 %) y el suelo sube con la frecuencia.

Sospecha: 2 ns para resolver un pulso de 32 ns, midiendo cargas cada vez mas
pequenas. Si es eso, al afinar el paso el balance baja y vm/rizado NO cambian:
serian datos buenos con un umbral mal puesto. Si vm o el rizado se mueven, los
datos estan mal y hay que remedir.
"""
import numpy as np, subprocess, banco

R = list(np.load('barrido_banda2.npy', allow_pickle=True))

def corre(g, f, vic, paso):
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    T = 1e6/f*1e-9; nset, nmed = 12, 8
    tfin = T*(1+nset+nmed); vent = T*nmed
    L=['*','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'VAMF nf avss 0','XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'VAMI ni avdd 0','XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,'VSPK Vext 0 PULSE(0 3.3 %.8gs 2n 2n 32n %.8gs)'%(T,T),
       '.ic v(vm)=%.5f'%vic,'.control','tran %g %.8g %.8g uic'%(paso,tfin,tfin-vent),
       'wrdata ps.dat v(vm) i(vamf) i(vami)','.endc','.end']
    open('ps.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','ps.spice'],capture_output=True)
    A=np.loadtxt('ps.dat'); t=A[:,0]; vm=A[:,1]
    Qi=np.trapezoid(A[:,5],t); Qf=np.trapezoid(A[:,3],t)
    return 100*(abs(Qi)/abs(Qf)-1), 1000*(vm.max()-vm.min()), vm.mean()

print('=== afinar el paso: baja el balance? se mueven vm y rizado? ===')
print('  %6s %5s %8s %10s %9s %10s' % ('f[kHz]','caso','paso','balance','rizado','vm'))
for f in (2400, 4500):
    # tres de los que NO cierran
    mal = [r for r in R if r['f'] == f and abs(r['bal']) > 1.5][:3]
    for i, r in enumerate(mal):
        for paso in (2e-9, 5e-10, 2e-10):
            b, rz, v = corre(r['g'], f, r['vm'], paso)
            print('  %6d %5d %7.1fns %9.2f%% %7.2fmV %9.4fV' % (f, i, paso*1e9, b, rz, v))
        print('  %6s %5s %8s %10s %9s %10s' % ('', '', '', '(barrido:', '%.2fmV'%r['riz'], '%.4fV)'%r['vm']))
