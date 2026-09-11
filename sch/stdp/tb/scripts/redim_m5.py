"""Redimensionar la salida de la sinapsis para que 4 en paralelo quepan.

Ninguna geometria del LIF acepta los 8924 nA que suman 4 sinapsis; el maximo
de todo su espacio es 2758 nA (W=3.5, L=50). Asi que el objetivo es
689 nA por sinapsis, y hay que bajarlo un factor 3.24 desde los 2231 de ahora.
"""
import sys
import numpy as np
sys.path.insert(0,'/tmp/stdp')
import carac_stdp as K
import polaridad as P

def lectura(txt, wn, ln, lp1, lp2, wp=0.5):
    out, dentro = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp'): dentro = True
        if dentro and t.startswith('M5 '):
            out.append('Mn  nd   vw avss avss nfet_03v3 W=%.4gu L=%.4gu nf=1'%(wn,ln))
            out.append('Mp1 nd   nd avdd avdd pfet_03v3 W=%.4gu L=%.4gu nf=1'%(wp,lp1))
            out.append('Mp2 iout nd avdd avdd pfet_03v3 W=%.4gu L=%.4gu nf=1'%(wp,lp2))
            continue
        out.append(l)
    return '\n'.join(out)

print('  objetivo: ~689 nA por sinapsis (4 x 689 = 2756, la ventana max del LIF)\n')
print('  %8s %8s %12s %12s %14s %10s'
      % ('W(Mp2)','L(Mp2)','Imax[nA]','x4 [nA]','rango vw[V]','area[um2]'))
for wp2, lp2 in ((0.5, 15.0), (0.5, 21.5), (0.22, 9.5), (0.22, 14.0), (0.5, 30.0)):
    cel = lectura(K.BASE, 0.22, 6.0, 2.0, lp2, wp=0.5)
    cel = cel.replace('Mp2 iout nd avdd avdd pfet_03v3 W=0.5u',
                      'Mp2 iout nd avdd avdd pfet_03v3 W=%.4gu' % wp2)
    r = P.barre_vw(cel)
    if r is None:
        print('  %8.2f %8.1f   FALLO' % (wp2, lp2)); continue
    v, i = r; i = np.abs(i)*1e9
    imax = i.max()
    u = (i > 0.05*imax) & (i < 0.95*imax)
    area = 0.22*6.0 + 0.5*2.0 + wp2*lp2
    print('  %8.2f %8.1f %12.1f %12.1f %14.2f %10.2f'
          % (wp2, lp2, imax, 4*imax, v[u].max()-v[u].min(), area))
