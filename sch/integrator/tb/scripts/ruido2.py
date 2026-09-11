import numpy as np, subprocess
L=['* espectro de ruido del encoder','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
 'VIN Vin 0 DC 1.65 AC 1','VINN Vinn 0 DC 1.65',
 'XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0',
 '.control','noise v(x) VIN dec 20 1 1e8','setplot noise1',
 'wrdata esp.dat inoise_spectrum','.endc','.end']
open('r2.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','r2.spice'],capture_output=True)
A=np.loadtxt('esp.dat'); f=A[:,0]; S=A[:,1]     # V/sqrt(Hz)
print('=== densidad de ruido referida a la entrada ===')
for F in (10,1e3,1e5,1e6,1e7):
    j=int(np.argmin(np.abs(f-F))); print('  %9.0f Hz  %8.1f nV/sqrt(Hz)'%(f[j],1e9*S[j]))
print()
print('=== RMS integrado, segun la banda ===')
for lo,hi,nom in [(1,1e8,'1 Hz - 100 MHz (todo)'),(1,1e6,'1 Hz - 1 MHz'),
                  (1e3,1e6,'1 kHz - 1 MHz'),(1e5,1e6,'100 kHz - 1 MHz (la del LIF)')]:
    m=(f>=lo)&(f<=hi)
    rms=np.sqrt(np.trapezoid(S[m]**2,f[m]))
    print('  %-32s %8.2f mV'%(nom,1e3*rms))
print()
print('  para comparar: sigma_Vos por desapareamiento = 18.0 mV')
print('                 la excursion de entrada       = +-140 mV')
