import subprocess
L=['* el M3/M2 del integrador: es un espejo de corriente de verdad?',
 '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD avdd 0 3.3','VSS avss 0 0','VMM vm 0 2.0',
 'IREF avdd nref 25n',
 'VAM3 nref n3 0',
 'XM3 n3 nref avss avss nfet_03v3 L=1.0u W=1u nf=1',
 'VAM2 avss n2 0',
 'XM2 n2 nref vg avss nfet_03v3 L=1.0u W=1u nf=1',
 'XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1',
 '.control','op','print i(vam3) i(vam2) v(nref) v(vg)','.endc','.end']
open('e.spice','w').write('\n'.join(L)+'\n')
r=subprocess.run(['ngspice','-b','e.spice'],capture_output=True,text=True)
d={}
for ln in r.stdout.splitlines():
    t=ln.strip()
    if '=' in t and t.split('=')[0].strip() in ('i(vam3)','i(vam2)','v(nref)','v(vg)'):
        d[t.split('=')[0].strip()]=float(t.split('=')[1])
i3=abs(d.get('i(vam3)',0)); i2=abs(d.get('i(vam2)',0))
print('  referencia inyectada        25.0 nA')
print('  corriente por M3 (diodo)  %6.1f nA'%(1e9*i3))
print('  corriente por M2 (copia)  %6.1f nA'%(1e9*i2))
print('  relacion de copia         %6.3f'%(i2/i3 if i3 else 0))
print()
print('  V(nref) = %.3f V   (la puerta comun)'%d.get('v(nref)',0))
print('  V(vg)   = %.3f V   (el drenador de M2)'%d.get('v(vg)',0))
