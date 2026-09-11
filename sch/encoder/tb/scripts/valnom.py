import json, numpy as np, subprocess
D=json.load(open('nom.json'))
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# los tres del motor (Ld=1.60 W9=0.26) + la celda ORIGINAL del equipo
casos=[(k,v['geo'][0],1.60,v['geo'][1],v['geo'][2],0.26,v['geo'][3]) for k,v in D.items()]
casos.append(('equipo',0.5,10.0,2.0,0.28,0.5,0.28))
L=['* nominal del encoder + celda original del equipo',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
   'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
vec=[]
for i,(nom,wd,ld,wl,ll,w9,l9) in enumerate(casos):
    p='g%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
        'VI_%s %so Vmem 0'%(p,p)]
    vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata nom.dat '+' '.join(vec),'.endc','.end']
open('nom.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','nom.spice'],capture_output=True)
A=np.loadtxt('nom.dat'); vd=A[:,0]
qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
print('%-9s %28s %28s'%('','MOTOR predice','NGSPICE'))
for i,(nom,wd,ld,wl,ll,w9,l9) in enumerate(casos):
    ie=np.abs(A[:,1+2*(3*i)]); vx=A[:,1+2*(3*i+1)]; va=A[:,1+2*(3*i+2)]
    g=float(np.abs(np.gradient(vx)/np.gradient(vd))[k0]); a,b=ie[qa]*1e9,ie[qb]*1e9
    if nom in D:
        p=D[nom]['pred']
        print('%-9s %9.1f/%6.1f G=%.3f V(a)=%3.0f %9.1f/%6.1f G=%.3f V(a)=%3.0f   (%+.1f%% %+.1f%% %+.1f%%)'
          %(nom,p[0],p[1],p[2],p[3],a,b,g,va[k0]*1000,100*(a/p[0]-1),100*(b/p[1]-1),100*(g/p[2]-1)))
    else:
        print('%-9s %28s %9.1f/%6.1f G=%.3f V(a)=%3.0f'%(nom,'(fuera de la caja)',a,b,g,va[k0]*1000))
