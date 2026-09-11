import json, numpy as np, subprocess
D=json.load(open('pareto.json')); geos=D['geos']; N=300
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
L=['* montecarlo de desapareamiento del frente de pareto',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.param sw_stat_global=0 sw_stat_mismatch=1',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
   'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
for i,(wd,ld,wl,ll,w9,l9) in enumerate(geos):
    p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO)]
L+=['.control','set appendwrite','let corrida=0','dowhile corrida < %d'%N,'  reset',
    '  dc VDIF -0.06 0.06 0.004']
L+=['  let d%d = v(g%dx)-v(g%dy)'%(i,i,i) for i in range(len(geos))]
L+=['  wrdata mc.dat '+' '.join('d%d'%i for i in range(len(geos))),
    '  let corrida = corrida + 1','end','.endc','.end']
open('mc.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','mc.spice'],capture_output=True,text=True)
print([l for l in r.stdout.splitlines() if 'rror' in l or 'annot' in l][:5])
A=np.loadtxt('mc.dat'); npts=31
print('%d filas -> %d corridas de %d puntos'%(len(A),len(A)//npts,npts))
A=A[:(len(A)//npts)*npts].reshape(-1,npts,2*len(geos))
q=np.array(geos); ar=q[:,0]*q[:,1]+2*q[:,2]*q[:,3]+q[:,4]*q[:,5]; pa=q[:,0]*q[:,1]
print()
print('%5s %8s %10s %12s %10s'%('w','area','par WdLd','sigma Vos','vs Pelgrom'))
sig=[]
for i in range(len(geos)):
    vd=A[0,:,2*i]; off=[]
    for k in range(A.shape[0]):
        y=A[k,:,2*i+1]
        j=np.where(np.diff(np.sign(y)))[0]
        if len(j): off.append(np.interp(0,y[j[0]:j[0]+2][::int(np.sign(y[j[0]+1]-y[j[0]]))],vd[j[0]:j[0]+2][::int(np.sign(y[j[0]+1]-y[j[0]]))]))
    off=np.array(off); sig.append(off.std())
    print('%5.1f %7.2f %9.3f %10.2f mV %8s  (n=%d)'%([0,.2,.4,.6,.8,1][i],ar[i],pa[i],1000*off.std(),'',len(off)))
sig=np.array(sig)
print()
print('mejora medida del mejor al peor: %.2fx    prediccion Pelgrom sqrt(%.1f)=%.2fx'
      %(sig.max()/sig.min(), pa.max()/pa.min(), np.sqrt(pa.max()/pa.min())))
