import numpy as np, subprocess, json
C=np.load('caja.npz'); G0=C['casos']; LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
med=(LO+HI)/2
LD=10**med[1]; W9=10**med[4]
print('fijados: Ld=%.3f um   W9=%.3f um'%(LD,W9))
J=[0,2,3,5]                      # Wd, Wl, Ll, L9
rng=np.random.default_rng(88); N=800
GE=np.zeros((N,6)); GE[:,1]=med[1]; GE[:,4]=med[4]
GE[:,J]=rng.uniform(LO[J],HI[J],(N,4))
GE=10**GE; np.save('cuatro_geos.npy',GE)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
TROZO=200; R=[]
for t in range(0,N,TROZO):
    sub=GE[t:t+TROZO]
    L=['* barrido de 4 variables (Ld y W9 fijos)',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(sub):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata c4_%d.dat '%t+' '.join(vec),'.endc','.end']
    open('c4_%d.spice'%t,'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','c4_%d.spice'%t],capture_output=True)
    A=np.loadtxt('c4_%d.dat'%t); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    for i in range(len(sub)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        R.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
    print('  trozo %d listo'%t)
R=np.array(R); np.savez('cuatro.npz',geos=GE,res=R,LD=LD,W9=W9)
m=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(GE[m][:,J]); NOM=['Wd','Wl','Ll','L9']
Y={'lgIa':np.log10(R[m,0]),'lgIb':np.log10(R[m,1]),'lgG':np.log10(R[m,2]),'va':R[m,3]}
rng2=np.random.default_rng(3); idx=rng2.permutation(m.sum()); n=int(.7*m.sum()); tr,te=idx[:n],idx[n:]
u=np.ones(m.sum())
B1=np.column_stack([u,X])
B2=np.column_stack([u,X]+[X[:,a]*X[:,b] for a in range(4) for b in range(a,4)])
print()
print('%d geometrias validas.  Leyes en 4 variables:'%m.sum())
print('%-6s %10s %10s %10s'%('salida','terminos','ajuste','EXTERNO'))
for k,y in Y.items():
    for nom,B in [('potencia',B1),('cuadratica',B2)]:
        c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
        f=lambda s: (100*np.abs(10**(B[s]@c-y[s])-1)).mean() if k!='va' else (100*np.abs((B[s]@c-y[s])/y[s])).mean()
        print('%-6s %10d %9.2f%% %9.2f%%'%(k if nom=='potencia' else '',B.shape[1],f(tr),f(te)))
        if nom=='potencia' and k!='va':
            c2=np.linalg.lstsq(B,y,rcond=None)[0]
            print('       %s = %+.3f %s'%(k,c2[0],' '.join('%+.3f lg%s'%(v,n_) for v,n_ in zip(c2[1:],NOM))))
