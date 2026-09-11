"""Colapso por el TECHO: cada geometria se anula a su propia tension."""
import numpy as np, itertools
J=np.load('iny3.npz'); C=J['casos']; V0=J['V0']; dV=J['dV']
# techo por caso: raiz de dV(v0), interpolando entre el ultimo positivo y el negativo
tech=np.full(len(C),np.nan)
for i in range(len(C)):
    d=dV[i]; f=np.isfinite(d)
    for k in range(len(V0)-1):
        if f[k] and f[k+1] and d[k]>0 and d[k+1]<=0:
            tech[i]=V0[k]+(V0[k+1]-V0[k])*d[k]/(d[k]-d[k+1]); break
    else:
        if f.sum()>=3 and (d[f]>0).all():          # no llega a cruzar: extrapola
            p=np.polyfit(V0[f][-3:],d[f][-3:],1)
            if p[0]<0: tech[i]=-p[1]/p[0]
ok=np.isfinite(tech)&(tech>1.5)&(tech<4.0)
print('=== el techo, caso por caso ===')
print('  estimado en %d de %d casos, de %.3f a %.3f V'%(ok.sum(),len(C),tech[ok].min(),tech[ok].max()))
Xt=np.log10(C[ok]); yt=np.log10(tech[ok])
rng=np.random.default_rng(5); it=rng.permutation(ok.sum()); nt=int(.7*ok.sum())
for nm,gr in [('potencia',1),('cuadratica',2),('cubica',3)]:
    E=[e for e in itertools.product(range(gr+1),repeat=3) if sum(e)<=gr]
    B=np.column_stack([np.prod(Xt**np.array(e),axis=1) for e in E])
    c=np.linalg.lstsq(B[it[:nt]],yt[it[:nt]],rcond=None)[0]
    r=100*np.abs(10**(B[it[nt:]]@c-yt[it[nt:]])-1)
    print('  ley del techo, %-11s %2d coef  externo %.2f%%'%(nm,B.shape[1],r.mean()))
print()
# --- ahora la inyeccion en la variable colapsada -------------------------
X=[];Y=[]
for i in np.where(ok)[0]:
    for k,v0 in enumerate(V0):
        d=dV[i,k]
        if np.isfinite(d) and d>1e-4 and v0<tech[i]-0.02:
            X.append([np.log10(C[i,0]),np.log10(C[i,1]),np.log10(C[i,2]),
                      np.log10(tech[i]-v0)]); Y.append(d)
X=np.array(X); y=np.log10(np.array(Y)); n=len(y)
print('=== inyeccion con la variable colapsada  u = lg10(techo - vm) ===')
print('  %d muestras'%n)
r2=np.random.default_rng(6); idx=r2.permutation(n); nt2=int(.7*n); tr,te=idx[:nt2],idx[nt2:]
print('  %-34s %6s %9s'%('forma','coef','externo'))
for nm,gr in [('potencia            (1,1,1,1)',(1,1,1,1)),
              ('cuadratica          (2,2,2,2)',(2,2,2,2)),
              ('cubica              (3,3,3,3)',(3,3,3,3)),
              ('cuartica            (4,4,4,4)',(4,4,4,4))]:
    E=[e for e in itertools.product(*[range(g+1) for g in gr]) if sum(e)<=max(gr)]
    B=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    r=100*np.abs(10**(B[te]@c-y[te])-1)
    print('  %-34s %6d %8.2f%%'%(nm,B.shape[1],r.mean()))
