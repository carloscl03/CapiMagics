import numpy as np, subprocess
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# empujar los tres bordes que suben la ganancia, uno a uno y juntos
casos=[('caja actual (borde)',1.796,0.300,0.620,2.0),
       ('Ll hasta 1.0',       1.796,0.300,1.000,2.0),
       ('Ll hasta 1.5',       1.796,0.300,1.500,2.0),
       ('Wd hasta 3.0',       3.000,0.300,0.620,2.0),
       ('Wl hasta 0.24',      1.796,0.240,0.620,2.0),
       ('los tres',           3.000,0.240,1.500,2.0)]
L=['* alcanzar ganancia alta','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
 'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
vec=[]
for i,(nom,wd,wl,ll,l9) in enumerate(casos):
    p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=0.26u %s'%(p,p,l9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
    vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata ga.dat '+' '.join(vec),'.endc','.end']
open('ga.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','ga.spice'],capture_output=True)
A=np.loadtxt('ga.dat'); vd=A[:,0]
qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
print('=== se puede llegar a ganancia 0.90? ===')
print('%-22s %8s %10s %10s %8s'%('caja','ganancia','Iex(-) nA','razon','V(a) mV'))
for i,(nom,wd,wl,ll,l9) in enumerate(casos):
    ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
    g=float(np.abs(np.gradient(vx)/np.gradient(vd))[k0])
    print('%-22s %8.3f %10.1f %10.1f %8.0f'%(nom,g,ie[qa]*1e9,ie[qb]/max(ie[qa],1e-18),va[k0]*1000))
