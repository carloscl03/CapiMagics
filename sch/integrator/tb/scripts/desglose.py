import numpy as np, subprocess
L=['* desglose del encoder nominal','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VB Vb 0 1.2','VIN Vin 0 1.65','VINN Vinn 0 1.65','VMEM Vmem 0 1.0',
 'VAX avdd px 0','VAY avdd py 0',
 'XM3 x x px avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y py avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'VTAIL a na 0','XM9 na Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
 'VAO avdd po 0','XM8 o x po avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0',
 '.control','op','print i(vdd) i(vax) i(vay) i(vtail) i(vao) i(vi) v(x) v(a)','.endc','.end']
open('d.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','d.spice'],capture_output=True,text=True)
d={}
for ln in r.stdout.splitlines():
    t=ln.strip()
    if '=' in t and t.split('=')[0].strip() in ('i(vdd)','i(vax)','i(vay)','i(vtail)','i(vao)','i(vi)','v(x)','v(a)'):
        d[t.split('=')[0].strip()]=float(t.split('=')[1])
print('=== ENCODER nominal, en reposo (Vdif = 0) ===')
print('  rama x (M3)        %8.1f nA'%(1e9*abs(d.get('i(vax)',0))))
print('  rama y (M4)        %8.1f nA'%(1e9*abs(d.get('i(vay)',0))))
print('  cola (M9)          %8.1f nA'%(1e9*abs(d.get('i(vtail)',0))))
print('  espejo salida M8   %8.1f nA   <- lo que entrega al LIF'%(1e9*abs(d.get('i(vao)',0))))
print('  TOTAL de Vdd       %8.1f nA'%(1e9*abs(d.get('i(vdd)',0))))
print()
print('  V(x)=%.3f V   V(a)=%.3f V'%(d.get('v(x)',0),d.get('v(a)',0)))
ent=abs(d.get('i(vao)',0)); tot=abs(d.get('i(vdd)',0))
print()
print('  eficiencia: entrega %.0f nA de %.0f nA consumidos = %.1f%%'%(1e9*ent,1e9*tot,100*ent/tot))
