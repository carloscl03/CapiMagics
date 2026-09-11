"""Depende `iout` de la actividad PRESINAPTICA, o solo del peso?

Leyendo el netlist, `vpre` solo aparece en M3 (escribe el peso) y M8 (escribe
la traza de potenciacion). La salida sale de Mp2, cuya puerta es `nd`, que
viene de Mn, cuya puerta es `vw`. O sea que `iout` = f(peso) y nada mas.

Pero el comentario del `stdp_4x2` dice que `ifwd` recoge lo que cada sinapsis
entrega "given its current synaptic weight value AND THE SPIKES OF THE PREVIOUS
LAYER". Si eso no esta implementado, la red no propaga informacion: la tasa de
cada capa dependeria solo de los pesos, no de la actividad de la anterior.

Se mide: misma celda, mismo peso, con la entrada presinaptica CALLADA y
DISPARANDO a varias tasas.
"""
import os, subprocess, sys
import numpy as np
sys.path.insert(0, '/tmp/stdp'); os.chdir('/tmp/stdp')
import carac_stdp as K
import stdp_banco as B

P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
CEL = open('stdp_propuesta.spice').read()

def carga_media(f_kHz, vw=1.2, tf=20e-6):
    """Corriente media entregada a `iout` con el pre disparando a f_kHz."""
    per = 1e3/f_kHz*1e-6 if f_kHz else 0
    if f_kHz:
        pre = ['VVPRE vpre 0 PULSE(0 3.3 1u 1n 1n 33n %.6g)' % per,
               'VNVPRE nvpre 0 PULSE(3.3 0 1u 1n 1n 33n %.6g)' % per]
    else:
        pre = ['VVPRE vpre 0 0', 'VNVPRE nvpre 0 3.3']
    cuerpo = (K.bias() + pre + ['VVPOST vpost 0 0', 'VNVPOST nvpost 0 3.3',
                                'VWS vw 0 %.4f' % vw, 'VIO iout 0 0.9'])
    ctl = ['.control', 'tran 20n %.6g' % tf,
           'wrdata gt.dat i(VIO)', '.endc', '.end']
    cab = ['* gating', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           B.MIM, CEL, 'X1 %s stdp' % K.PUERTOS, 'VDD avdd 0 3.3', 'VSS avss 0 0']
    open('gt.spice','w').write('\n'.join(cab+cuerpo+ctl)+'\n')
    subprocess.run(['/foss/tools/bin/ngspice','-b','gt.spice'],
                   capture_output=True, text=True)
    A = np.loadtxt('gt.dat')
    t, i = A[:,0], np.abs(A[:,1])
    m = t > 5e-6
    return float(np.mean(i[m]))

print('  peso fijo en vw = 1.2 V. Solo cambia la actividad del PRE.\n')
print('  %14s %16s' % ('f pre [kHz]', 'Iout medio [nA]'))
base = None
for f in (0, 100, 500, 1000, 2000):
    v = carga_media(f)*1e9
    if base is None: base = v
    print('  %14s %16.3f   %s' % ('callado' if f==0 else '%d'%f, v,
          '' if f==0 else '(%+.2f %% vs callado)' % (100*(v-base)/base)))
