"""Las cuatro salidas del encoder: cuales suben y cuales bajan con Vdif?

El motor las trata como una sola `iex`. Segun Euler son 2 positivas y 2
negativas, y el numero de salidas usadas deberia ser parametro (1 a 4).
Se mide antes de tocar nada.
"""
import os, subprocess
import numpy as np
os.chdir('/tmp/cad')
P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'

def corre(vdif):
    L = ['* salidas del encoder', '.include %s/design.ngspice'%P,
         '.lib %s/sm141064.ngspice typical'%P, '.option rshunt=1e12',
         '.include /foss/designs/libs/snn_analog/encoder/encoder_lvs.spice',
         'VDD vdd 0 3.3','VSS vss 0 0',
         'VIN vin 0 %.6f'%(1.65+vdif/2), 'VINN vinn 0 %.6f'%(1.65-vdif/2),
         'Xe vdd vss vin vinn i1 i2 i3 i4 encoder']
    # cada salida cargada a una tension realista de membrana, con amperimetro
    for k in range(1,5):
        L += ['VM%d i%d m%d 0'%(k,k,k), 'VL%d m%d 0 0.9'%(k,k)]
    L += ['.control','op','print i(VM1) i(VM2) i(VM3) i(VM4)','.endc','.end']
    open('se.spice','w').write('\n'.join(L)+'\n')
    r = subprocess.run(['/foss/tools/bin/ngspice','-b','se.spice'],
                       capture_output=True, text=True)
    out = {}
    for ln in r.stdout.splitlines():
        s = ln.strip().split('=')
        if len(s)==2 and s[0].strip().startswith('i(vm'):
            out[s[0].strip()] = float(s[1])
    return out

print('  corriente de cada salida [nA], con la carga a 0.9 V\n')
print('  %8s %10s %10s %10s %10s' % ('Vdif','Iex_1','Iex_2','Iex_3','Iex_4'))
prev=None
for vd in (-0.14,-0.07,0.0,0.07,0.14):
    o = corre(vd)
    if not o: print('  %8.2f  sin datos'%vd); continue
    v = [abs(o.get('i(vm%d)'%k,0))*1e9 for k in range(1,5)]
    print('  %8.2f %10.3f %10.3f %10.3f %10.3f'%(vd,*v))
    if prev is None: prev=v
print()
o1, o2 = corre(-0.14), corre(0.14)
for k in range(1,5):
    a=abs(o1.get('i(vm%d)'%k,0))*1e9; b=abs(o2.get('i(vm%d)'%k,0))*1e9
    print('  Iex_%d: %.3f -> %.3f nA  => %s' % (k,a,b,
          'SUBE con Vdif (positiva)' if b>a*1.05 else
          ('BAJA con Vdif (negativa)' if a>b*1.05 else 'plana')))
