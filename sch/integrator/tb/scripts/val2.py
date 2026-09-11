import numpy as np, subprocess
def corre(W1,L1,W2,L2,Ir,W6,L6,Cf,f_kHz,tfin=200e-6):
    T=1e6/f_kHz*1e-9
    L=['* validacion del mejor','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM2 avss nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'XM6 vm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.5gs)'%T,
       '.ic v(vm)=1.5','.control','tran 4n %g uic'%tfin,'wrdata v2.dat v(vm)','.endc','.end']
    open('v2.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','v2.spice'],capture_output=True)
    A=np.loadtxt('v2.dat'); t=A[:,0]; vm=A[:,1]; m=t>0.85*t.max()
    return vm[m].mean(), vm[m].max()-vm[m].min()
G=(1.0,0.28,1.0,1.00,200e-9,0.25,0.28,1000)
pred={268:1.38,400:None,800:None,1500:2.15}
print('MEJOR DISEÑO: L2=1.0u  Iref=200nA  C=1000fF  W6=0.25/0.28')
print('%8s %12s %12s %10s'%('f [kHz]','compuesto','ngspice','rizado'))
vals={}
for f in (268,400,800,1500):
    v,r=corre(*G,f); vals[f]=v
    p=pred.get(f)
    print('%8d %11s %11.3f V %8.0f mV'%(f,('%.3f V'%p) if p else '-',v,1000*r))
s=1000*(vals[1500]-vals[268])/np.log10(1500/268)
print()
print('  sensibilidad medida: %.0f mV/decada   (compuesto decia 1024, original 411)'%s)
