"""Espejo bien parametrizado: Mp1 y Mp2 con L distinta para escalar."""
import sys
import numpy as np
sys.path.insert(0, '/tmp/stdp')
import carac_stdp as K
import polaridad as P

def lectura(txt, wn, ln, lp1=2.0, lp2=2.0, wp=0.5):
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

print('  Wn=0.22 Ln=6.0 (mejor linealidad medida). Se escala con L de Mp2.\n')
print('  %8s %10s %12s %12s %14s %10s'
      % ('L(Mp2)', 'razon', 'Imax[uA]', 'rango vw', 'linealidad[%]', 'area[um2]'))
for lp2 in (2.0, 4.0, 6.6, 10.0, 15.0):
    cel = lectura(K.BASE, 0.22, 6.0, lp1=2.0, lp2=lp2)
    r = P.barre_vw(cel)
    if r is None:
        print('  %8.2f   FALLO'%lp2); continue
    v, i = r; i = np.abs(i)*1e6
    imax = i.max()
    u = (i > 0.05*imax) & (i < 0.95*imax)
    rango = v[u].max()-v[u].min() if u.sum()>2 else 0
    c = np.polyfit(v[u], i[u], 1)
    lin = 100*np.abs(np.polyval(c,v[u])-i[u]).max()/imax
    area = 0.22*6.0 + 0.5*2.0 + 0.5*lp2
    print('  %8.2f %10.2f %12.3f %12.2f %14.1f %10.2f'
          % (lp2, lp2/2.0, imax, rango, lin, area))
print('\n  (M5 de hoy: 0.5 x 15 = 7.50 um2, Imax 2.353 uA, rango 2.40 V,')
print('   pero con el SIGNO INVERTIDO)')
