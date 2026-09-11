import numpy as np, itertools
D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok]); n=ok.sum(); y=np.log10(R[ok,0])
NOM=['a(Wd)','b(Wl)','d(Ll)','e(L9)']
rng=np.random.default_rng(11); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
TODOS=[x for x in itertools.product(range(4),repeat=4) if sum(x)<=3]
def ext(E):
    B=np.column_stack([np.prod(X**np.array(x),axis=1) for x in E])
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    return len(E),(100*np.abs(10**(B[te]@c-y[te])-1)).mean()
puro=[x for x in TODOS if sum(1 for k in x if k)<=1]
print('=== 1. probar a factorizar por CADA variable, no solo por Ll ===')
print('   forma: P3(v) x lineal(las otras tres)   -> 16 coef siempre')
for i in range(4):
    E=[x for x in TODOS if all(k<=1 for j,k in enumerate(x) if j!=i) and sum(1 for j,k in enumerate(x) if j!=i and k)<=1]
    print('   P3(%s) x lineal(resto)     %3d coef  %7.2f%%'%(NOM[i],*ext(E)))
print()
print('=== 2. que PAREJA se lleva las interacciones? ===')
print('   base = aditiva (13 coef, cada variable con su curvatura, cero cruces)')
print('   se anade SOLO los cruces de una pareja, y se REAJUSTA todo')
print('   %-18s %5s %9s %9s'%('pareja','coef','externo','gana'))
c0,e0=ext(puro); print('   %-18s %5d %8.2f%%'%('(ninguna)',c0,e0))
for i,j in itertools.combinations(range(4),2):
    E=puro+[x for x in TODOS if x not in puro and set(k for k,v in enumerate(x) if v)=={i,j}]
    c,e=ext(E); print('   %-18s %5d %8.2f%% %8.2f%%'%('%s x %s'%(NOM[i],NOM[j]),c,e,e0-e))
print()
E2=puro+[x for x in TODOS if x not in puro and len(set(k for k,v in enumerate(x) if v))==2]
c,e=ext(E2); print('   %-18s %5d %8.2f%% %8.2f%%'%('TODAS las parejas',c,e,e0-e))
E3=[x for x in TODOS if len(set(k for k,v in enumerate(x) if v))<=2]
print('   %-18s %5d %8.2f%%'%('idem (comprobacion)',*ext(E3)))
c,e=ext(TODOS); print('   %-18s %5d %8.2f%%'%('+ los triples',c,e))
