import numpy as np, subprocess
L=['* ruido del encoder nominal, referido a la entrada',
 '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0',
 'VIN Vin 0 DC 1.65 AC 1','VINN Vinn 0 DC 1.65',
 'XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0',
 '.control','noise v(x) VIN dec 20 1 1e8',
 'setplot noise2','print inoise_total onoise_total','.endc','.end']
open('r.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','r.spice'],capture_output=True,text=True)
er=[l for l in r.stdout.splitlines() if 'rror' in l]
if er: print(er[:3])
for ln in r.stdout.splitlines():
    t=ln.strip()
    if 'noise_total' in t: print('  ',t)
