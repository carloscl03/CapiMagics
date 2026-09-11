import numpy as np, json, subprocess, itertools
c=np.load('viabilidad.npy'); M=np.load('modelo_cubico.npz'); EXP=M['exp']
C=np.load('caja.npz'); G0=C['casos']; vdc=C['vd']
LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
VA,VB=vdc[int(np.argmin(np.abs(vdc+0.15)))],vdc[int(np.argmin(np.abs(vdc-0.15)))]
def P(a,g): return np.column_stack([np.ones(np.size(a)),a,g,a*a,g*g,a*g])
def Ib_de(Ia,G): return Ia*10**float((P(np.log10([Ia]),np.log10([G]))@c)[0])
def pred(k,X): return np.column_stack([np.prod(X**e,axis=1) for e in EXP])@M[k]
def nb(X):
    u=(X-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)

print('=== 1) la comprobacion atrapa mis 4 pedidos inventados? ===')
for Ia,Ib,G in [(60e-9,180e-9,.35),(80e-9,240e-9,.40),(40e-9,120e-9,.30),(100e-9,300e-9,.45)]:
    q=Ib_de(Ia,G); d=100*(Ib/q-1)
    print('   %5.0f-%3.0f nA G=%.2f -> el circuito exige Ib=%6.1f nA  (pedi %+.0f%%)  %s'
      %(Ia*1e9,Ib*1e9,G,q*1e9,d,'IMPOSIBLE' if abs(d)>5 else 'ok'))

MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
def simular(geos,tag):
    L=['* '+tag,'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(geos):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%tag+' '.join(vec),'.endc','.end']
    open(tag+'.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',tag+'.spice'],capture_output=True)
    A=np.loadtxt(tag+'.dat'); vd=A[:,0]
    qa,qb,q0=[int(np.argmin(np.abs(vd-t))) for t in (VA,VB,0)]
    R=[]
    for i in range(len(geos)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        R.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[q0]),va[q0]])
    return np.array(R)

print()
print('=== 2) EncoderSpec pidiendo solo (Iex_min, ganancia); Ib lo da la ley ===')
rng=np.random.default_rng(77)
PED=[(x,y) for x,y in zip(10**rng.uniform(np.log10(20e-9),np.log10(400e-9),20),
                          rng.uniform(0.26,0.55,20))]
POOL=rng.uniform(LO,HI,(200000,6)); POOL=POOL[nb(POOL)<=2]
PA,PB,PG,PV=[pred(k,POOL) for k in ('lgIa','lgIb','gan','va')]
PEN=100*np.maximum(0,0.15-PV)**2
sol=[]; tgt=[]
for Ia,g in PED:
    Ib=Ib_de(Ia,g); tgt.append((Ia,Ib,g))
    co=(PA-np.log10(Ia))**2+(PB-np.log10(Ib))**2+np.log10(np.maximum(PG,1e-6)/g)**2+PEN
    x=POOL[np.argmin(co)].copy(); cb=co.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(30):
            Q=np.clip(x+rng.normal(0,paso,(1500,6)),LO,HI)
            cc=((pred('lgIa',Q)-np.log10(Ia))**2+(pred('lgIb',Q)-np.log10(Ib))**2
                +np.log10(np.maximum(pred('gan',Q),1e-6)/g)**2
                +100*np.maximum(0,0.15-pred('va',Q))**2+10.*np.maximum(0,nb(Q)-2)**2)
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],Q[j].copy()
    sol.append(x)
got=simular(10**np.array(sol),'viab'); tgt=np.array(tgt)
e=np.column_stack([100*(got[:,0]/tgt[:,0]-1),100*(got[:,1]/tgt[:,1]-1),100*(got[:,2]/tgt[:,2]-1)])
for n,j in [('Iex(-) pedido',0),('Iex(+) por ley',1),('ganancia',2)]:
    v=e[:,j]; print('  %-15s sesgo %+6.2f%%  |error| %5.2f%%  p90 %5.2f%%  peor %6.2f%%'
      %(n,v.mean(),np.abs(v).mean(),np.percentile(np.abs(v),90),np.abs(v).max()))
d=np.abs(e).max(1)
for t in (2,5,10): print('  dentro de +-%2d%% en los tres: %2d/%d'%(t,(d<t).sum(),len(d)))
