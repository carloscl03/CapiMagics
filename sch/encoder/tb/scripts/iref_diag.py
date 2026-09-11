import numpy as np, itertools
D=np.load('iref2.npz'); C=D['geos']; I=D['I']; ok=D['ok']
X=np.log10(C[ok]); y=np.log10(I[ok]); G=C[ok]; n=len(y)
rng=np.random.default_rng(7); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
E=[e for e in itertools.product(range(4),repeat=4) if sum(e)<=3]
B=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
r=100*np.abs(10**(B[te]@c-y[te])-1)
o=np.argsort(-r)[:10]
print('=== los 10 peores de la cubica ===')
print('   Wn    Ln    Wp    Lp   I[uA]   error')
for k in o:
    j=te[k]; print(' %5.2f %5.2f %5.2f %5.2f %7.2f %7.1f%%'%(*G[j],1e6*10**y[j],r[k]))
print()
print('=== error por decada de corriente ===')
lim=[-7,-6,-5,-4,-3.4]
for a,b in zip(lim,lim[1:]):
    m=(y[te]>=a)&(y[te]<b)
    if m.sum(): print('  %6.1f a %5.1f uA  %3d casos  medio %6.2f%%  peor %6.2f%%'%(1e6*10**a,1e6*10**b,m.sum(),r[m].mean(),r[m].max()))
print()
print('=== y si nos quedamos donde importa (consumo bajo, I <= 5 uA)? ===')
for tope,nom in [(5e-6,'I <= 5 uA'),(2e-5,'I <= 20 uA')]:
    s=y<np.log10(tope)
    Xs,ys=X[s],y[s]
    r2=np.random.default_rng(7); i2=r2.permutation(s.sum()); m2=int(.7*s.sum())
    for gr,nm in ((2,'cuadratica'),(3,'cubica')):
        Ee=[e for e in itertools.product(range(gr+1),repeat=4) if sum(e)<=gr]
        Bs=np.column_stack([np.prod(Xs**np.array(e),axis=1) for e in Ee])
        cc=np.linalg.lstsq(Bs[i2[:m2]],ys[i2[:m2]],rcond=None)[0]
        rr=100*np.abs(10**(Bs[i2[m2:]]@cc-ys[i2[m2:]])-1)
        print('  %-10s %-11s %3d muestras %3d coef  %6.2f%%  peor %6.2f%%'%(nom,nm,s.sum(),Bs.shape[1],rr.mean(),rr.max()))
