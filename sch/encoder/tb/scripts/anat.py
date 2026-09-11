import numpy as np, itertools
D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok]); n=ok.sum()
OBJ=[('lg Iex(-)',np.log10(R[ok,0])),('lg ganancia',np.log10(R[ok,2])),('V(a)',R[ok,3])]
NOM=['a=lgWd','b=lgWl','d=lgLl','e=lgL9']
rng=np.random.default_rng(11); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]
def err(B,y,log=True):
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    r=B[te]@c-y[te]
    return (100*np.abs(10**r-1)).mean() if log else 1000*np.abs(r).mean()
print('=== 1. cuanto se mueve cada objetivo en la caja ===')
for nm,y in OBJ:
    print('  %-12s recorre %.2f decadas' % (nm, y.max()-y.min()) if 'lg' in nm else '  %-12s recorre %.0f mV'%(nm,1000*(y.max()-y.min())))
print()
print('=== 2. es SEPARABLE? (suma de curvas de 1 variable, sin cruces) ===')
print('   aditiva  = const + cubica en a + cubica en b + cubica en d + cubica en e')
print('   %-12s %8s %8s %8s   %s'%('objetivo','lineal','aditiva','completa','coef'))
for nm,y in OBJ:
    lg='lg' in nm
    Blin=np.column_stack([np.ones(n),X])
    Badd=np.column_stack([np.ones(n)]+[X[:,i]**k for i in range(4) for k in (1,2,3)])
    E=[e for e in itertools.product(range(4),repeat=4) if sum(e)<=3]
    Bful=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
    u='%%' if lg else 'mV'
    print('   %-12s %7.2f%s %7.2f%s %7.2f%s   %d/%d/%d'%(nm,err(Blin,y,lg),u,err(Badd,y,lg),u,err(Bful,y,lg),u,5,13,35))
print()
print('=== 3. cuanta curvatura tiene cada variable por separado ===')
print('   (rodajas 1-D reales: fijas 3 variables, mueves 1, ajustas grado 1/2/3)')
for nm,y in OBJ[:1]:
    for i in range(4):
        otras=[j for j in range(4) if j!=i]
        # agrupa por los valores de las otras 3
        cla={}
        for k in range(n):
            cla.setdefault(tuple(np.round(X[k,otras],4)),[]).append(k)
        e1=[];e2=[];e3=[]
        for ks in cla.values():
            if len(ks)<6: continue
            xv=X[ks,i]; yv=y[ks]
            if xv.max()-xv.min()<0.3: continue
            for g,acc in ((1,e1),(2,e2),(3,e3)):
                p=np.polyfit(xv,yv,g); acc.append(np.abs(np.polyval(p,xv)-yv).max())
        if e1: print('   %-8s %3d rodajas   grado1 %.4f  grado2 %.4f  grado3 %.4f  decadas'%(NOM[i],len(e1),np.mean(e1),np.mean(e2),np.mean(e3)))
