import numpy as np, subprocess
LD,W9=1.60,0.26
EXT=np.array([[0.260,1.796],[0.300,2.699],[0.280,0.620],[0.801,3.781]])
LO,HI=np.log10(EXT[:,0]),np.log10(EXT[:,1])
rng=np.random.default_rng(515); GE=10**rng.uniform(LO,HI,(150,4)); np.save('mcley7_geos.npy',GE)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
N=200
L=['* sigma_Vos en la caja corregida',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.param sw_stat_global=0 sw_stat_mismatch=1',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
   'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)']
for i,(wd,wl,ll,l9) in enumerate(GE):
    p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO)]
L+=['.control','set appendwrite','let c=0','dowhile c < %d'%N,'  reset','  dc VDIF -0.09 0.09 0.015']
L+=['  let d%d = v(g%dx)-v(g%dy)'%(i,i,i) for i in range(len(GE))]
L+=['  wrdata mcley7.dat '+' '.join('d%d'%i for i in range(len(GE))),'  let c = c + 1','end','.endc','.end']
open('mcley7.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['rm','-f','mcley7.dat'])
subprocess.run(['ngspice','-b','mcley7.spice'],capture_output=True)
A=np.loadtxt('mcley7.dat'); P=13; A=A[:(len(A)//P)*P].reshape(-1,P,2*len(GE))
print('%d corridas'%A.shape[0]); vd=A[0,:,0]
sig=np.zeros(len(GE)); nn=np.zeros(len(GE))
for i in range(len(GE)):
    off=[]
    for k in range(A.shape[0]):
        y=A[k,:,2*i+1]; j=np.where(np.diff(np.sign(y)))[0]
        if len(j):
            a,b=j[0],j[0]+2
            yy,xx=(y[a:b],vd[a:b]) if y[a+1]>y[a] else (y[a:b][::-1],vd[a:b][::-1])
            off.append(np.interp(0.0,yy,xx))
    sig[i]=np.std(off); nn[i]=len(off)
np.savez('mcley7.npz',geos=GE,sig=sig,n=nn)
ok=nn>0.9*A.shape[0]
print('%d/%d con estadistica completa;  sigma_Vos de %.1f a %.1f mV'%(ok.sum(),len(GE),1000*sig[ok].min(),1000*sig[ok].max()))
X=np.log10(GE[ok]); y=np.log10(sig[ok]); NOM=['Wd','Wl','Ll','L9']
r=np.random.default_rng(2); ii=r.permutation(ok.sum()); n=int(.7*ok.sum()); tr,te=ii[:n],ii[n:]
for nom,B in [('potencia',np.column_stack([np.ones(ok.sum()),X])),
              ('cuadratica',np.column_stack([np.ones(ok.sum()),X]+[X[:,a]*X[:,b] for a in range(4) for b in range(a,4)]))]:
    c=np.linalg.lstsq(B[tr],y[tr],rcond=None)[0]
    e=lambda s: 100*np.abs(10**(B[s]@c-y[s])-1)
    print('  %-11s %2d coef  ajuste %.1f%%  externo %.1f%%'%(nom,B.shape[1],e(tr).mean(),e(te).mean()))
    if nom=='potencia':
        c2=np.linalg.lstsq(B,y,rcond=None)[0]
        print('     lg sigma_Vos = %+.3f %s'%(c2[0],' '.join('%+.3f lg%s'%(v,n_) for v,n_ in zip(c2[1:],NOM))))
