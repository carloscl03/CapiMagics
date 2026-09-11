import numpy as np, itertools
D=np.load('iref2.npz'); C=D['geos']; I=D['I']; ok=D['ok']
X=np.log10(C[ok]); y=np.log10(I[ok]); n=len(y)
rng=np.random.default_rng(7); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
def prueba(nom,Z,grado):
    E=[e for e in itertools.product(range(grado+1),repeat=Z.shape[1]) if sum(e)<=grado]
    B=np.column_stack([np.prod(Z**np.array(e),axis=1) for e in E])
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    r=100*np.abs(10**(B[te]@c-y[te])-1)
    print('  %-38s %4d coef  %7.2f%%  peor %6.2f%%'%(nom,B.shape[1],r.mean(),r.max()))
    return r.mean(),B.shape[1]
print('=== busqueda de colapso: 4 variables -> 2 formas? ===')
S=np.column_stack([X[:,0]-X[:,1], X[:,2]-X[:,3]])   # lg(Wn/Ln), lg(Wp/Lp)
for g in (2,3,4,5,6):
    prueba('colapso (Wn/Ln, Wp/Lp)  grado %d'%g,S,g)
print()
print('  control, sin colapsar:')
for g in (3,4):
    prueba('4 variables  grado %d'%g,X,g)
print()
# residuo del colapso: depende de algo mas?
E=[e for e in itertools.product(range(5),repeat=2) if sum(e)<=4]
B=np.column_stack([np.prod(S**np.array(e),axis=1) for e in E])
c=np.linalg.lstsq(B,y,rcond=None)[0]; res=y-B@c
print('  residuo del colapso (grado 4) contra cada variable, correlacion:')
for i,nm in enumerate(['Wn','Ln','Wp','Lp']):
    print('     %-3s  %+.3f'%(nm,np.corrcoef(X[:,i],res)[0,1]))
print('     rms residuo: %.4f decadas'%res.std())
