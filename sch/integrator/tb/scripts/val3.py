import numpy as np, subprocess
def corre(W1,L1,W2,L2,Ir,W6,L6,Cf,f_kHz,tfin=400e-6):
    T=1e6/f_kHz*1e-9
    L=['* validacion final','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM2 avss nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'XM6 vm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.5gs)'%T,
       '.ic v(vm)=2.0','.control','tran 4n %g uic'%tfin,'wrdata v3.dat v(vm)','.endc','.end']
    open('v3.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','v3.spice'],capture_output=True)
    A=np.loadtxt('v3.dat'); t=A[:,0]; vm=A[:,1]; m=t>0.85*t.max()
    return vm[m].mean(), vm[m].max()-vm[m].min()
print('%-34s %8s %10s %9s'%('diseño','f [kHz]','vm ngspice','rizado'))
R={}
for nom,G in [('ORIGINAL  W6=1.0/0.28 Iref=50n',(1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111)),
              ('MEJOR     W6=0.25/1.0 Iref=25n',(1.0,0.28,1.0,1.00,25e-9,0.25,1.0,5111))]:
    vs={}
    for f in (268,1500):
        v,r=corre(*G,f); vs[f]=(v,r)
        print('%-34s %8d %9.3f V %7.0f mV'%(nom,f,v,1000*r))
    s=1000*(vs[1500][0]-vs[268][0])/np.log10(1500/268)
    rz=1000*max(vs[268][1],vs[1500][1])
    R[nom]=(s,rz)
    print('%-34s %8s sensibilidad %.0f mV/dec, rizado %.0f mV -> RESOL %.1f'%('',' ',s,rz,s/rz))
    print()
a=R['ORIGINAL  W6=1.0/0.28 Iref=50n']; b=R['MEJOR     W6=0.25/1.0 Iref=25n']
print('MEJORA REAL en resolucion: %.1fx'%((b[0]/b[1])/(a[0]/a[1])))
