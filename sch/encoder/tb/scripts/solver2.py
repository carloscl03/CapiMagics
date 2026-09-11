import numpy as np, json, itertools
d=np.load('caja.npz'); vb=d['vbias']; vd=d['vd']; G=d['casos']
jb=int(np.argmin(np.abs(vb-1.2)))
ka=int(np.argmin(np.abs(vd+0.15))); kb=int(np.argmin(np.abs(vd-0.15))); k0=int(np.argmin(np.abs(vd)))
iex=np.abs(d['iex'][:,jb,:]); vx=d['vx'][:,jb,:]; va=d['va'][:,jb,:]
dV=np.gradient(vd)
Y={'lgIa':np.log10(iex[:,ka]), 'lgIb':np.log10(iex[:,kb]),
   'gan':np.abs(np.gradient(vx,axis=1)/dV)[:,k0], 'va':va[:,k0]}
X=np.log10(G)                                    # 6 dims en log

# --- base polinomica cubica completa en 6 variables (84 terminos) ---
EXP=[e for e in itertools.product(range(4),repeat=6) if sum(e)<=3]
def base(X):
    return np.column_stack([np.prod(X**np.array(e),axis=1) for e in EXP])
B=base(X)
print('%d geometrias, %d terminos cubicos' % (len(X),B.shape[1]))

# --- validacion externa: 70/30, semilla fija ---
rng=np.random.default_rng(7); idx=rng.permutation(len(X))
tr,te=idx[:840],idx[840:]
CO={}
print()
print('%6s %14s %14s' % ('','ajuste (train)','externo (test)'))
for k,y in Y.items():
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    def err(s):
        r=B[s]@c-y[s]
        return (100*np.abs(10**r-1)).mean() if k.startswith('lg') else (100*np.abs(r/y[s])).mean()
    print('%6s %13.2f%% %13.2f%%' % (k,err(tr),err(te)))
    CO[k]=np.linalg.lstsq(B,y,rcond=None)[0]   # final: todo el dato
np.savez('modelo_cubico.npz',**CO,exp=np.array(EXP))
