"""Impedancias de acoplo de la celda STDP, como en el encoder y el integrador.

Los nodos que tocan al exterior, y por que importa cada uno:

  vpre, nvpre, vpost, nvpost   ENTRADAS. Son carga capacitiva para los
      inversores de salida de la neurona. El motor del LIF tiene
      `c_load_max(w_m7m8)` y `i_drive(w_m7m8)`: hay que pasarle esto en vez de
      suponerlo. Y en el 4x2 cada linea `pre` mueve 2 sinapsis y cada `post` 4.

  iout   SALIDA. Va a `ifwd`, que es el nodo `Iin` de la neurona siguiente --
      o sea LA MEMBRANA. Dos cosas:
        R_out  si es baja, la corriente entregada depende de la tension de
               membrana, que se mueve en todo el ciclo
        C_out  SE SUMA A Cm. Con 4 sinapsis por neurona, eso desplaza el
               umbral y la excursion, que en el LIF SI dependen de Cm.

  vw     es PIN del LEF (vw11, vw12...). Si alguien lo lee o lo inicializa,
      su impedancia manda.

Metodo: analisis .ac con una fuente de tension en el nodo; Y = I/V,
C = imag(Y)/(2*pi*f), R = 1/real(Y).
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import stdp_banco as B

P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
CEL = open('stdp_propuesta.spice').read()
PID = os.getpid()


def admitancia(nodo, dc, freq=1e6):
    """C y R vistos en `nodo`, con el resto de la celda en reposo."""
    fijos = {'vpre': 0.0, 'nvpre': 3.3, 'vpost': 0.0, 'nvpost': 3.3,
             'vw': 1.65, 'iout': 0.9}
    cuerpo = list(K.bias())
    for n, v in fijos.items():
        if n == nodo:
            continue
        cuerpo.append('V%s %s 0 %.4f' % (n.upper(), n, v))
    cuerpo.append('VM %s 0 %.4f AC 1' % (nodo, dc))
    ctl = ['.control', 'ac lin 1 %g %g' % (freq, freq),
           'wrdata im_%d.dat real(i(VM)) imag(i(VM))' % PID, '.endc', '.end']
    cab = ['* impedancia', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           B.MIM, CEL, 'X1 %s stdp' % K.PUERTOS,
           'VDD avdd 0 3.3', 'VSS avss 0 0']
    sp = 'im_%d.spice' % PID
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', sp],
                   capture_output=True, text=True)
    try:
        A = np.atleast_2d(np.loadtxt('im_%d.dat' % PID))
    except Exception:
        return None
    re_, im_ = A[0, 1], A[0, 3]
    C = abs(im_) / (2 * np.pi * freq)
    R = 1.0 / abs(re_) if abs(re_) > 1e-15 else float('inf')
    return C, R


def r_out_iout():
    """dI/dV en `iout` barriendo la tension de carga: lo que la membrana ve."""
    cuerpo = (K.bias() + ['VWS vw 0 1.65', 'VIO iout 0 0']
              + K.quieto('vpre', 'nvpre') + K.quieto('vpost', 'nvpost'))
    ctl = ['.control', 'dc VIO 0.2 2.4 0.1',
           'wrdata ro_%d.dat i(VIO)' % PID, '.endc', '.end']
    cab = ['* r_out', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           B.MIM, CEL, 'X1 %s stdp' % K.PUERTOS,
           'VDD avdd 0 3.3', 'VSS avss 0 0']
    sp = 'ro_%d.spice' % PID
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', sp],
                   capture_output=True, text=True)
    try:
        A = np.loadtxt('ro_%d.dat' % PID)
    except Exception:
        return None
    v, i = A[:, 0], A[:, 1]
    g = np.polyfit(v, i, 1)[0]
    return 1.0 / abs(g) if abs(g) > 1e-15 else float('inf'), i.mean()


if __name__ == '__main__':
    print('  === ENTRADAS: lo que la neurona tiene que mover ===')
    print('  %-10s %8s %12s %14s' % ('nodo', 'DC[V]', 'C_in[fF]', 'R[ohm]'))
    tot_pre = tot_post = 0.0
    for n, dc in (('vpre', 0.0), ('nvpre', 3.3), ('vpost', 0.0), ('nvpost', 3.3)):
        r = admitancia(n, dc)
        if r is None:
            print('  %-10s   FALLO' % n); continue
        C, R = r
        print('  %-10s %8.2f %12.4f %14.3g' % (n, dc, C * 1e15, R))
        if 'pre' in n:
            tot_pre += C
        else:
            tot_post += C
    print('  -> por sinapsis: pre %.2f fF, post %.2f fF' % (tot_pre*1e15, tot_post*1e15))
    print('     en el 4x2: cada linea pre mueve 2 sinapsis (%.2f fF),'
          % (2*tot_pre*1e15))
    print('                cada linea post mueve 4 (%.2f fF)' % (4*tot_post*1e15))

    print('\n  === SALIDA: lo que se suma a la membrana ===')
    r = admitancia('iout', 0.9)
    if r:
        print('  C_out por sinapsis     %10.4f fF' % (r[0]*1e15))
        print('  con 4 sinapsis         %10.4f fF   <- SE SUMA A Cm (280 fF)'
              % (4*r[0]*1e15))
    ro = r_out_iout()
    if ro:
        print('  R_out                  %10.4g ohm   (I media %.4g uA)'
              % (ro[0], ro[1]*1e6))

    print('\n  === vw, que es pin del LEF ===')
    r = admitancia('vw', 1.65)
    if r:
        print('  C en vw                %10.4f fF' % (r[0]*1e15))
        print('  R en vw                %10.4g ohm' % r[1])
