"""Los dos ultimos cabos.

A) LA PARASITA DE `vw` ES LA PUERTA DE M5?
   Medida: C0 = 0.50 unidades = 27 fF, identica en las dos mitades. La puerta
   de M5 (W=0.5, L=15) son 7.5 um2, que a ~4.5 fF/um2 dan ~34 fF. Si la
   hipotesis es buena, encoger M5 tiene que bajar C0 en proporcion al AREA DE
   PUERTA, y eso acopla dos decisiones que yo trataba por separado.

   Test: medir la senal a dos CW con M5 grande y con M5 pequeno, y extraer C0
   en cada caso.

B) DE QUIEN ES LA FUGA DE 20 pA?
   El decaimiento cierra a -1.7 % pero por debajo de Itd ~ 0.4 nA aparece una
   fuga de ~20 pA que pone suelo a tau-. Candidatos sobre `vdep`: M12 apagado
   (drenador en n5 ~ 0.87 V), M4 (solo puerta, no deberia), y el rshunt=1e12
   del banco (0.9 pA a 0.9 V: deberia ser el 4 %).
   Test: apagar rshunt, y barrer W de M12, que es el unico con Vds sobre vdep.
"""
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

CU = 54.5e-15


def senal(ncw, w5, l5, vdep=0.85):
    cel = K.forzado(K.caps(S.dim(K.BASE, ['M5'], w5, l5), ncw=ncw), 'vdep')
    r = []
    for v in (0.0, vdep):
        cuerpo = (K.bias() + ['VFvdep vdepf 0 %.4f' % v]
                  + K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
                  + K.quieto('vpost', 'nvpost'))
        d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado='vdep'), cel,
                    extra=' vdepf')
        if not K.arranco_bien(d):
            return None
        r.append(float(d['V']['vw'][-1] - K.VW0))
    return r[1] - r[0]


def extrae_C0(w5, l5):
    """C0 tal que senal*(nCW+C0) sea igual a dos capacidades distintas."""
    a, b = senal(5, w5, l5), senal(40, w5, l5)
    if a is None or b is None:
        return None
    # a*(5+x) = b*(40+x)  ->  x = (40b - 5a)/(a - b)
    return (40 * b - 5 * a) / (a - b), a, b


def fuga(wm12, rshunt=True):
    """Pendiente de decaimiento a Itd muy baja: el exceso es la fuga."""
    cel = K.caps(S.dim(K.BASE, ['M12'], wm12, 0.63), ndep=2)
    cuerpo = (K.bias(itd=0.50) + K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
              + K.quieto('vpre', 'nvpre'))
    ctl = K.tran(4.2e-6, paso='1n')
    sp, dat = 'fg_%d.spice' % os.getpid(), 'fg_%d.dat' % os.getpid()
    cab = ['* fuga', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
           '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical']
    if rshunt:
        cab.append('.option rshunt=1e12')
    cab += [K.B.MIM, cel, 'X1 %s stdp' % K.PUERTOS,
            'VDD avdd 0 3.3', 'VSS avss 0 0', 'VIO iout 0 0.9']
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl).replace('SALIDA', dat) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', sp], capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None
    t = A[:, 0]
    vd = A[:, 1 + 2 * K.NODOS.index('vdep')]
    itd = np.abs(A[:, 1 + 2 * (len(K.NODOS) + K.B.AMPS.index('vam_td'))])
    m = (t > 1.0e-6) & (t < 4.0e-6)
    pend = np.polyfit(t[m], vd[m], 1)[0]
    i = float(np.median(itd[m]))
    return i, pend, -pend * 2 * CU - i          # exceso = fuga


if __name__ == '__main__':
    print('=== A) la parasita de vw es la puerta de M5? ===')
    print('  %10s %10s %12s %12s %14s'
          % ('W5', 'L5', 'area pta', 'C0[uds]', 'C0[fF]'))
    for w5, l5 in ((0.50, 15.0), (0.50, 6.0), (0.22, 7.5), (0.50, 1.0)):
        r = extrae_C0(w5, l5)
        if r is None:
            print('  %10.2f %10.2f   RECHAZADO' % (w5, l5)); continue
        x, a, b = r
        print('  %10.2f %10.2f %12.2f %12.3f %14.1f'
              % (w5, l5, w5 * l5, x, x * CU * 1e15))

    print('\n=== B) de quien es la fuga de 20 pA? ===')
    print('  %10s %10s %12s %12s %12s'
          % ('W(M12)', 'rshunt', 'Itd[pA]', 'pend[V/s]', 'exceso[pA]'))
    for wm in (0.22, 0.50, 2.00):
        for rs in (True, False):
            r = fuga(wm, rs)
            if r is None:
                print('  %10.2f %10s   FALLO' % (wm, rs)); continue
            i, p, ex = r
            print('  %10.2f %10s %12.3f %12.4g %12.3f'
                  % (wm, 'si' if rs else 'NO', i * 1e12, p, ex * 1e12))
