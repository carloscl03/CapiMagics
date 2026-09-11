import numpy as np, itertools
D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok]); n=ok.sum()
y=np.log10(R[ok,0])
rng=np.random.default_rng(11); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
def err(E):
    B=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    return len(E),(100*np.abs(10**(B[te]@c-y[te])-1)).mean()
TODOS=[e for e in itertools.product(range(4),repeat=4) if sum(e)<=3]
puro=lambda e: sum(1 for k in e if k)<=1
grado=lambda e: sum(e)
fam=[('constante + lineal',                  [e for e in TODOS if grado(e)<=1]),
     ('+ curvatura propia, SIN cruces',       [e for e in TODOS if puro(e)]),
     ('lineal + cruces de 2, SIN curvatura',  [e for e in TODOS if grado(e)<=1 or (grado(e)==2 and not puro(e))]),
     ('cuadratica completa',                  [e for e in TODOS if grado(e)<=2]),
     ('cuadratica + cruces triples',          [e for e in TODOS if grado(e)<=2 or (grado(e)==3 and sum(1 for k in e if k)==3)]),
     ('CUBICA COMPLETA',                      TODOS)]
print('=== de que vive la precision de lg Iex(-)?  (cada familia REAJUSTADA) ===')
print('  %-38s %5s %9s'%('familia','coef','externo'))
for nm,E in fam:
    c,e=err(E); print('  %-38s %5d %8.2f%%'%(nm,c,e))
