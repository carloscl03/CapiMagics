import numpy as np, subprocess
CAB='''* integrador: respuesta a tren de spikes reales (32 ns)
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.subckt integ Vext avdd avss I_50n vm
XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1
XM6 vm Vext avdd avss nfet_03v3 L=0.28u W=1u nf=1
XM2 avss I_50n vg avss nfet_03v3 L=0.28u W=1u nf=1
XM3 I_50n I_50n avss avss nfet_03v3 L=0.28u W=1u nf=1
C3 vm avss 5111f
.ends
VDD avdd 0 3.3
VSS avss 0 0
IREF avdd nref 50n
X1 Vext avdd avss nref vm integ
'''
res=[]
for f_kHz in (25,50,100,200,400,800,1500):
    T=1e3/f_kHz*1e-9      # periodo en s
    fin=max(300e-6, 40*T)
    L=[CAB,'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.4gs)'%T,
       '.control','tran %.4g %.4g'%(min(T/40,20e-9),fin),
       'wrdata b.dat v(vm)','.endc','.end']
    open('b.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','b.spice'],capture_output=True)
    A=np.loadtxt('b.dat'); t=A[:,0]; vm=A[:,1]
    fin_m=t>0.8*t.max()
    res.append((f_kHz,vm[fin_m].mean(),vm[fin_m].max()-vm[fin_m].min(),vm[t<5e-6].mean()))
    print('%6d kHz  vm estacionario %.4f V   rizado %5.1f mV   (reposo %.4f)'%(f_kHz,res[-1][1],1000*res[-1][2],res[-1][3]))
np.save('barrido.npy',np.array(res))
