import numpy as np, subprocess
def corre(Ir,f_kHz,tfin=600e-6):
    T=1e6/f_kHz*1e-9
    L=['* suelo de corriente, validacion','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%Ir,
       'XM3 nref nref avss avss nfet_03v3 L=1.0u W=1u nf=1',
       'XM2 avss nref vg avss nfet_03v3 L=1.0u W=1u nf=1',
       'XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1',
       'XM6 vm Vext avdd avss nfet_03v3 L=1.0u W=0.25u nf=1',
       'C3 vm avss 5111f','VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.5gs)'%T,
       '.ic v(vm)=2.05','.control','tran 6n %g uic'%tfin,'wrdata v4.dat v(vm)','.endc','.end']
    open('v4.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','v4.spice'],capture_output=True)
    A=np.loadtxt('v4.dat'); t=A[:,0]; vm=A[:,1]; m=t>0.85*t.max()
    return vm[m].mean(), vm[m].max()-vm[m].min()
print('%9s %8s %11s %10s %11s'%('Iref [nA]','f [kHz]','vm ngspice','rizado','compuesto'))
pred={(12,268):1.987,(12,1500):2.163,(25,268):1.789,(25,1500):2.122}
R={}
for ir in (12,25):
    vs={}
    for f in (268,1500):
        v,r=corre(ir,f); vs[f]=(v,r)
        print('%9d %8d %10.3f V %8.0f mV %10.3f V'%(ir,f,v,1000*r,pred[(ir,f)]))
    s=1000*(vs[1500][0]-vs[268][0])/np.log10(1500/268); rz=1000*max(vs[268][1],vs[1500][1])
    R[ir]=(s,rz); print('%9s %8s sensibilidad %.0f mV/dec, rizado %.0f mV -> RESOL %.1f'%('','',s,rz,s/rz))
print()
print('  el ORIGINAL medido antes: 180 mV/dec, rizado 71 mV, RESOL 2.5, con 50 nA')
