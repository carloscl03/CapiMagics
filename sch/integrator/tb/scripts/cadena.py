import numpy as np, subprocess
# rango de entrada REAL del encoder: barrer Vdif hasta que sature
L=['* rango de entrada del encoder nominal','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VB Vb 0 1.2','VMEM Vmem 0 1.0','VDIF Vdif 0 0',
 'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)',
 'XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0',
 '.control','dc VDIF -1.2 1.2 0.01','wrdata rng.dat i(vi)','.endc','.end']
open('rg.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','rg.spice'],capture_output=True)
A=np.loadtxt('rng.dat'); vd=A[:,0]; ie=np.abs(A[:,1])
g=np.abs(np.gradient(np.log10(np.maximum(ie,1e-15)),vd))
gm=g.max()
u=np.where(g>0.1*gm)[0]
print('=== RANGO DE ENTRADA del encoder (Vdif) ===')
print('  zona con >10%% de la pendiente maxima: %.3f a %.3f V   (%.0f mV de ancho)'%(vd[u[0]],vd[u[-1]],1000*(vd[u[-1]]-vd[u[0]])))
print('  Iex en esos extremos: %.1f a %.1f nA'%(1e9*ie[u[0]],1e9*ie[u[-1]]))
print()
print('  la entrada es DIFERENCIAL: Vin = 1.65 + Vdif/2, Vinn = 1.65 - Vdif/2')
print('  o sea Vin recorre %.3f a %.3f V'%(1.65+vd[u[0]]/2,1.65+vd[u[-1]]/2))
print()
print('=== SALIDA del integrador (vm), medida ===')
print('  original  Iref=50n:  2.21 a 2.34 V   (130 mV, un solo extremo)')
print('  mejorado  Iref=25n:  1.79 a 2.00 V   (210 mV)')
print('  a 12 nA:             1.99 a 2.16 V   (170 mV)')
print()
print('=== LA CADENA ===')
print('  el integrador entrega una tension UNIPOLAR en torno a 2.0 V')
print('  el encoder pide una DIFERENCIAL en torno a 1.65 V de modo comun')
