import numpy as np, json, subprocess
M=np.load('modelo_cubico.npz'); EXP=M['exp']; cv=np.load('viabilidad.npy')
D=np.load('mcley.npz'); X=np.log10(D['geos']); y=np.log10(D['sig'])
cs=np.linalg.lstsq(np.column_stack([np.ones(len(X)),X]),y,rcond=None)[0]
C=np.load('caja.npz'); G0=C['casos']; LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
def pr(k,Z): return np.column_stack([np.prod(Z**e,axis=1) for e in EXP])@M[k]
def sig(Z): return 10**(cs[0]+Z@cs[1:])
def nb(Z):
    u=(Z-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)
def P(a,g): return np.column_stack([np.ones(np.size(a)),a,g,a*a,g*g,a*g])
Ia,Gt=100e-9,0.35
Ib=Ia*10**float((P(np.log10([Ia]),np.log10([Gt]))@cv)[0])
rng=np.random.default_rng(41)
POOL=rng.uniform(LO,HI,(400000,6)); POOL=POOL[nb(POOL)<=2]
PA,PB,PG,PV=[pr(k,POOL) for k in ('lgIa','lgIb','gan','va')]
def esp(A,B,Gg,V): return ((A-np.log10(Ia))**2+(B-np.log10(Ib))**2
    +np.log10(np.maximum(Gg,1e-6)/Gt)**2+100*np.maximum(0,0.15-V)**2)
SE=esp(PA,PB,PG,PV)
def area(Z):
    q=10**Z; return q[:,0]*q[:,1]+2*q[:,2]*q[:,3]+q[:,4]*q[:,5]
res=[]
for w in [0.0,0.25,0.5,0.75,1.0]:
    co=300*SE + w*np.log10(area(POOL)) + (1-w)*np.log10(sig(POOL))
    x=POOL[np.argmin(co)].copy(); cb=co.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(35):
            Q=np.clip(x+rng.normal(0,paso,(1500,6)),LO,HI)
            cc=(300*esp(pr('lgIa',Q),pr('lgIb',Q),pr('gan',Q),pr('va',Q))
                +w*np.log10(area(Q))+(1-w)*np.log10(sig(Q))+10.*np.maximum(0,nb(Q)-2)**2)
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],Q[j].copy()
    res.append((w,10**x,float(area(x[None,:])[0]),float(sig(x[None,:])[0]),
        [float(pr(k,x[None,:])[0]) for k in ('lgIa','lgIb','gan','va')]))
json.dump([[w,list(map(float,q))] for w,q,_,_,_ in res],open('pareto2.json','w'))
print('pedido Iex(-)=100 nA G=0.35 -> ley exige Iex(+)=%.1f nA'%(Ib*1e9))
print()
print('%5s %8s %11s %28s'%('w','area','sigma pred','especificacion (modelo)'))
for w,q,ar,sg,(a,b,g,v) in res:
    print('%5.2f %7.2f %10.1f mV   %.1f/%.1f nA G=%.3f  (%+.1f%% %+.1f%% %+.1f%%)'
      %(w,ar,1000*sg,10**a*1e9,10**b*1e9,g,100*(10**a/Ia-1),100*(10**b/Ib-1),100*(g/Gt-1)))
    print('      Wd=%.3f Ld=%.3f Wl=%.3f Ll=%.3f W9=%.3f L9=%.3f'%tuple(q))
