import numpy as np, subprocess
CUERPO=['XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0']
def corre(Ir,nodo):
    L=['* encoder polarizado por corriente inyectada',
     '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
     'VDD avdd 0 3.3','VSS avss 0 0','VMEM Vmem 0 1.0',
     'VIN Vin 0 1.58','VINN Vinn 0 1.72']+CUERPO+[
     'IR avdd nr %gn'%Ir,'XMR nr nr avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
     'XM9 a nr avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
     '.control','dc %s'%nodo,'wrdata p2.dat i(vi)','.endc','.end']
    open('p2.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','p2.spice'],capture_output=True)
    A=np.loadtxt('p2.dat'); return A[:,0],np.abs(A[:,1])
print('  buscando la referencia que iguala Iex = 79.6 nA...')
lo,hi=50.0,20000.0
for _ in range(28):
    m=(lo*hi)**0.5
    v,i=corre(m,'VSS -0.001 0.001 0.001')
    ie=i[len(i)//2]*1e9
    if ie<79.6: lo=m
    else: hi=m
Ir=(lo*hi)**0.5
v,i=corre(Ir,'VSS -0.05 0.05 0.005')
j=int(np.argmin(np.abs(v))); I0=i[j]; d=np.gradient(i,v)[j]
v2,i2=corre(Ir,'VDD 3.25 3.35 0.005')
j2=int(np.argmin(np.abs(v2-3.3))); d2=np.gradient(i2,v2)[j2]
print()
print('=== AL MISMO PUNTO DE TRABAJO (Iex ~ 79.6 nA) ===')
print()
print('  polarizacion por TENSION (Vb = 1.2 V)')
print('     Iex = 79.6 nA   dIex/dVss = -0.487 %/mV   dIex/dVdd = +0.001 %/mV')
print()
print('  polarizacion por CORRIENTE (referencia de %.0f nA en un diodo)'%Ir)
print('     Iex = %.1f nA   dIex/dVss = %+.3f %%/mV   dIex/dVdd = %+.3f %%/mV'%(1e9*I0,100*d/I0*1e-3,100*d2/I0*1e-3))
print()
print('  con 8 mV de rebote en Vss:  tension %+.1f %%   corriente %+.1f %%'%(-0.487*8,100*d/I0*1e-3*8))
