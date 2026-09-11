import numpy as np, subprocess
LD,W9=1.60,0.26
EXT=np.array([[0.260,1.796],[0.300,2.699],[0.280,0.620],[0.801,3.781]])
LO,HI=np.log10(EXT[:,0]),np.log10(EXT[:,1])
rng=np.random.default_rng(707); N=300
G=10**rng.uniform(LO,HI,(N,4))
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
L=['* capacidad de entrada del encoder',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
   '* entrada en el centro de la excursion, con AC solo en Vin',
   'VIN  Vin  0 DC 1.65 AC 1','VINN Vinn 0 DC 1.65']
vec=[]
for i,(wd,wl,ll,l9) in enumerate(G):
    p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
L+=['.control','ac lin 1 1k 1k',
    'let cin = abs(i(vin))/(2*3.14159265*1000)',
    'print cin','.endc','.end']
open('cin.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','cin.spice'],capture_output=True,text=True)
val=None
for ln in r.stdout.splitlines():
    t=ln.strip()
    if t.startswith('cin'):
        val=t
print(val[:120] if val else [l for l in r.stdout.splitlines() if 'rror' in l][:3])
