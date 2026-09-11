import numpy as np, itertools
D=np.load('iref2.npz'); C=D['geos']; I=D['I']; ok=D['ok']
X=np.log10(C[ok]); y=np.log10(I[ok]); n=len(y)
rng=np.random.default_rng(7); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
def base(gr):
    E=[e for e in itertools.product(*[range(g+1) for g in gr]) if sum(e)<=max(gr)]
    return np.column_stack([np.prod(X**np.array(e),axis=1) for e in E]),E
print('=== competencia de formas, I_ref (%d muestras, 3.24 decadas) ==='%n)
print('  %-32s %5s %10s %10s'%('forma','coef','EXTERNO','peor'))
best=None
for nom,gr in [('potencia            (1,1,1,1)',(1,1,1,1)),
               ('cuadratica          (2,2,2,2)',(2,2,2,2)),
               ('cuad solo en las L  (1,2,1,2)',(1,2,1,2)),
               ('cubica              (3,3,3,3)',(3,3,3,3)),
               ('cubica solo en L    (1,3,1,3)',(1,3,1,3)),
               ('cuartica            (4,4,4,4)',(4,4,4,4))]:
    B,E=base(gr)
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    r=100*np.abs(10**(B[te]@c-y[te])-1)
    print('  %-32s %5d %9.2f%% %9.2f%%'%(nom,B.shape[1],r.mean(),r.max()))
# curva de aprendizaje de la cubica: dato o modelo?
print()
print('  curva de aprendizaje (cubica, 35 coef):')
B,E=base((3,3,3,3))
for frac in (0.25,0.4,0.55,0.7):
    m=int(frac*n)
    c=np.linalg.lstsq(B[idx[:m]],y[idx[:m]],rcond=None)[0]
    r=100*np.abs(10**(B[te]@c-y[te])-1)
    print('     %3d de entrenamiento -> %.2f%%'%(m,r.mean()))
