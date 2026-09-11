import numpy as np, subprocess
LD,W9=1.60,0.26
EXT=np.array([[0.260,1.796],[0.300,2.699],[0.280,0.620],[0.801,3.781]])
LO,HI=np.log10(EXT[:,0]),np.log10(EXT[:,1])
rng=np.random.default_rng(707); N=300
G=10**rng.uniform(LO,HI,(N,4)); np.save('cin_geos.npy',G)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
L=['* capacidad de entrada, una fuente por geometria',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0']
for i,(wd,wl,ll,l9) in enumerate(G):
    p='g%d'%i
    L+=['VIN_%s  %sp 0 DC 1.65 AC 1'%(p,p),'VINN_%s %sn 0 DC 1.65'%(p,p),
        'XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx %sp %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,LD,wd,MO),
        'XM2_%s %sy %sn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,LD,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
L+=['.control','ac lin 1 1k 1k']
L+=['let c%d = abs(i(vin_g%d))/(2*3.14159265*1000)'%(i,i) for i in range(N)]
L+=['wrdata cin.dat '+' '.join('c%d'%i for i in range(N)),'.endc','.end']
open('cin2.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','cin2.spice'],capture_output=True,text=True)
er=[l for l in r.stdout.splitlines() if 'rror' in l]
if er: print(er[:3])
A=np.loadtxt('cin.dat'); C=np.abs(A[1::2]) if A.ndim==1 else np.abs(A[0,1::2])
print('%d capacidades leidas'%len(C))
ok=(C>1e-16)&np.isfinite(C)
print('C_in de %.2f a %.2f fF  (mediana %.2f)'%(1e15*C[ok].min(),1e15*C[ok].max(),1e15*np.median(C[ok])))
X=np.log10(G[ok]); y=np.log10(C[ok])
NOM=['Wd','Wl','Ll','L9']
r2=np.random.default_rng(5); ii=r2.permutation(ok.sum()); n=int(.7*ok.sum())
for nom,B in [('potencia',np.column_stack([np.ones(ok.sum()),X])),
              ('cuadratica',np.column_stack([np.ones(ok.sum()),X]+[X[:,a]*X[:,b] for a in range(4) for b in range(a,4)]))]:
    c=np.linalg.lstsq(B[ii[:n]],y[ii[:n]],rcond=None)[0]
    e=100*np.abs(10**(B[ii[n:]]@c-y[ii[n:]])-1)
    print('  %-11s %2d coef  externo %.2f%%'%(nom,B.shape[1],e.mean()))
    if nom=='potencia':
        c2=np.linalg.lstsq(B,y,rcond=None)[0]
        print('     lg C_in = %+.4f %s'%(c2[0],' '.join('%+.4f lg%s'%(v,n_) for v,n_ in zip(c2[1:],NOM))))
        np.save('cin_ley.npy',c2)
