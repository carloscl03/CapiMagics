import numpy as np, subprocess
MO='nf=1'
def op(nom,cuerpo,extra=''):
    L=['* consumo '+nom,'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0']+cuerpo+[extra,
       '.control','op','print i(vdd)','.endc','.end']
    open('c.spice','w').write('\n'.join(l for l in L if l)+'\n')
    r=subprocess.run(['ngspice','-b','c.spice'],capture_output=True,text=True)
    for ln in r.stdout.splitlines():
        if ln.strip().startswith('i(vdd)'): return abs(float(ln.split('=')[1]))
    return float('nan')
# --- ENCODER, el nominal del motor: Wd .725 Wl .947 Ll .394 L9 1.811, Ld 1.60 W9 0.26
enc=['VB Vb 0 1.2','VIN Vin 0 1.65','VINN Vinn 0 1.65','VMEM Vmem 0 1.0',
 'XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0']
print('ENCODER (nominal del motor, 1 salida)       %8.1f nA'%(1e9*op('enc',enc)))
# con 4 salidas, que es lo que hace el encoder real
enc4=enc[:-2]+[l for i in range(4) for l in ('XM8_%d o%d x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1'%(i,i),'VI%d o%d Vmem 0'%(i,i))]
print('ENCODER con 4 salidas                       %8.1f nA'%(1e9*op('enc4',enc4)))
# --- INTEGRADOR original y mejorado (estatico, sin spikes)
for nom,(L2,Ir,W6,L6) in [('original',(0.28,50,1.0,0.28)),('mejorado',(1.00,25,0.25,1.0))]:
    b=['IREF avdd nref %gn'%Ir,
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=1u nf=1'%L2,
       'XM2 avss nref vg avss nfet_03v3 L=%gu W=1u nf=1'%L2,
       'XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1',
       'XM6 vm avss avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss 5111f','VMM vm 0 2.2']
    print('INTEGRADOR %-8s (vm=2.2 V, sin spikes)     %8.1f nA'%(nom,1e9*op(nom,b)))
