import json, numpy as np, subprocess
CS=json.load(open('motor.json')); LD,W9=1.60,0.26
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
L=['* validacion del motor EncoderSpec',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
   'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
vec=[]
for i,c in enumerate(CS):
    wd,wl,ll,l9=c['geo']; p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,LD,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,W9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
    vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata motor.dat '+' '.join(vec),'.endc','.end']
open('motor.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','motor.spice'],capture_output=True)
A=np.loadtxt('motor.dat'); vd=A[:,0]
qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
E=[]
print('%22s %26s %24s'%('PEDIDO','MOTOR predice','NGSPICE'))
for i,c in enumerate(CS):
    ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
    g=float(np.abs(np.gradient(vx)/np.gradient(vd))[k0])
    a,b=ie[qa]*1e9,ie[qb]*1e9; pi,px,pg,pv=c['pred']; oi,og,t=c['pide']
    e=(100*(a/oi-1),100*(g/og-1),100*(a/pi-1),100*(b/px-1),100*(g/pg-1))
    E.append(e)
    if i<8: print('%7.0f nA G=%.2f t=%.0f  %8.1f/%6.1f G=%.3f  %8.1f/%6.1f G=%.3f'%(oi,og,t,pi,px,pg,a,b,g))
E=np.array(E)
print('   ...')
print()
print('=== PEDIDO vs NGSPICE (lo que le importa al usuario) ===')
for n,j in [('iex_min',0),('ganancia',1)]:
    v=E[:,j]; print('  %-9s sesgo %+6.2f%%  |error| %5.2f%%  p90 %5.2f%%  peor %6.2f%%'%(n,v.mean(),np.abs(v).mean(),np.percentile(np.abs(v),90),np.abs(v).max()))
d=np.abs(E[:,:2]).max(1)
for t in (2,5,10): print('  los dos dentro de +-%2d%%: %2d/%d'%(t,(d<t).sum(),len(d)))
print()
print('=== MOTOR vs NGSPICE (calidad de las leyes) ===')
for n,j in [('iex_min',2),('iex_max',3),('ganancia',4)]:
    v=E[:,j]; print('  %-9s sesgo %+6.2f%%  |error| %5.2f%%  peor %6.2f%%'%(n,v.mean(),np.abs(v).mean(),np.abs(v).max()))
