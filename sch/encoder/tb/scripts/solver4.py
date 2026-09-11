import numpy as np, json, itertools
M=np.load('modelo_cubico.npz'); EXP=M['exp']
G=np.load('caja.npz')['casos']; LO,HI=np.log10(G.min(0)),np.log10(G.max(0))
def pred(k,X): return np.column_stack([np.prod(X**e,axis=1) for e in EXP])@M[k]
def nborde(X):
    u=(X-LO)/(HI-LO); return (np.minimum(u,1-u)<0.05).sum(1)
PED=[(60e-9,180e-9,0.35),(80e-9,240e-9,0.40),(40e-9,120e-9,0.30),(100e-9,300e-9,0.45)]
rng=np.random.default_rng(3)
def coste(X,Ia,Ib,g):
    e =(pred('lgIa',X)-np.log10(Ia))**2+(pred('lgIb',X)-np.log10(Ib))**2
    e+=np.log10(np.maximum(pred('gan',X),1e-6)/g)**2
    e+=100*np.maximum(0,0.15-pred('va',X))**2
    e+=10.0*np.maximum(0,nborde(X)-2)**2          # <-- quedarse donde hay dato
    return e
sal=[]
for Ia,Ib,g in PED:
    X=rng.uniform(LO,HI,(150000,6)); c=coste(X,Ia,Ib,g)
    x=X[np.argmin(c)].copy(); cb=c.min()
    for paso in [0.05,0.015,0.005,0.0015]:
        for _ in range(40):
            C=np.clip(x+rng.normal(0,paso,(2000,6)),LO,HI); cc=coste(C,Ia,Ib,g)
            j=int(np.argmin(cc))
            if cc[j]<cb: cb,x=cc[j],C[j].copy()
    q=10**x; a,b,gg,v=[float(pred(k,x[None,:])[0]) for k in ('lgIa','lgIb','gan','va')]
    print('%5.0f-%3.0f G=%.3f -> %6.1f-%5.1f G=%.3f (%+.1f%% %+.1f%% %+.1f%%) V(a)=%.0f mV  borde=%d'
      %(Ia*1e9,Ib*1e9,g,10**a*1e9,10**b*1e9,gg,100*(10**a/Ia-1),100*(10**b/Ib-1),
        100*(gg/g-1),1000*v,nborde(x[None,:])[0]))
    print('   Wd=%.3f Ld=%.3f Wl=%.3f Ll=%.3f W9=%.3f L9=%.3f'%tuple(q))
    sal.append([Ia,Ib,g]+list(q)+[10**a,10**b,gg,v])
json.dump(sal,open('spec_test3.json','w'))
