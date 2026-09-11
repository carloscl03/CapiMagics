import numpy as np, subprocess
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# el espejo REAL de la celda, alimentado por una corriente controlada
IEX=np.logspace(np.log10(5e-9),np.log10(800e-9),24)
L=['* ro del espejo de salida, a espejo fijo',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VM vm 0 1.0']
vec=[]
for i,I in enumerate(IEX):
    p='k%d'%i
    L+=['I%s %sd 0 %gn'%(p,p,I*1e9),
        'XMR_%s %sd %sd Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'XMO_%s %so %sd Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VAM%s %so vm 0'%(p,p)]
    vec.append('i(vam%s)'%p)
L+=['.control','dc VM 0.3 2.6 0.02','wrdata rf.dat '+' '.join(vec),'.endc','.end']
open('rf.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','rf.spice'],capture_output=True)
A=np.loadtxt('rf.dat'); vm=A[:,0]
m=(vm>0.6)&(vm<1.6)
print('=== ro del espejo REAL (Wo=0.93, Lo=1.86), a espejo fijo ===')
print('%10s %14s %14s'%('Iex [nA]','ro [ohm]','LIF pide 1%'))
xs=[];ys=[]
for i,I in enumerate(IEX):
    y=np.abs(A[:,1+2*i]); g=np.gradient(y,vm)
    mm=m&np.isfinite(g)&(np.abs(g)>0)&(y>1e-12)
    if mm.sum()<5: continue
    ro=np.median(1.0/np.abs(g[mm])); ie=np.median(y[mm])
    xs.append(ie); ys.append(ro)
    if i%3==0: print('%10.1f %13.2e %13.2e'%(1e9*ie,ro,1.9e9/(0.01*ie*1e9)))
xs=np.array(xs); ys=np.array(ys)
np.savez('ro_fijo.npz',iex=xs,ro=ys)
X=np.log10(xs); Y=np.log10(ys)
for g in (1,2,3):
    c=np.polyfit(X,Y,g)
    e=100*np.abs(10**(np.polyval(c,X)-Y)-1)
    print()
    print('  grado %d: error medio %.2f%%, peor %.2f%%'%(g,e.mean(),e.max()))
    if g<=2: print('     lg ro = '+' '.join('%+.4f*lgI^%d'%(v,g-k) for k,v in enumerate(c)))
