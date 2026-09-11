import numpy as np, subprocess
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
D=np.load('siete.npz'); G=D['geos']
rng=np.random.default_rng(55); sel=rng.choice(len(G),40,replace=False)
VC=[1.20,1.40,1.55,1.65,1.75,1.90,2.10]
res={}
for vc in VC:
    L=['* efecto del modo comun','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
       'BP Vin 0 V = %g + 0.5*V(Vdif)'%vc,'BN Vinn 0 V = %g - 0.5*V(Vdif)'%vc]
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
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata vc.dat '+' '.join(vec),'.endc','.end']
    open('vc.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','vc.spice'],capture_output=True)
    A=np.loadtxt('vc.dat'); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    out=[]
    for i in range(len(sel)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        out.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
    res[vc]=np.array(out)
np.savez('vcm.npz',VC=np.array(VC),**{str(k):v for k,v in res.items()},sel=sel)
ref=res[1.65]
print('=== efecto de Vcm sobre las magnitudes del encoder (40 geometrias) ===')
print('%8s %14s %14s %14s %12s'%('Vcm [V]','Iex(-)','Iex(+)','ganancia','V(a) [mV]'))
for vc in VC:
    r=res[vc]; m=np.isfinite(r).all(1)&(ref[:,0]>0)&(r[:,0]>0)
    print('%8.2f %12.3fx %12.3fx %12.3fx %11.0f'%(vc,
      np.median(r[m,0]/ref[m,0]),np.median(r[m,1]/ref[m,1]),np.median(r[m,2]/ref[m,2]),1000*np.median(r[m,3])))
