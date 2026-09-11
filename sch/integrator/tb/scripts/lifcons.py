import numpy as np, subprocess
def corre(Iex_nA,tfin=40e-6):
    L=['* consumo de la neurona v3','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD vdd 0 3.3','VSS vss 0 0','IEX vdd Iin %gn'%Iex_nA,
       'M1 spike_neg Iin vdd vdd pfet_03v3 L=0.28u W=0.5u nf=1',
       'M2 spike_neg Iin vss vss nfet_03v3 L=0.28u W=0.5u nf=1',
       'M3 spike_reset spike_neg vdd vdd pfet_03v3 L=0.28u W=0.5u nf=1',
       'M4 spike_reset spike_neg vss vss nfet_03v3 L=0.28u W=0.5u nf=1',
       'M7 spike spike_neg vdd vdd pfet_03v3 L=0.28u W=0.5u nf=1',
       'M8 spike spike_neg vss vss nfet_03v3 L=0.28u W=0.5u nf=1',
       'M5 Iin spike_reset vss vss nfet_03v3 L=50u W=2.3u nf=1',
       'C2 Iin vss 280f',
       '.control','tran 1n %g'%tfin,'wrdata lc.dat i(vdd) v(spike)','.endc','.end']
    open('lc.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','lc.spice'],capture_output=True)
    A=np.loadtxt('lc.dat'); t=A[:,0]; i=np.abs(A[:,1]); sp=A[:,3]
    m=t>0.3*t.max()
    n=len(np.where(np.diff((sp[m]>1.65).astype(int))>0)[0])
    f=n/(t[m].max()-t[m].min())
    return np.mean(i[m]), f
print('=== NEURONA v3: consumo medio ===')
print('%10s %14s %12s %14s'%('Iex [nA]','f [kHz]','I media [nA]','de la cual Iex'))
for Iex in (50,100,300):
    im,f=corre(Iex)
    print('%10d %13.0f %12.1f %13.0f%%'%(Iex,f*1e-3,1e9*im,100*Iex/(1e9*im)))
