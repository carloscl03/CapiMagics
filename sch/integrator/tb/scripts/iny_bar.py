import numpy as np, subprocess, itertools
casos=[]
for W6 in (0.25,0.5,1.0,2.0,4.0):
  for L6 in (0.28,1.0):
    for Cf in (1000,5111,20000):
      casos.append((W6,L6,Cf))
V0=(1.0,1.4,1.8,2.2,2.6)
out=np.zeros((len(casos),len(V0)))
for k,v0 in enumerate(V0):
    L=['* inyeccion: salto por spike de 32 ns',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0',
       'VSPK Vext 0 PULSE(0 3.3 0.5u 2n 2n 32n 100u)']
    vec=[]; ic=[]
    for i,(W6,L6,Cf) in enumerate(casos):
        p='g%d'%i
        L+=['XM6_%s %svm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(p,p,L6,W6),
            'C%s %svm avss %gf'%(p,p,Cf)]
        vec.append('v(%svm)'%p); ic.append('v(%svm)=%.3f'%(p,v0))
    L+=['.ic '+' '.join(ic),'.control','tran 0.2n 0.9u uic','wrdata iny.dat '+' '.join(vec),'.endc','.end']
    open('iny.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','iny.spice'],capture_output=True)
    A=np.loadtxt('iny.dat'); t=A[:,0]
    a=int(np.argmin(np.abs(t-0.45e-6))); b=int(np.argmin(np.abs(t-0.8e-6)))
    for i in range(len(casos)): out[i,k]=A[b,1+2*i]-A[a,1+2*i]
    print('  v0=%.1f listo'%v0)
np.savez('iny_bar.npz',casos=np.array(casos),V0=np.array(V0),dV=out)
print()
print('=== salto por spike [mV], segun de donde parta vm ===')
print('%6s %6s %8s %s'%('W6','L6','C [fF]',''.join('%9.1f'%v for v in V0)))
for i,(W6,L6,Cf) in enumerate(casos):
    print('%6.2f %6.2f %8.0f %s'%(W6,L6,Cf,''.join('%9.1f'%(1000*x) for x in out[i])))
