import numpy as np, subprocess
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
D=np.load('siete.npz'); G=D['geos']
rng=np.random.default_rng(77); sel=rng.choice(len(G),8,replace=False)
N=200
L=['* variacion GLOBAL estadistica del encoder',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.param sw_stat_global=1 sw_stat_mismatch=0',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
   'VIN Vin 0 1.58','VINN Vinn 0 1.72']
vec=[]
for i,j in enumerate(sel):
    wd,wl,ll,l9=G[j]; p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=0.26u %s'%(p,p,l9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
    vec.append('i(vi_%s)'%p)
L+=['.control','set appendwrite','let c=0','dowhile c < %d'%N,'  reset','  op',
    '  wrdata glob.dat '+' '.join(vec),'  let c = c + 1','end','.endc','.end']
open('gl.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['rm','-f','glob.dat'])
subprocess.run(['ngspice','-b','gl.spice'],capture_output=True)
A=np.loadtxt('glob.dat')
if A.ndim==1: A=A.reshape(1,-1)
I=np.abs(A[:,1::2])
print('=== VARIACION GLOBAL (sw_stat_global=1), %d tiradas ==='%len(I))
print()
print('%10s %12s %12s %10s %14s'%('geometria','mediana','sigma','sigma/med','p5-p95'))
for i in range(I.shape[1]):
    y=I[:,i]; y=y[np.isfinite(y)&(y>0)]
    if len(y)<20: continue
    print('%10d %10.1f nA %10.1f nA %9.1f%% %6.2fx-%.2fx'%(i,1e9*np.median(y),1e9*y.std(),100*y.std()/np.median(y),np.percentile(y,5)/np.median(y),np.percentile(y,95)/np.median(y)))
r=I[np.isfinite(I).all(1)]
n=r/np.median(r,axis=0)
print()
print('  dispersion tipica: %.1f%%   (las 5 esquinas del PDK daban un factor 4.5)'%(100*np.median(n.std(0))))
