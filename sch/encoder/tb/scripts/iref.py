import numpy as np, subprocess, itertools
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# I_ref del bloque de bias: la corriente que circula por el divisor M10/M11
casos=[]
for wn,ln in [(0.5,0.28),(0.5,1.0),(0.5,2.0),(1.0,0.28),(1.0,1.0),(2.0,0.28),(2.0,1.0)]:
    for wp,lp in [(0.5,0.28),(0.5,1.0),(1.0,0.28),(1.0,1.0),(2.0,0.28),(0.5,2.0)]:
        casos.append((wn,ln,wp,lp))
L=['* I_ref del divisor de bias','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0']
vec=[]
for i,(wn,ln,wp,lp) in enumerate(casos):
    p='b%d'%i
    L+=['VAM%s Vdd %ss 0'%(p,p),
        'XM11_%s %sn %sn %ss Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,lp,wp,MO),
        'XM10_%s %sn %sn Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ln,wn,MO)]
    vec.append('i(vam%s)'%p)
L+=['.control','op','print '+' '.join(vec),'.endc','.end']
open('ir.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','ir.spice'],capture_output=True,text=True)
d={}
for ln_ in r.stdout.splitlines():
    t=ln_.strip()
    if '=' in t and t.split('=')[0].strip().startswith('i(vam'):
        d[t.split('=')[0].strip()]=abs(float(t.split('=')[1]))
I=np.array([d.get('i(vamb%d)'%i,np.nan) for i in range(len(casos))])
ok=np.isfinite(I)&(I>0)
C=np.array(casos)
print('=== I_ref del divisor M10/M11: %d geometrias ==='%ok.sum())
print('  de %.2f a %.2f nA'%(1e9*I[ok].min(),1e9*I[ok].max()))
print()
X=np.log10(C[ok]); y=np.log10(I[ok]); u=np.ones(ok.sum())
NOM=['Wn','Ln','Wp','Lp']
rng=np.random.default_rng(4); idx=rng.permutation(ok.sum()); n=int(.7*ok.sum()); tr,te=idx[:n],idx[n:]
for nom,B in [('potencia',np.column_stack([u,X])),
              ('cuadratica',np.column_stack([u,X]+[X[:,i]*X[:,j] for i in range(4) for j in range(i,4)]))]:
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    e=(100*np.abs(10**(B[te]@c-y[te])-1)).mean()
    print('  %-11s %2d coef  externo %.2f%%'%(nom,B.shape[1],e))
    if nom=='potencia':
        c2=np.linalg.lstsq(B,y,rcond=None)[0]
        print('     lg I_ref = %+.4f %s'%(c2[0],' '.join('%+.4f lg%s'%(v,n_) for v,n_ in zip(c2[1:],NOM))))
