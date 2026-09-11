"""Competencia de familias ESTRUCTURADAS para lg Iex(-).

La cubica completa (35) trata las 4 variables como iguales. Pero la medida dice
otra cosa: `Ll` es la unica curvada, las otras tres son casi rectas, y lo que
manda son los cruces. Eso sugiere factorizar: coeficientes que son FUNCIONES de
la variable curvada.
"""
import numpy as np, itertools
D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok]); n=ok.sum()
a,b,d,e=X[:,0],X[:,1],X[:,2],X[:,3]
u=np.ones(n)
rng=np.random.default_rng(11); idx=rng.permutation(n); nt=int(.7*n); tr,te=idx[:nt],idx[nt:]

def ext(B,y):
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    return B.shape[1],(100*np.abs(10**(B[te]@c-y[te])-1)).mean()

def prod(A1,A2):
    return np.column_stack([p*q for p in A1.T for q in A2.T])

for nom_obj, y in (('lg Iex(-)',np.log10(R[ok,0])), ('lg ganancia',np.log10(R[ok,2]))):
    print('=== %s ==='%nom_obj)
    Pd3=np.column_stack([u,d,d*d,d**3])          # cubica en la variable curvada
    Pd2=np.column_stack([u,d,d*d])
    Lin=np.column_stack([u,a,b,e])               # el resto, lineal
    Lin2=np.column_stack([u,a,b,e,a*b,a*e,b*e])  # el resto, con sus cruces
    Pe2=np.column_stack([u,e,e*e])
    De=np.column_stack([p*q for p in Pd3.T for q in Pe2.T])   # superficie (d,e)
    TODOS=[x for x in itertools.product(range(4),repeat=4) if sum(x)<=3]
    Bful=np.column_stack([np.prod(X**np.array(x),axis=1) for x in TODOS])
    Bcua=np.column_stack([np.prod(X**np.array(x),axis=1) for x in TODOS if sum(x)<=2])
    cands=[
      ('cubica completa (referencia)',        Bful),
      ('cuadratica completa',                 Bcua),
      ('P3(d) x lineal(a,b,e)',               prod(Pd3,Lin)),
      ('P2(d) x lineal(a,b,e)',               prod(Pd2,Lin)),
      ('P3(d) x [lineal+cruces](a,b,e)',      prod(Pd3,Lin2)),
      ('P3(d)xlin(a,b,e) + P2(e)xlin(a,b)',   np.column_stack([prod(Pd3,Lin),prod(Pe2,np.column_stack([a,b]))])),
      ('P3(d)P2(e) x lineal(a,b)',            prod(De,np.column_stack([u,a,b]))),
    ]
    print('  %-38s %5s %9s'%('familia','coef','externo'))
    for nm,B in cands:
        c,er=ext(B,y); print('  %-38s %5d %8.2f%%'%(nm,c,er))

    # --- factorizacion de verdad: producto de dos funciones (rango 1) --------
    # lg I  ~  f(d) * g(a,b,e)  , ajustado por minimos cuadrados alternados
    def als(Ba,Bb,y,it=200):
        cb=np.linalg.lstsq(Bb[tr],y[tr],rcond=None)[0]
        for _ in range(it):
            gb=Bb@cb
            M=Ba*gb[:,None]
            ca=np.linalg.lstsq(M[tr],y[tr],rcond=None)[0]
            ga=Ba@ca
            M2=Bb*ga[:,None]
            cb=np.linalg.lstsq(M2[tr],y[tr],rcond=None)[0]
        pred=(Ba@ca)*(Bb@cb)
        return (100*np.abs(10**(pred[te]-y[te])-1)).mean()
    r1=als(Pd3,Lin,y)
    print('  %-38s %5d %8.2f%%'%('RANGO 1:  f(d) * g(a,b,e)',4+4-1,r1))
    print()
