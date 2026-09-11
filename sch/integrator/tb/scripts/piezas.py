import numpy as np, subprocess
CAB='''* las dos piezas del integrador, por separado
.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice
.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical
.subckt integ Vext avdd avss I_50n vm
XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1
XM6 vm Vext avdd avss nfet_03v3 L=0.28u W=1u nf=1
XM2 avss I_50n vg avss nfet_03v3 L=0.28u W=1u nf=1
XM3 I_50n I_50n avss avss nfet_03v3 L=0.28u W=1u nf=1
.ends
VDD avdd 0 3.3
VSS avss 0 0
IREF avdd nref 50n
'''
# --- 1) la FUGA: cuanta corriente sale de vm en funcion de vm ---
L=[CAB,'VEXT Vext 0 0','VM vm 0 1.0','X1 Vext avdd avss nref vm integ',
   '.control','dc VM 0.05 3.3 0.025','wrdata fuga.dat i(vm)','.endc','.end']
open('f.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','f.spice'],capture_output=True)
A=np.loadtxt('fuga.dat'); v=A[:,0]; i=A[:,1]
np.save('fuga.npy',np.column_stack([v,i]))
print('=== 1) LA FUGA: corriente que sale de vm ===')
for V in (0.5,1.0,1.5,2.0,2.5,3.0):
    j=int(np.argmin(np.abs(v-V))); print('   vm=%.2f V  ->  %8.2f nA'%(V,1e9*i[j]))
print()
# --- 2) LA CARGA: cuanto sube vm con UN spike de 32 ns, segun donde parta ---
print('=== 2) LA CARGA: salto de vm con un spike de 32 ns ===')
sal=[]
for v0 in (0.5,1.0,1.5,2.0,2.5,3.0):
    L=[CAB,'VSPK Vext 0 PULSE(0 3.3 1u 2n 2n 32n 100u)',
       'X1 Vext avdd avss nref vm integ','C3 vm avss 5111f','.ic v(vm)=%.3f'%v0,
       '.control','tran 0.2n 1.5u uic','wrdata s.dat v(vm)','.endc','.end']
    open('s.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','s.spice'],capture_output=True)
    B=np.loadtxt('s.dat'); t=B[:,0]; vm=B[:,1]
    antes=vm[np.argmin(np.abs(t-0.9e-6))]; desp=vm[np.argmin(np.abs(t-1.2e-6))]
    dq=5111e-15*(desp-antes)
    sal.append((v0,antes,desp,desp-antes,dq))
    print('   partiendo de %.2f V  ->  sube a %.4f V   (salto %6.1f mV, %5.2f fC)'%(v0,desp,1000*(desp-antes),dq*1e15))
np.save('carga.npy',np.array(sal))
