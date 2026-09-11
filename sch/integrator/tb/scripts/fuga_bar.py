import numpy as np, subprocess, itertools, json
CAB=['* cribado de la fuga del integrador',
 '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VM vm 0 1.0']
casos=[]
for W1 in (0.5,1.0,2.0):
  for L1 in (0.28,1.0,4.0):
    for W2 in (0.5,1.0,2.0):
      for L2 in (0.28,1.0,4.0):
        casos.append((W1,L1,W2,L2,50e-9))
for Ir in (10e-9,25e-9,100e-9,200e-9):
  for L2 in (0.28,1.0,4.0):
    casos.append((1.0,0.28,1.0,L2,Ir))
L=list(CAB); vec=[]
for i,(W1,L1,W2,L2,Ir) in enumerate(casos):
    p='b%d'%i
    L+=['I%s avdd %sref %gn'%(p,p,Ir*1e9),
        'XM3_%s %sref %sref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(p,p,p,L2,W2),
        'XM2_%s avss %sref %svg avss nfet_03v3 L=%gu W=%gu nf=1'%(p,p,p,L2,W2),
        'XM1_%s %svg %svg %ss avdd pfet_03v3 L=%gu W=%gu nf=1'%(p,p,p,p,L1,W1),
        'VAM%s vm %ss 0'%(p,p)]
    vec.append('i(vam%s)'%p)
L+=['.control','dc VM 0.05 3.3 0.05','wrdata fb.dat '+' '.join(vec),'.endc','.end']
open('fb.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','fb.spice'],capture_output=True)
A=np.loadtxt('fb.dat'); v=A[:,0]; I=np.abs(A[:,1::2])
json.dump([list(c) for c in casos],open('fuga_casos.json','w'))
np.savez('fuga_bar.npz',v=v,I=I,casos=np.array(casos))
print('%d geometrias, %d puntos de vm'%(I.shape[1],len(v)))
def en(V): return I[int(np.argmin(np.abs(v-V))),:]
i10,i15,i25=en(1.0),en(1.5),en(2.5)
plan=np.where(i10>1e-12,i25/np.maximum(i10,1e-15),np.inf)
print()
print('=== que controla el NIVEL y que la PLANITUD? ===')
print('%6s %6s %6s %6s %8s %12s %12s %10s'%('W1','L1','W2','L2','Iref','I@1.5V [nA]','I@2.5V [nA]','I25/I10'))
for idx in [0,2,6,8,18,20,24,26,36,44,52]:
    if idx>=len(casos): continue
    W1,L1,W2,L2,Ir=casos[idx]
    print('%6.2f %6.2f %6.2f %6.2f %7.0fn %12.1f %12.1f %10.1f'%(W1,L1,W2,L2,Ir*1e9,1e9*i15[idx],1e9*i25[idx],plan[idx]))
print()
mej=np.argsort(plan)[:6]
print('=== las 6 mas PLANAS (menor I@2.5 / I@1.0) ===')
print('%6s %6s %6s %6s %8s %12s %10s'%('W1','L1','W2','L2','Iref','I@1.5V','I25/I10'))
for j in mej:
    W1,L1,W2,L2,Ir=casos[j]
    print('%6.2f %6.2f %6.2f %6.2f %7.0fn %11.1f %10.2f'%(W1,L1,W2,L2,Ir*1e9,1e9*i15[j],plan[j]))
