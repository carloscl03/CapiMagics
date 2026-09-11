"""La inyeccion, restringida a la ventana util (sin ceros). Competencia de formas."""
import numpy as np, itertools
J=np.load('iny3.npz'); C=J['casos']; V0=J['V0']; dV=J['dV']
X=[];Y=[]
for i in range(len(C)):
    for k,v0 in enumerate(V0):
        if v0>2.25: continue                 # ventana util: sin ceros
        d=dV[i,k]
        if np.isfinite(d) and d>1e-5:
            X.append([np.log10(C[i,0]),np.log10(C[i,1]),np.log10(C[i,2]),v0]); Y.append(d)
X=np.array(X); y=np.log10(np.array(Y))
n=len(y); print('=== inyeccion en la ventana util (V0 <= 2.25) ===')
print('  %d muestras, dV de %.4f a %.4f V (%.1f decadas), CERO ceros'
      %(n,10**y.min(),10**y.max(),y.max()-y.min()))
rng=np.random.default_rng(5); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
def ext(gr):
    E=[e for e in itertools.product(*[range(g+1) for g in gr]) if sum(e)<=max(gr)]
    B=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
    if B.shape[1]>=nt: return B.shape[1],float('nan')
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    r=100*np.abs(10**(B[te]@c-y[te])-1)
    return B.shape[1],r.mean()
print()
print('  %-34s %6s %9s'%('forma','coef','externo'))
for nm,gr in [('potencia            (1,1,1,1)',(1,1,1,1)),
              ('cuadratica          (2,2,2,2)',(2,2,2,2)),
              ('cubica              (3,3,3,3)',(3,3,3,3)),
              ('cuartica            (4,4,4,4)',(4,4,4,4)),
              ('quintica            (5,5,5,5)',(5,5,5,5)),
              ('cubica en geom, quintica en vm',(3,3,3,5))]:
    c,e=ext(gr); print('  %-34s %6d %8.2f%%'%(nm,c,e))
print()
print('  (para comparar: sobre TODO el rango, incluidos los ceros, la P5 de 126')
print('   terminos daba 4.14 % y la mejor familia corta 11.36 %)')
