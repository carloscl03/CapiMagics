import numpy as np, subprocess
LD, W9 = 1.60, 0.26
J=['Wd','Wl','Ll','L9']
ORIG=np.array([[0.260,1.796],[0.550,2.699],[0.370,0.620],[0.801,3.781]])
EXT =np.array([[0.260,1.796],[0.300,2.699],[0.280,0.620],[0.801,3.781]])
LO,HI=np.log10(EXT[:,0]),np.log10(EXT[:,1])
rng=np.random.default_rng(404); N=800
G=10**rng.uniform(LO,HI,(N,4)); np.save('siete_geos.npy',G)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
R=[]
for t in range(0,N,200):
    sub=G[t:t+200]
    L=['* caja extendida, Ld=1.60 W9=0.26',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
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
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata s7_%d.dat '%t+' '.join(vec),'.endc','.end']
    open('s7_%d.spice'%t,'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','s7_%d.spice'%t],capture_output=True)
    A=np.loadtxt('s7_%d.dat'%t); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    for i in range(len(sub)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        R.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]),va[k0]])
    print('  trozo %d'%t)
R=np.array(R); np.savez('siete.npz',geos=G,res=R,LD=LD,W9=W9,ext=EXT,orig=ORIG)
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
dentro=np.all((G>=ORIG[:,0])&(G<=ORIG[:,1]),axis=1)
print()
print('%d/%d validas.  %d caen dentro de la caja original'%(ok.sum(),len(R),(ok&dentro).sum()))
X=np.log10(G); u=np.ones(len(G))
def B(Z): return np.column_stack([np.ones(len(Z)),Z]+[Z[:,a]*Z[:,b] for a in range(4) for b in range(a,4)])
Y={'lgIa':np.log10(np.maximum(R[:,0],1e-15)),'lgIb':np.log10(np.maximum(R[:,1],1e-15)),
   'lgG':np.log10(np.maximum(R[:,2],1e-9)),'va':R[:,3]}
rng2=np.random.default_rng(3); ii=np.where(ok)[0]; ii=rng2.permutation(ii)
n=int(.7*len(ii)); tr,te=ii[:n],ii[n:]
print()
print('%-6s %26s %26s'%('salida','EXTERNO en caja EXTENDIDA','EXTERNO solo en la ORIGINAL'))
BB=B(X)
for k,y in Y.items():
    c=np.linalg.lstsq(BB[tr],y[tr],rcond=None)[0]
    f=lambda s: (100*np.abs(10**(BB[s]@c-y[s])-1)).mean() if k!='va' else (100*np.abs((BB[s]@c-y[s])/y[s])).mean()
    td=te[dentro[te]]
    print('%-6s %24.2f%% %25.2f%%'%(k,f(te),f(td) if len(td)>5 else float('nan')))
print()
print('=== la caja extendida da diseños de MENOS AREA a igual especificacion? ===')
ar=G[:,0]*LD+2*G[:,1]*G[:,2]+W9*G[:,3]
for Ia,Gt in [(50e-9,0.30),(100e-9,0.35),(250e-9,0.40)]:
    s=ok&(np.abs(np.log10(R[:,0]/Ia))<0.04)&(np.abs(np.log10(R[:,2]/Gt))<0.04)
    if s.sum()<4: continue
    print('  %5.0f nA G=%.2f (n=%d):  area min extendida %.2f um2   solo dentro de la original %.2f um2'
      %(Ia*1e9,Gt,s.sum(),ar[s].min(),ar[s&dentro].min() if (s&dentro).sum() else float('nan')))
