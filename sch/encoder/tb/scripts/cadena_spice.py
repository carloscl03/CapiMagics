"""Validacion en SPICE de la cadena ENTERA, con las celdas conectadas de verdad.

Hasta ahora `cadena.py` COMPONE LEYES: evalua la ley de un bloque en el borde
de la ley de otro. Eso no es una validacion. Nuestra propia regla dice que el
error de la ley y el del motor no son lo mismo; por extension, el de la cadena
tampoco es la suma de los de los bloques. En el integrador tres leyes de 2-5 %
componian 43 mV.

Topologia:

    encoder --Iex_1--> LIF1 --spike--> 4 x STDP --iout--> LIF2 --spike--> integrador
                                          ^                  |
                                          +---- vpost -------+

El lazo de realimentacion es REAL y a proposito: el post de las sinapsis es la
neurona de salida, que es lo que hace que el STDP sea STDP.

Lo que se quiere ver:
  1. arranca y converge?
  2. la frecuencia de la capa 1 es la que la cadena predice?
  3. LAS IMPEDANCIAS: la capa 1 mueve la carga de las 4 sinapsis sin degradar
     su spike? la corriente que entra en la capa 2 es la que se calculo?
  4. la ganancia por etapa medida, contra el 0.925 calculado
"""
import os
import subprocess
import sys

import numpy as np

R = '/root/CapiMagics' if os.path.isdir('/root/CapiMagics') else '/foss/designs'
P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
os.chdir('/tmp/cad')

ENC = 'libs/snn_analog/encoder/encoder_lvs.spice'
LIF = 'libs/snn_analog/lif/neurona_sch.spice'
STDP = 'libs/snn_analog/stdp/stdp_propuesta.spice'
INT = 'libs/snn_analog/Integrator/integrator_sch.spice'

VB = dict(itd=0.60, pot=1.30, idep=2.32, itp=2.60)
PESOS = [1.0, 1.2, 1.4, 1.6]     # vw inicial de cada sinapsis, en V


def netlist(vin_dif, tf=60e-6, n_syn=4):
    L = ['* cadena completa: encoder -> LIF -> STDP -> LIF -> integrador',
         '.include %s/design.ngspice' % P,
         '.lib %s/sm141064.ngspice typical' % P,
         '.option rshunt=1e12',
         open('/tmp/cad/mimfull.spice').read(),
         '.include %s/%s' % (R, ENC),
         '.include %s/%s' % (R, LIF),
         '.include /tmp/cad/stdp_propuesta.spice',
         '.include %s/%s' % (R, INT),
         '',
         'VDD vdd 0 3.3', 'VSS vss 0 0',
         '* entrada diferencial del encoder, centrada en 1.65',
         'VIN  vin  0 %.6f' % (1.65 + vin_dif / 2),
         'VINN vinn 0 %.6f' % (1.65 - vin_dif / 2),
         '',
         '* --- encoder: 4 salidas, se usa la primera ---',
         'Xenc vdd vss vin vinn iex1 iex2 iex3 iex4 encoder',
         '* las otras tres se terminan para que no floten',
         'Rt2 iex2 vss 1G', 'Rt3 iex3 vss 1G', 'Rt4 iex4 vss 1G',
         '',
         '* --- capa 1 ---',
         'VAMI iex1 iex1n 0', 'Xn1 iex1n vdd vss spk1 spkn1 neurona_lvs',
         '',
         '* --- bias de las sinapsis ---',
         'VBITD vb_itd 0 %.4f' % VB['itd'],
         'VBPOT vb_pot 0 %.4f' % VB['pot'],
         'VBIDEP vb_idep 0 %.4f' % VB['idep'],
         'VBITP vb_itp 0 %.4f' % VB['itp'],
         '']
    L.append('* --- %d sinapsis: pre = capa 1, post = capa 2, salidas sumadas ---'
             % n_syn)
    for k in range(n_syn):
        L.append('Xs%d vdd vss spkn1 spkn2 spk1 spk2 vb_itd vb_idep vb_itp '
                 'vb_pot vw%d ifwd stdp' % (k, k))
    L.append('')
    L.append('* --- capa 2, alimentada por la suma ---')
    L.append('VAMF ifwd ifwdn 0')
    L.append('Xn2 ifwdn vdd vss spk2 spkn2 neurona_lvs')
    L.append('')
    L.append('* --- integrador, leyendo la capa 2 ---')
    L.append('VIREF iref 0 0')
    L.append('Xig vss spk2 iref vdd integrator')
    L.append('IREF vdd iref 12n')
    L.append('')
    L.append('* condiciones iniciales de los pesos')
    ics = ' '.join('v(vw%d)=%.4f' % (k, PESOS[k % len(PESOS)])
                   for k in range(n_syn))
    L.append('.ic %s' % ics)
    L.append('.control')
    L.append('tran 5n %.6g' % tf)
    vec = ['i(VAMI)', 'v(spk1)', 'v(spk2)', 'i(VAMF)']
    vec += ['v(vw%d)' % k for k in range(n_syn)]
    #  es PUERTO de la neurona: a nivel superior se llama iex1/ifwd,
    # no xn1.iin.  del integrador SI es interno. Tercera vez que
    # tropiezo con esto en la misma sesion.
    vec += ['v(xig.n1)']
    L.append('wrdata cad.dat %s i(vdd) i(vss)' % ' '.join(vec))
    L.append('.endc')
    L.append('.end')
    return '\n'.join(L) + '\n'


def corre(vin_dif, tf=60e-6):
    open('cad.spice', 'w').write(netlist(vin_dif, tf))
    r = subprocess.run(['/foss/tools/bin/ngspice', '-b', 'cad.spice'],
                       capture_output=True, text=True)
    try:
        A = np.loadtxt('cad.dat')
    except Exception:
        return None, r
    return A, r


def frec(t, v, umbral=1.65):
    """Frecuencia [kHz] contando cruces de subida."""
    s = (v[:-1] < umbral) & (v[1:] >= umbral)
    idx = np.where(s)[0]
    if len(idx) < 3:
        return 0.0
    dt = np.diff(t[idx])
    return 1e-3 / np.median(dt)


if __name__ == '__main__':
    print('  Vdif   Iex1[nA]   f capa1[kHz]  f capa2[kHz]  ifwd[nA]  vm_int[V]')
    for vd in (-0.10, 0.0, 0.10):
        A, r = corre(vd)
        if A is None:
            err = [l for l in (r.stderr + r.stdout).splitlines()
                   if 'rror' in l or 'annot' in l][:2]
            print('  %6.2f   FALLO: %s' % (vd, err))
            continue
        t = A[:, 0]
        c = {n: A[:, 1 + 2 * k] for k, n in enumerate(
            ['iex1', 'spk1', 'spk2', 'ifwd', 'vw0', 'vw1', 'vw2', 'vw3',
             'vmint'])}
        m = t > 0.3 * t[-1]
        # Iex e ifwd son NODOS, no corrientes: se saca la corriente de la
        # carga integrando el nodo no vale. Se mide con las tensiones y las
        # leyes inversas, o mejor: se anaden amperimetros. Aqui se reporta la
        # tension de los nodos, que ya dice si estan vivos.
        print('  %6.2f   %8.4f   %12.1f  %12.1f  %8.4f  %9.4f'
              % (vd, 1e9*float(np.mean(np.abs(c['iex1'][m]))), frec(t[m], c['spk1'][m]),
                 frec(t[m], c['spk2'][m]), 1e9*float(np.mean(np.abs(c['ifwd'][m]))),
                 float(np.mean(c['vmint'][m]))))
