import numpy as np, subprocess
C=np.load('caja.npz'); G0=C['casos']; LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
W9L=[0.22,0.24,0.26,0.28,0.30,0.35]
rng=np.random.default_rng(77); N=120
J=[0,2,3,5]
G=np.zeros((N,4)); G[:]=rng.uniform(LO[J],HI[J],(N,4)); G=10**G
R={}
for w9 in W9L:
    L=['* W9 por debajo del suelo de la caja',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,wl,ll,l9) in enumerate(G):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=1.6u W=%gu %s'%(p,p,p,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=1.6u W=%gu %s'%(p,p,p,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata w9_%s.dat '%str(w9).replace('.','')+' '.join(vec),'.endc','.end']
    f='w9_%s'%str(w9).replace('.','')
    open(f+'.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b',f+'.spice'],capture_output=True,text=True)
    err=[l for l in r.stdout.splitlines() if 'rror' in l or 'valid modelname' in l]
    if err: print('W9=%.2f -> %s'%(w9,err[0][:70])); continue
    A=np.loadtxt(f+'.dat'); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    out=[]
    for i in range(len(G)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        out.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
    R[w9]=np.array(out)
    o=R[w9]; m=o[:,3]>0.15
    print('W9=%.2f um  valido %3d/%d  Iex(-) %6.1f-%7.1f nA  G %.2f-%.2f  V(a) min %3.0f mV  area M9 %.3f um2'
      %(w9,m.sum(),len(o),o[m,0].min()*1e9,o[m,0].max()*1e9,o[m,2].min(),o[m,2].max(),1000*o[m,3].min(),w9*np.median(G[:,3])))
np.savez('w9bajo.npz',geos=G,**{str(k):v for k,v in R.items()})
