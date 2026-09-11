"""Cuanto tarda el integrador en asentarse? MEDIDO, no supuesto.

Un solo transitorio largo con paso grueso: no resuelve el pulso de 32 ns pero
si la envolvente de vm, que es lo unico que hace falta para ver cuando deja de
derivar. Con eso se dimensiona el barrido grande en vez de adivinarlo.
"""
import numpy as np, subprocess, os, sys

def envolvente(g, f_kHz, tfin, paso=20e-9, tag='a'):
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    T = 1e6/f_kHz*1e-9
    sp, dat = 'as_%s.spice'%tag, 'as_%s.dat'%tag
    L=['* asiento','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'VAMF nf avss 0',
       'XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'VAMI ni avdd 0',
       'XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.8gs)'%T,
       '.ic v(vm)=2.0','.control','tran %g %g uic'%(paso,tfin),
       'wrdata %s v(vm)'%dat,'.endc','.end']
    open(sp,'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',sp],capture_output=True)
    A=np.loadtxt(dat); return A[:,0], A[:,1]

G=(1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111)     # el ORIGINAL
print('=== cuanto tarda en asentarse? (ORIGINAL, el caso lento) ===')
for f,tfin in ((74,900e-6),(4500,120e-6)):
    T=1e6/f*1e-9
    t,vm=envolvente(G,f,tfin,tag='f%d'%f)
    print()
    print('  f = %d kHz   periodo %.2f us   simulados %.0f us = %.0f periodos'
          %(f,T*1e6,tfin*1e6,(tfin-5e-6)/T))
    print('    %10s %10s %12s'%('t [us]','vm [V]','falta [mV]'))
    vfin=vm[t>0.95*t.max()].mean()
    for frac in (0.05,0.1,0.2,0.3,0.5,0.7,0.9,1.0):
        k=t<=frac*t.max()
        if k.sum()<10: continue
        w=(t>max(0,(frac-0.05)*t.max()))&k
        print('    %10.0f %10.4f %12.2f'%(t[k][-1]*1e6, vm[w].mean(), 1000*(vm[w].mean()-vfin)))
    # cuando entra y se queda dentro de 1 mV
    per=np.arange(5e-6,tfin,T)
    for p0 in per:
        w=(t>=p0)&(t<p0+2*T)
        if w.sum()>5 and abs(vm[w].mean()-vfin)<1e-3:
            print('    -> dentro de 1 mV desde t = %.0f us = %.0f periodos'
                  %(p0*1e6,(p0-5e-6)/T)); break
