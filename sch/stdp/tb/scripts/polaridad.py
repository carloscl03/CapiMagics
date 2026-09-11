"""La lectura del peso tiene el signo invertido. Se arregla y se mide.

CADENA TRAZADA:
  paper, linea 162:  "When Dt < 0 (Dt > 0), VW is decreased (increased) by the
                      depression (potentiation) circuit"
  celda:             potenciacion sube vw (+146.76 mV medido)   -> DE ACUERDO
  M5 iout vw avdd avdd pfet:  vw arriba -> Vsg abajo -> MENOS Iout
  neurona:           XC2 Iin vss cap_mim  -> Iin ES la membrana, y la corriente
                     que ENTRA la carga hacia el umbral

  => potenciar reduce la corriente que recibe la neurona: INVERTIDO.

Un pfet con la puerta en `vw` tiene transconductancia negativa por
construccion; no hay geometria que lo arregle. Y un nfet solo DRENA de `iout`,
cuando la membrana necesita que le inyecten. Hace falta transconductor + espejo.

Se comparan las dos lecturas con el MISMO nucleo y el mismo evento.
"""
import os
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S


def con_lectura_nueva(txt, wn=0.5, ln=2.0, wp=0.5, lp=2.0):
    """Sustituye M5 por transconductor nfet + espejo pfet."""
    out, dentro = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp'):
            dentro = True
        if dentro and t.startswith('M5 '):
            out.append('Mn  nd   vw avss avss nfet_03v3 W=%.4gu L=%.4gu nf=1' % (wn, ln))
            out.append('Mp1 nd   nd avdd avdd pfet_03v3 W=%.4gu L=%.4gu nf=1' % (wp, lp))
            out.append('Mp2 iout nd avdd avdd pfet_03v3 W=%.4gu L=%.4gu nf=1' % (wp, lp))
            continue
        out.append(l)
    return '\n'.join(out)


def barre_vw(cel, vout=0.9):
    import subprocess
    cuerpo = (K.bias() + ['VWS vw 0 0', 'VIO2 iout 0 %.3f' % vout]
              + K.quieto('vpre', 'nvpre') + K.quieto('vpost', 'nvpost'))
    ctl = ['.control', 'dc VWS 0 3.3 0.1', 'wrdata SALIDA i(VIO2)', '.endc', '.end']
    sp, dat = 'pol_%d.spice' % K.PID, 'pol_%d.dat' % K.PID
    P = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
    cab = ['* polaridad', '.include %s/design.ngspice' % P,
           '.lib %s/sm141064.ngspice typical' % P, '.option rshunt=1e12',
           K.B.MIM, cel, 'X1 %s stdp' % K.PUERTOS,
           'VDD avdd 0 3.3', 'VSS avss 0 0']
    open(sp, 'w').write('\n'.join(cab + cuerpo + ctl).replace('SALIDA', dat) + '\n')
    subprocess.run(['/foss/tools/bin/ngspice', '-b', sp], capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None
    return A[:, 0], A[:, 1]


if __name__ == '__main__':
    print('  Iout en funcion de vw.  SIGNO de i(VIO2): positivo = la fuente')
    print('  absorbe, o sea que la celda INYECTA en iout (que es lo que la')
    print('  membrana necesita).\n')
    print('  %8s %16s %16s' % ('vw[V]', 'HOY (pfet)', 'ARREGLO (n+espejo)'))
    a = barre_vw(K.BASE)
    b = barre_vw(con_lectura_nueva(K.BASE))
    if a is None or b is None:
        print('  FALLO'); sys.exit()
    for k in range(0, len(a[0]), 4):
        print('  %8.2f %16.4g %16.4g' % (a[0][k], a[1][k] * 1e6, b[1][k] * 1e6))
    print('\n  pendiente (uA/V) en vw=1.65:')
    for nom, (v, i) in (('hoy', a), ('arreglo', b)):
        k = int(np.argmin(np.abs(v - 1.65)))
        m = np.polyfit(v[k-3:k+4], i[k-3:k+4], 1)[0]
        print('    %-10s %+10.4f   ->  %s' % (nom, m * 1e6,
              'potenciar SUBE Iout' if m > 0 else 'potenciar BAJA Iout (INVERTIDO)'))
