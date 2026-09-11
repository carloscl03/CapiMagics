import numpy as np, subprocess
def enc(nodo):
    L=['* sensibilidad del encoder al riel','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
     'VDD avdd 0 3.3','VSS avss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
     'VIN Vin 0 1.58','VINN Vinn 0 1.72',
     'XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
     'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
     'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
     'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
     'XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
     'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0',
     '.control','dc %s'%nodo,'wrdata ps.dat i(vi)','.endc','.end']
    open('p.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','p.spice'],capture_output=True)
    A=np.loadtxt('ps.dat'); return A[:,0], np.abs(A[:,1])
print('=== ENCODER: cuanto mueve Iex una perturbacion del riel ===')
v,i=enc('VDD 3.25 3.35 0.005')
j=int(np.argmin(np.abs(v-3.3))); I0=i[j]
d=np.gradient(i,v)[j]
print('  Iex nominal          %.1f nA'%(1e9*I0))
print('  dIex/dVdd            %.2f nA por mV  ->  %.3f %%/mV'%(1e6*d,100*d/I0*1e-3))
v,i=enc('VSS -0.05 0.05 0.005')
j=int(np.argmin(np.abs(v))); d2=np.gradient(i,v)[j]
print('  dIex/dVss            %.2f nA por mV  ->  %.3f %%/mV'%(1e6*d2,100*d2/I0*1e-3))
print()
print('  o sea: 10 mV de rebote en Vss cambian Iex un %.1f %%'%(abs(100*d2/I0*1e-3)*10))
print('         10 mV en Vdd,                        %.1f %%'%(abs(100*d/I0*1e-3)*10))
