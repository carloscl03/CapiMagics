"""El amperimetro de Itd esta en el FONDO de la pila. Entra mas por arriba?

VAM_td mide en MCM_9 -> avss. Pero los cuatro nodos intermedios (n6..n9) tienen
uniones propias, asi que la corriente que entra por MCM_5 desde `vdep` puede ser
mayor que la que sale. Seria el mismo error que el amperimetro de M16: medir el
extremo equivocado de un reparto.

Se anade un amperimetro ARRIBA (vdep -> MCM_5) y se comparan los dos extremos.
"""
import os, re, subprocess, sys
import numpy as np
sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

CU = 54.5e-15

def con_amp_arriba(txt):
    out, dentro = [], False
    for l in txt.splitlines():
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
    return '\n'.join(out)

cel = con_amp_arriba(K.caps(K.BASE, ndep=2))
AMPS = K.B.AMPS + ['vam_arr']
vec = ' '.join(['v(x1.%s)' % n for n in K.NODOS_INT] + ['v(vw)']
               + ['i(v.x1.%s)' % a for a in AMPS])
cuerpo = (K.bias(itd=0.50) + K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
          + K.quieto('vpre', 'nvpre'))
ctl = ['.ic v(vw)=1.65 v(x1.vdep)=0', '.control', 'tran 1n 4.2e-06',
       'wrdata fp.dat %s' % vec, '.endc', '.end']
cab = ['* fuga pila', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       K.B.MIM, cel, 'X1 %s stdp' % K.PUERTOS,
       'VDD avdd 0 3.3', 'VSS avss 0 0', 'VIO iout 0 0.9']
open('fp.spice', 'w').write('\n'.join(cab + cuerpo + ctl) + '\n')
subprocess.run(['/foss/tools/bin/ngspice', '-b', 'fp.spice'], capture_output=True, text=True)
A = np.loadtxt('fp.dat')
t = A[:, 0]; nv = len(K.NODOS)
V = {n: A[:, 1 + 2 * k] for k, n in enumerate(K.NODOS)}
I = {a: A[:, 1 + 2 * (nv + k)] for k, a in enumerate(AMPS)}
m = (t > 1.0e-6) & (t < 4.0e-6)
arr = float(np.median(np.abs(I['vam_arr'][m])))
aba = float(np.median(np.abs(I['vam_td'][m])))
pend = float(np.polyfit(t[m], V['vdep'][m], 1)[0])
print('  corriente que ENTRA por arriba (vdep -> MCM_5):  %8.3f pA' % (arr*1e12))
print('  corriente que SALE por abajo  (MCM_9 -> avss) :  %8.3f pA' % (aba*1e12))
print('  diferencia                                    :  %8.3f pA  (%.1f %%)'
      % ((arr-aba)*1e12, 100*(arr-aba)/aba))
print()
print('  pendiente medida      %10.4g V/s' % pend)
print('  -pend * Cdep          %8.3f pA   <- la corriente que de verdad sale de vdep'
      % (-pend*2*CU*1e12))
print('  con el amp de ARRIBA  exceso %8.3f pA' % ((-pend*2*CU - arr)*1e12))
print('  con el amp de ABAJO   exceso %8.3f pA' % ((-pend*2*CU - aba)*1e12))
