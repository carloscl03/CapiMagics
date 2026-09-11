import numpy as np, subprocess, itertools, json
C=np.load('caja.npz'); G0=C['casos']; LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
def nb(X):
    u=(X-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)
rng=np.random.default_rng(67); GE=[]
while len(GE)<40:
    x=rng.uniform(LO,HI,(1,6))
    if nb(x)[0]<=2: GE.append(x[0])
GE=10**np.array(GE); np.save('esq_geos.npy',GE)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
res={}
for cor,T in itertools.product(COR,TMP):
    L=['* esquina %s %dC'%(cor,T),
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.options temp=%d tnom=27'%T,
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(GE):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    t='e_%s_%d'%(cor,T)
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%t+' '.join(vec),'.endc','.end']
    open(t+'.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',t+'.spice'],capture_output=True)
    A=np.loadtxt(t+'.dat'); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    R=[]
    for i in range(len(GE)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        R.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
    res['%s|%d'%(cor,T)]=np.array(R)
    print('%-8s %4dC  Iex(-) mediana %8.1f nA   G %.3f   V(a) %.0f mV'
      %(cor,T,np.median(np.array(R)[:,0])*1e9,np.median(np.array(R)[:,2]),1000*np.median(np.array(R)[:,3])))
np.savez('esquinas.npz',geos=GE,**{k:v for k,v in res.items()})
