import numpy as np, subprocess, itertools
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# Caja AMPLIADA: hasta L=25um, porque el punto recomendado (Ln=10, Lp=20)
# quedaba fuera del barrido anterior (Ln<=3, Lp<=4).
WN=[0.22,0.5,1.0,2.0,4.0]; LN=[0.28,0.6,1.5,4.0,10.0,25.0]
WP=[0.22,0.5,1.0,2.0,4.0]; LP=[0.28,0.6,1.5,4.0,10.0,25.0]
casos=[c for c in itertools.product(WN,LN,WP,LP)]
print('%d geometrias'%len(casos))
I=np.full(len(casos),np.nan)
B=120
for k0 in range(0,len(casos),B):
    blo=casos[k0:k0+B]
    L=['* I_ref','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0']
    vec=[]
    for i,(wn,ln,wp,lp) in enumerate(blo):
        p='b%d'%i
        L+=['VAM%s Vdd %ss 0'%(p,p),
            'XM11_%s %sn %sn %ss Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,lp,wp,MO),
            'XM10_%s %sn %sn Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ln,wn,MO)]
        vec.append('i(vam%s)'%p)
    L+=['.control','op','print '+' '.join(vec),'.endc','.end']
    open('ir2.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','ir2.spice'],capture_output=True,text=True)
    d={}
    for t in r.stdout.splitlines():
        t=t.strip()
        if '=' in t and t.split('=')[0].strip().startswith('i(vam'):
            try: d[t.split('=')[0].strip()]=abs(float(t.split('=')[1]))
            except: pass
    for i in range(len(blo)):
        v=d.get('i(vamb%d)'%i)
        if v is not None: I[k0+i]=v
    print('  %d/%d'%(min(k0+B,len(casos)),len(casos)),flush=True)
C=np.array(casos)
ok=np.isfinite(I)&(I>0)
np.savez('iref2.npz',geos=C,I=I,ok=ok)
print('validas %d/%d   de %.3f a %.1f uA'%(ok.sum(),len(I),1e6*I[ok].min(),1e6*I[ok].max()))
