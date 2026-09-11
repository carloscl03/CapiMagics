"""Las tres cajas que quedan sin distinguir borde-de-barrido de limite fisico.

  itd   (0.115, 7.4) nA. El 0.115 es donde deje de medir. Importa porque el
        arreglo del acoplo con la neurona pide 0.24 nA, y alguien podria querer
        ventanas aun mas largas. Se baja hasta que algo se rompa DE VERDAD y se
        anota que fue.

  W1    (0.23, 1.70) um. El 1.70 es el ultimo punto del barrido. Se extiende
        hasta que la amplitud sature o la ley se degrade.

  Vdep  [0.50, 1.00] V. Los dos bordes TIENEN razon fisica medida y solo hay
        que documentarla: por debajo la senal se entierra en el suelo, por
        encima la ventana pierde la forma exponencial (medido en barE). Se
        cuantifican los dos.
"""
import os
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

CU = 54.5e-15
P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'


def decae(vbitd, ncdep=2):
    """Pendiente medida contra Itd/Cdep, con el amperimetro en la ENTRADA."""
    import re
    cel = K.caps(K.BASE, ndep=ncdep)
    out, dentro = [], False
    for l in cel.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp'):
            dentro = True
        if dentro and t.startswith('MCM_5 '):
            out.append(t.replace('MCM_5 vdep ', 'MCM_5 vdtx '))
            continue
        if dentro and t.startswith('.ends'):
            out.append('VAM_arr vdep vdtx 0')
            dentro = False
        out.append(l)
    cel = '\n'.join(out)
    AMPS = K.B.AMPS + ['vam_arr']
    vec = ' '.join(['v(x1.%s)' % n for n in K.NODOS_INT] + ['v(vw)']
                   + ['i(v.x1.%s)' % a for a in AMPS])
    cuerpo = (['VBITD vb_itd 0 %.4f' % vbitd, 'VBPOT vb_pot 0 1.30',
               'VBIDEP vb_idep 0 2.32', 'VBITP vb_itp 0 2.60']
              + K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
              + K.quieto('vpre', 'nvpre'))
    ctl = ['.ic v(vw)=1.65 v(x1.vdep)=0', '.control', 'tran 2n 2.1e-05',
           'wrdata cj.dat %s' % vec, '.endc', '.end']
    cab = ['* caja itd', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           K.B.MIM, cel, 'X1 %s stdp' % K.PUERTOS,
           'VDD avdd 0 3.3', 'VSS avss 0 0', 'VIO iout 0 0.9']
    open('cj.spice', 'w').write('\n'.join(cab + cuerpo + ctl) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', 'cj.spice'],
                   capture_output=True, text=True)
    try:
        A = np.loadtxt('cj.dat')
    except Exception:
        return None
    t = A[:, 0]
    nv = len(K.NODOS)
    vd = A[:, 1 + 2 * K.NODOS.index('vdep')]
    ii = np.abs(A[:, 1 + 2 * (nv + AMPS.index('vam_arr'))])
    m = (t > 3e-6) & (t < 18e-6)
    if m.sum() < 20:
        return None
    pend = float(np.polyfit(t[m], vd[m], 1)[0])
    I = float(np.median(ii[m]))
    esp = -I / (ncdep * CU)
    return I, pend, 100 * (pend - esp) / abs(esp), 73.9e-3 / abs(pend)


if __name__ == '__main__':
    t0 = time.time()
    print('=== caja de `itd`: hasta donde baja antes de romperse ===', flush=True)
    print('  %8s %12s %14s %10s %12s'
          % ('vb_itd', 'Itd[pA]', 'pendiente[V/s]', 'err[%]', 'tau[us]'), flush=True)
    for vb in (0.50, 0.46, 0.42, 0.38, 0.34, 0.30, 0.25, 0.20):
        r = decae(vb)
        if r is None:
            print('  %8.2f   sin datos utiles' % vb, flush=True); continue
        I, pend, err, tau = r
        print('  %8.2f %12.4f %14.4g %10.2f %12.2f'
              % (vb, I * 1e12, pend, err, tau * 1e6), flush=True)
    print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)
