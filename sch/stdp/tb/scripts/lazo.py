"""Lazo cerrado sobre el netlist propuesto: se mide lo que la NEURONA ve.

Hasta ahora todo se ha medido en `vw`. Pero `vw` es interno; lo que importa es
`Iout`, porque es lo que carga la membrana. Un par causal TIENE que subirla.
"""
import os, subprocess, sys
import numpy as np
sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import stdp_banco as B

CEL = open('stdp_propuesta.spice').read()
# se instrumenta igual que el resto: el amperimetro de iout es la propia fuente
PUERTOS = K.PUERTOS
P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'

def evento(dt, vw0=1.65):
    """dt > 0: pre ANTES que post -> causal -> deberia POTENCIAR."""
    t0 = 200e-9
    tpre, tpost = (t0, t0 + dt) if dt > 0 else (t0 - dt, t0)
    cuerpo = (K.bias() + K.pulso('vpre', 'nvpre', tpre, K.DTP0)
              + K.pulso('vpost', 'nvpost', tpost, K.DTP0)
              + ['VIO iout 0 0.9'])
    tf = max(tpre, tpost) + 400e-9
    ctl = ['.ic v(vw)=%.4f' % vw0, '.control', 'tran 0.2n %.6g' % tf,
           'wrdata lz.dat v(vw) i(VIO)', '.endc', '.end']
    cab = ['* lazo', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           B.MIM, CEL, 'X1 %s stdp' % PUERTOS, 'VDD avdd 0 3.3', 'VSS avss 0 0']
    open('lz.spice','w').write('\n'.join(cab+cuerpo+ctl)+'\n')
    subprocess.run(['/foss/tools/bin/ngspice','-b','lz.spice'],
                   capture_output=True, text=True)
    try:
        A = np.loadtxt('lz.dat')
    except Exception:
        return None
    vw, io_ = A[:,1], A[:,3]
    if abs(vw[0]-vw0) > 2e-3:
        return None
    return vw[-1]-vw[0], io_[-1]-io_[0]

print('  netlist PROPUESTO. dt>0 = pre antes que post = causal = potenciacion\n')
print('  %10s %14s %16s %14s' % ('dt[ns]','DVw[mV]','DIout[nA]','efecto'))
for dt in (-4000e-9, -1000e-9, -200e-9, 200e-9, 1000e-9, 4000e-9):
    r = evento(dt)
    if r is None:
        print('  %10.0f   RECHAZADO' % (dt*1e9)); continue
    dv, di = r
    ef = 'refuerza' if di > 1e-11 else ('debilita' if di < -1e-11 else 'plano')
    print('  %10.0f %14.4f %16.4f %14s' % (dt*1e9, dv*1e3, di*1e9, ef))
