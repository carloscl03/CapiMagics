"""Los dos que faltan y son baratos.

M12 -- ESCRIBE LA TRAZA, y es el que fija el TECHO.
  `Vdep0` satura porque la fuente de M12 *es* `vdep`: al subir la traza su
  `Vgs` se cierra solo. O sea que el techo es `Vpost - Vth(M12)`, y con el
  canal corto el `Vth` se mueve. Se mide la meseta (Dtp largo) y el valor con
  el spike real del LIF (33 ns), que es lo que de verdad se usa.

M5 -- LEE EL PESO.
  Medido a UNA sola geometria: `Iout` de 0 a 2.35 uA e independiente de la
  carga al 0.11 % con L=15u. La pregunta de diseno es cuanto `L` hace falta
  para esa independencia, porque 15 um es mucha area.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

W12 = [0.22, 0.35, 0.50, 1.00, 2.00]
L12 = [0.28, 0.45, 0.63, 1.20, 2.50]
W5 = [0.22, 0.50, 1.00]
L5 = [1.0, 3.0, 6.0, 10.0, 15.0]
DTP = [33e-9, 200e-9]


def techo(W, L, dtp):
    """Vdep0 alcanzado con el pulso dado."""
    cel = K.caps(S.dim(K.BASE, ['M12'], W, L), ndep=2)
    cuerpo = (K.bias() + K.pulso('vpost', 'nvpost', K.T0, dtp)
              + K.quieto('vpre', 'nvpre'))
    d = K.corre(cuerpo, K.tran(K.T0 + dtp + 300e-9), cel)
    if not K.arranco_bien(d):
        return None
    return float(d['V']['vdep'].max() - d['V']['vdep'][0])


def lector(W, L, vout):
    """Iout(vw) en continua, con la salida a `vout`."""
    cel = S.dim(K.BASE, ['M5'], W, L)
    cuerpo = (K.bias() + ['VWS vw 0 0', 'VIO2 iout 0 %.3f' % vout]
              + K.quieto('vpre', 'nvpre') + K.quieto('vpost', 'nvpost'))
    ctl = ['.control', 'dc VWS 0 3.3 0.1', 'wrdata SALIDA i(VIO2)', '.endc', '.end']
    sp, dat = 'cs_%d.spice' % K.PID, 'cs_%d.dat' % K.PID
    cab = ['* m5', '.include %s/design.ngspice' % '/foss/pdks/gf180mcuD/libs.tech/ngspice',
           '.lib %s/sm141064.ngspice typical' % '/foss/pdks/gf180mcuD/libs.tech/ngspice',
           '.option rshunt=1e12', K.B.MIM, cel,
           'X1 %s stdp' % K.PUERTOS, 'VDD avdd 0 3.3', 'VSS avss 0 0']
    import subprocess
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl).replace('SALIDA', dat) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', sp], capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None
    return A[:, 0], np.abs(A[:, 1])


if __name__ == '__main__':
    t0 = time.time()
    print('=== M12: el techo de la traza ===', flush=True)
    print('  %6s %6s %12s %12s %10s'
          % ('W', 'L', 'V0@33ns', 'V0@200ns(mes)', 'alcanzado'), flush=True)
    f = []
    for W in W12:
        for L in L12:
            a, b = techo(W, L, DTP[0]), techo(W, L, DTP[1])
            if a is None or b is None:
                print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True); continue
            f.append((W, L, a, b))
            print('  %6.2f %6.2f %12.4f %12.4f %9.1f %%'
                  % (W, L, a, b, 100 * a / b), flush=True)
            np.savez('m12.npz', filas=np.array(f, float))
    print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)

    print('\n=== M5: lectura del peso ===', flush=True)
    print('  %6s %6s %12s %12s %14s'
          % ('W', 'L', 'Iout@vw=0', 'Iout@1.65', 'indep carga[%]'), flush=True)
    g = []
    for W in W5:
        for L in L5:
            r0 = lector(W, L, 0.0)
            r9 = lector(W, L, 0.9)
            if r0 is None or r9 is None:
                print('  %6.2f %6.2f   FALLO' % (W, L), flush=True); continue
            v, i0 = r0
            _, i9 = r9
            k = int(np.argmin(np.abs(v - 1.65)))
            dif = 100 * np.median(np.abs(i9[i0 > 1e-9] / i0[i0 > 1e-9] - 1))
            g.append((W, L, i0[0], i0[k], dif))
            print('  %6.2f %6.2f %12.4g %12.4g %14.3f'
                  % (W, L, i0[0], i0[k], dif), flush=True)
            np.savez('m5.npz', filas=np.array(g, float))
    print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)
