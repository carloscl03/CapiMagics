import numpy as np, json
M=np.load('modelo_cubico.npz'); EXP=M['exp']; cv=np.load('viabilidad.npy')
C=np.load('caja.npz'); G0=C['casos']; LO,HI=np.log10(G0.min(0)),np.log10(G0.max(0))
def pr(k,X): return np.column_stack([np.prod(X**e,axis=1) for e in EXP])@M[k]
def nb(X):
    u=(X-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)
def P(a,g): return np.column_stack([np.ones(np.size(a)),a,g,a*a,g*g,a*g])
Ia,Gt=100e-9,0.35
Ib=Ia*10**float((P(np.log10([Ia]),np.log10([Gt]))@cv)[0])
print('pedido: Iex(-)=%.0f nA  G=%.2f  ->  la ley exige Iex(+)=%.1f nA'%(Ia*1e9,Gt,Ib*1e9))
rng=np.random.default_rng(31)
POOL=rng.uniform(LO,HI,(400000,6)); POOL=POOL[nb(POOL)<=2]
PA,PB,PG,PV=[pr(k,POOL) for k in ('lgIa','lgIb','gan','va')]
def espec(A,B,Gg,V):
    return ((A-np.log10(Ia))**2+(B-np.log10(Ib))**2+np.log10(np.maximum(Gg,1e-6)/Gt)**2
            +100*np.maximum(0,0.15-V)**2)
def sec(X):
    q=10**X; ar=q[:,0]*q[:,1]+2*q[:,2]*q[:,3]+q[:,4]*q[:,5]
    return np.log10(ar), np.log10(q[:,0]*q[:,1])
SE=espec(PA,PB,PG,PV); LA,LP=sec(POOL)
sal=[]
for w in [0.0,0.2,0.4,0.6,0.8,1.0]:
    co=300*SE + w*LA - (1-w)*LP
    x=POOL[np.argmin(co)].copy(); cb=co.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(35):
            Q=np.clip(x+rng.normal(0,paso,(1500,6)),LO,HI)
            se=espec(pr('lgIa',Q),pr('lgIb',Q),pr('gan',Q),pr('va',Q))
            la,lp=sec(Q); cc=300*se+w*la-(1-w)*lp+10.*np.maximum(0,nb(Q)-2)**2
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],Q[j].copy()
    q=10**x; ar=q[0]*q[1]+2*q[2]*q[3]+q[4]*q[5]; pa=q[0]*q[1]
    a,b,g,v=[float(pr(k,x[None,:])[0]) for k in ('lgIa','lgIb','gan','va')]
    print('w=%.1f  area %.2f um2  par WdLd %.3f um2   modelo %.1f/%.1f nA G=%.3f V(a)=%.0f mV  (esp %+.1f%% %+.1f%% %+.1f%%)'
      %(w,ar,pa,10**a*1e9,10**b*1e9,g,1000*v,100*(10**a/Ia-1),100*(10**b/Ib-1),100*(g/Gt-1)))
    print('        Wd=%.3f Ld=%.3f Wl=%.3f Ll=%.3f W9=%.3f L9=%.3f'%tuple(q))
    sal.append(list(map(float,q)))
json.dump({'Ia':Ia,'Ib':Ib,'G':Gt,'geos':sal},open('pareto.json','w'))
