import numpy as np, subprocess
# --- 1) IMPEDANCIA DE ENTRADA: la puerta de M6, que el spike del LIF debe mover
casos=[(0.25,1.0),(0.25,0.28),(1.0,0.28),(1.0,1.0),(2.0,0.28),(4.0,0.28)]
L=['* C_in del integrador','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD avdd 0 3.3','VSS avss 0 0']
vec=[]
for i,(W6,L6) in enumerate(casos):
    p='k%d'%i
    L+=['VIN%s %se 0 DC 1.65 AC 1'%(p,p),
        'XM6_%s %sm %se avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(p,p,p,L6,W6),
        'C%s %sm avss 5111f'%(p,p),'VMM%s %sm 0 2.0'%(p,p)]
    vec.append('i(vin%s)'%p)
L+=['.control','ac lin 1 1k 1k','wrdata ci.dat '+' '.join('abs(%s)/(2*3.14159265*1000)'%x for x in vec),'.endc','.end']
open('ci.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','ci.spice'],capture_output=True)
A=np.loadtxt('ci.dat'); C=np.abs(A[1::2]) if A.ndim==1 else np.abs(A[0,1::2])
print('=== 1) IMPEDANCIA DE ENTRADA (puerta de M6) ===')
print('  la entrada es una puerta MOS: en DC infinita, lo que importa es la capacidad')
print('%8s %8s %12s'%('W6','L6','C_in [fF]'))
for (W6,L6),c in zip(casos,C): print('%8.2f %8.2f %12.3f'%(W6,L6,1e15*c))
print()
# --- 2) IMPEDANCIA DE SALIDA en vm: la pendiente de la curva de fuga
F=np.load('suelo.npz'); v=F['v']; I=F['I']; IR=F['IR']
print('=== 2) IMPEDANCIA DE SALIDA en vm (espejo L2=1u) ===')
print('  R_out = dvm/dI, de la curva de fuga')
print('%10s %10s %14s %14s'%('Iref [nA]','vm [V]','fuga [nA]','R_out [ohm]'))
for k,ir in enumerate(IR):
    if ir not in (5,12,25): continue
    for V in (1.6,2.0,2.4):
        j=int(np.argmin(np.abs(v-V)))
        g=np.gradient(I[:,k],v)[j]
        print('%10.0f %10.2f %13.1f %14.2e'%(ir,V,1e9*I[j,k],1/abs(g) if abs(g)>0 else np.inf))
