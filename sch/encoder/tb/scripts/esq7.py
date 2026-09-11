import numpy as np, subprocess, itertools
LD,W9=1.60,0.26
EXT=np.array([[0.260,1.796],[0.300,2.699],[0.280,0.620],[0.801,3.781]])
LO,HI=np.log10(EXT[:,0]),np.log10(EXT[:,1])
rng=np.random.default_rng(909); N=400
G=10**rng.uniform(LO,HI,(N,4)); np.save('esq7_geos.npy',G)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
res={}
for cor,T in itertools.product(COR,TMP):
    out=[]
    for t in range(0,N,200):
        sub=G[t:t+200]
        L=['* %s %dC'%(cor,T),'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
           '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
           '.options temp=%d tnom=27'%T,
           'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
           'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
        vec=[]
        for i,(wd,wl,ll,l9) in enumerate(sub):
            p='g%d'%i
            L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
                'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
                'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO),
                'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
                'VI_%s %so Vmem 0'%(p,p)]
            vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
        f='e7_%s_%d_%d'%(cor,T,t)
        L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%f+' '.join(vec),'.endc','.end']
        open(f+'.spice','w').write('\n'.join(L)+'\n')
        subprocess.run(['ngspice','-b',f+'.spice'],capture_output=True)
        A=np.loadtxt(f+'.dat'); vd=A[:,0]
        qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
        for i in range(len(sub)):
            ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
            out.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
        subprocess.run(['rm','-f',f+'.dat'])
    res['%s|%d'%(cor,T)]=np.array(out)
    print('  %-8s %4dC  listo'%(cor,T))
np.savez('esquinas7.npz',geos=G,**res)
