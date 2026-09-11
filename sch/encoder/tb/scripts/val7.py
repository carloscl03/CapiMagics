import numpy as np, subprocess, itertools
D=np.load('siete.npz'); GE=D['geos']; R=D['res']; LD=float(D['LD']); W9=float(D['W9'])
J=[0,1,2,3]
m=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(GE[m]); LO,HI=X.min(0),X.max(0)
EXPC=[e for e in __import__("itertools").product(range(4),repeat=4) if sum(e)<=3]
def B(Z): return np.column_stack([np.prod(Z**np.array(e),axis=1) for e in EXPC])
CO={k:np.linalg.lstsq(B(X),y,rcond=None)[0] for k,y in
    [('lgIa',np.log10(R[m,0])),('lgIb',np.log10(R[m,1])),('lgG',np.log10(R[m,2])),('va',R[m,3])]}
pr=lambda k,Z: B(Z)@CO[k]
# --- 25 pedidos alcanzables: geometrias nuevas simuladas ---
rng=np.random.default_rng(202)
pass
NG=10**rng.uniform(LO,HI,(25,4))
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
def sim(geos,tag):
    L=['* '+tag,'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,wl,ll,l9) in enumerate(geos):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%tag+' '.join(vec),'.endc','.end']
    open(tag+'.spice','w').write('\n'.join(L)+'\n'); subprocess.run(['ngspice','-b',tag+'.spice'],capture_output=True)
    A=np.loadtxt(tag+'.dat'); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    return np.array([[np.abs(A[:,1+2*(3*i)])[qa],np.abs(A[:,1+2*(3*i)])[qb],
        float(np.abs(np.gradient(A[:,1+2*(3*i+1)])/np.gradient(vd))[k0]),A[:,1+2*(3*i+2)][k0]] for i in range(len(geos))])
ped=sim(NG,'p4'); ok=(ped[:,3]>0.15)&(ped[:,0]>0); ped=ped[ok]
print('%d pedidos alcanzables, Iex(-) de %.1f a %.1f nA'%(ok.sum(),ped[:,0].min()*1e9,ped[:,0].max()*1e9))
POOL=rng.uniform(LO,HI,(250000,4))
PA,PB,PG,PV=[pr(k,POOL) for k in ('lgIa','lgIb','lgG','va')]
sol=[]
for Ia,Ib,g,_ in ped:
    co=(PA-np.log10(Ia))**2+(PB-np.log10(Ib))**2+(PG-np.log10(g))**2+100*np.maximum(0,0.15-PV)**2
    x=POOL[np.argmin(co)].copy(); cb=co.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(30):
            Q=np.clip(x+rng.normal(0,paso,(1500,4)),LO,HI)
            cc=((pr('lgIa',Q)-np.log10(Ia))**2+(pr('lgIb',Q)-np.log10(Ib))**2
                +(pr('lgG',Q)-np.log10(g))**2+100*np.maximum(0,0.15-pr('va',Q))**2)
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],Q[j].copy()
    sol.append(x)
S=np.array(sol)
got=sim(10**S,'s4')
e=np.column_stack([100*(got[:,0]/ped[:,0]-1),100*(got[:,1]/ped[:,1]-1),100*(got[:,2]/ped[:,2]-1)])
print()
print('=== LAZO CERRADO EN 4 VARIABLES (pedido y logrado, ambos en ngspice) ===')
for n,j in [('Iex(-)',0),('Iex(+)',1),('ganancia',2)]:
    v=e[:,j]; print('  %-9s sesgo %+6.2f%%  |error| %5.2f%%  p90 %5.2f%%  peor %6.2f%%'
      %(n,v.mean(),np.abs(v).mean(),np.percentile(np.abs(v),90),np.abs(v).max()))
d=np.abs(e).max(1)
for t in (2,5,10): print('  con los 3 dentro de +-%2d%%: %2d/%d'%(t,(d<t).sum(),len(d)))
