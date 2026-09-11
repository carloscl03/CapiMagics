import numpy as np, subprocess
def corre(W1,L1,W2,L2,Ir,W6,L6,Cf,f_kHz,tfin=350e-6):
    T=1e6/f_kHz*1e-9
    L=['* validacion directa','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM2 avss nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'XM6 vm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.5gs)'%T,
       '.ic v(vm)=1.5','.control','tran 4n %g uic'%tfin,'wrdata val.dat v(vm)','.endc','.end']
    open('val.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','val.spice'],capture_output=True)
    A=np.loadtxt('val.dat'); t=A[:,0]; vm=A[:,1]
    m=t>0.85*t.max()
    return vm[m].mean(), vm[m].max()-vm[m].min()
print('%-22s %8s %12s %12s %10s'%('diseño','f [kHz]','compuesto','ngspice','error'))
pred={('orig',268):2.183,('orig',800):2.407,('mej',268):1.649,('mej',800):1.909}
for nom,g in [('original',(1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111)),
              ('L2=1u + M6 0.25/1.0',(1.0,0.28,1.0,1.00,50e-9,0.25,1.0,5111))]:
    k='orig' if nom=='original' else 'mej'
    for f in (268,800):
        v,riz=corre(*g,f)
        p=pred[(k,f)]
        print('%-22s %8d %11.3f V %11.3f V %9.1f%%   rizado %.0f mV'%(nom,f,p,v,100*(v/p-1),1000*riz))
