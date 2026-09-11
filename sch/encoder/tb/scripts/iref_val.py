import numpy as np, subprocess, itertools
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# geometrias AJENAS a la malla, incluidos los dos puntos que discutimos
val=[(0.5,0.28,0.5,0.28),(0.5,10.0,0.5,20.0),(0.35,0.45,0.7,0.9),(1.4,3.3,0.9,7.0),
     (0.8,1.1,1.6,0.4),(2.5,7.0,0.3,2.2),(0.6,18.0,1.2,12.0),(3.0,0.9,2.4,5.5),
     (0.25,2.7,0.45,0.35),(1.1,15.0,3.2,18.0),(0.9,0.33,0.28,1.7),(1.8,5.5,2.8,0.5)]
L=['* val','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical','VDD Vdd 0 3.3','VSS Vss 0 0']
vec=[]
for i,(wn,ln,wp,lp) in enumerate(val):
    p='v%d'%i
    L+=['VAM%s Vdd %ss 0'%(p,p),
        'XM11_%s %sn %sn %ss Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,lp,wp,MO),
        'XM10_%s %sn %sn Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ln,wn,MO)]
    vec.append('i(vam%s)'%p)
L+=['.control','op','print '+' '.join(vec),'.endc','.end']
open('irv.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','irv.spice'],capture_output=True,text=True)
d={}
for t in r.stdout.splitlines():
    t=t.strip()
    if '=' in t and t.split('=')[0].strip().startswith('i(vam'):
        try: d[t.split('=')[0].strip()]=abs(float(t.split('=')[1]))
        except: pass
Iv=np.array([d.get('i(vamv%d)'%i,np.nan) for i in range(len(val))])
# ley entrenada con TODO el barrido
D=np.load('iref2.npz'); C=D['geos']; I=D['I']; ok=D['ok']
X=np.log10(C[ok]); y=np.log10(I[ok])
E=[e for e in itertools.product(range(4),repeat=4) if sum(e)<=3]
B=np.column_stack([np.prod(X**np.array(e),axis=1) for e in E])
c=np.linalg.lstsq(B,y,rcond=None)[0]
np.save('iref_cub.npy',c)
Xv=np.log10(np.array(val))
Bv=np.column_stack([np.prod(Xv**np.array(e),axis=1) for e in E])
pred=10**(Bv@c)
print('=== validacion externa POR GEOMETRIA (12 puntos fuera de la malla) ===')
print('    Wn     Ln     Wp     Lp     ngspice      ley     error')
er=[]
for (wn,ln,wp,lp),m,p in zip(val,Iv,pred):
    e=100*abs(p/m-1); er.append(e)
    print(' %6.2f %6.2f %6.2f %6.2f  %9.3f uA %9.3f %7.1f%%'%(wn,ln,wp,lp,1e6*m,1e6*p,e))
er=np.array(er)
print()
print('  medio %.2f%%   peor %.2f%%'%(er.mean(),er.max()))
