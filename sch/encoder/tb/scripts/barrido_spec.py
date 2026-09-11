import numpy as np, json, subprocess, itertools
M=np.load('modelo_cubico.npz'); EXP=M['exp']
C=np.load('caja.npz'); G0=C['casos']; vdc=C['vd']
LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
ka,kb,k0=[int(np.argmin(np.abs(vdc-t))) for t in (-0.15,0.15,0)]
VA,VB=vdc[ka],vdc[kb]                       # los Vdif REALES del modelo
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
WO,LO_=0.93,1.86
def base(X): return np.column_stack([np.prod(X**e,axis=1) for e in EXP])
def pred(k,X): return base(X)@M[k]
def nborde(X):
    u=(X-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)

def simular(geos,tag):
    L=['* barrido '+tag,'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
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
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,LO_,WO,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%tag+' '.join(vec),'.endc','.end']
    open(tag+'.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',tag+'.spice'],capture_output=True)
    A=np.loadtxt(tag+'.dat'); vd=A[:,0]
    qa,qb,q0=[int(np.argmin(np.abs(vd-t))) for t in (VA,VB,0)]
    assert abs(vd[qa]-VA)<1e-9 and abs(vd[qb]-VB)<1e-9, 'malla distinta'
    R=[]
    for i in range(len(geos)):
        ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
        R.append([ie[qa],ie[qb],float(np.abs(np.gradient(vx)/np.gradient(vd))[q0]),va[q0]])
    return np.array(R)

# ---- 1) 40 geometrias nuevas -> pedidos alcanzables y no vistos ----
rng=np.random.default_rng(101); P=[]
while len(P)<40:
    x=rng.uniform(LO,HI,(1,6))
    if nborde(x)[0]<=2: P.append(x[0])
P=np.array(P); ref=simular(10**P,'ped')
ok=(ref[:,3]>0.15)&(ref[:,0]>1e-9)&np.isfinite(ref).all(1)
P,ref=P[ok],ref[ok]
print('%d pedidos validos (V(a)>150mV)'%len(P))
print('   rango Iex(-): %.1f - %.1f nA'%(ref[:,0].min()*1e9,ref[:,0].max()*1e9))
print('   rango Iex(+): %.1f - %.1f nA'%(ref[:,1].min()*1e9,ref[:,1].max()*1e9))
print('   rango G     : %.3f - %.3f'%(ref[:,2].min(),ref[:,2].max()))

# ---- 2) resolver cada pedido (pool precalculado, comun a todos) ----
POOL=rng.uniform(LO,HI,(200000,6))
PA,PB,PG,PV,PN=pred('lgIa',POOL),pred('lgIb',POOL),pred('gan',POOL),pred('va',POOL),nborde(POOL)
PEN=100*np.maximum(0,0.15-PV)**2+10.0*np.maximum(0,PN-2)**2
sol=[]
for Ia,Ib,g,_ in ref:
    c=(PA-np.log10(Ia))**2+(PB-np.log10(Ib))**2+np.log10(np.maximum(PG,1e-6)/g)**2+PEN
    x=POOL[np.argmin(c)].copy(); cb=c.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(30):
            Q=np.clip(x+rng.normal(0,paso,(1500,6)),LO,HI)
            cc=((pred('lgIa',Q)-np.log10(Ia))**2+(pred('lgIb',Q)-np.log10(Ib))**2
                +np.log10(np.maximum(pred('gan',Q),1e-6)/g)**2
                +100*np.maximum(0,0.15-pred('va',Q))**2+10.0*np.maximum(0,nborde(Q)-2)**2)
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],Q[j].copy()
    sol.append(x)
sol=np.array(sol)

# ---- 3) simular las soluciones ----
got=simular(10**sol,'sol')
np.savez('barrido_spec.npz',ped=P,ref=ref,sol=sol,got=got)
e=np.column_stack([100*(got[:,0]/ref[:,0]-1),100*(got[:,1]/ref[:,1]-1),100*(got[:,2]/ref[:,2]-1)])
print()
print('=== BARRIDO: %d pedidos, PEDIDO vs LOGRADO (ambos en ngspice) ==='%len(P))
for n,j in [('Iex(-)',0),('Iex(+)',1),('ganancia',2)]:
    v=e[:,j]; print('  %-9s sesgo %+6.2f%%  |error| medio %5.2f%%  p90 %5.2f%%  peor %6.2f%%'
        %(n,v.mean(),np.abs(v).mean(),np.percentile(np.abs(v),90),np.abs(v).max()))
d=np.abs(e).max(1)
for t in (2,5,10,20):
    print('  pedidos con los 3 objetivos dentro de +-%2d%%: %2d/%d (%.0f%%)'%(t,(d<t).sum(),len(d),100*(d<t).mean()))
print('  V(a) logrado: %.0f - %.0f mV'%(got[:,3].min()*1000,got[:,3].max()*1000))
