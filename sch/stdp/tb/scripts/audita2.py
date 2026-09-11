"""Llamar al codigo ORIGINAL del barrido C, no a una reimplementacion mia.

Mi reproduccion dio vw(0) = 0.2887 con 9 avisos, pero los numeros que el
barrido C publico solo son coherentes con arrancar en 1.65. Una de las dos
cosas esta mal, y hasta saberlo no se puede confiar en NINGUNA de las dos.
"""
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, '/tmp/stdp')
import barCE as C
import stdp_banco as SB

# se intercepta la llamada al simulador para quedarse con los avisos
_orig = subprocess.run
ultimo = {}


def espia(*a, **k):
    r = _orig(*a, **k)
    txt = (r.stdout or '') + (r.stderr or '')
    ultimo['avisos'] = len(re.findall(r'singular|failed|not found', txt, re.I))
    ultimo['ic'] = len(re.findall(r'non-existent|IC on', txt, re.I))
    return r


subprocess.run = espia

print('--- barrido C original, tal cual, nCW = 5 ---')
cel = C.con_cw(SB.CEL, 5)
for etiq, con_post in (('blanco (sin post)', False), ('senal  (post+pre)', True)):
    d, _ = C.evento(2.32, cel, 200e-9, 200e-9 + 100e-9, 200e-9 + 100e-9 + 300e-9,
                    con_post=con_post)
    if d is None:
        print('  %-20s  sin datos' % etiq)
        continue
    vw = d['V']['vw']
    print('  %-20s  avisos %3d  avisos_ic %2d  vw(0) %8.4f  vw(fin) %8.4f  '
          'DVw(vs 1.65) %9.4f mV  DVw(real) %9.4f mV'
          % (etiq, ultimo['avisos'], ultimo['ic'], vw[0], vw[-1],
             (vw[-1] - 1.65) * 1e3, (vw[-1] - vw[0]) * 1e3))

print('\n--- y el barrido B original (vdep forzado), nCW = 10 ---')
import barABD as A
for vd in (0.0, 0.8):
    cuerpo = A.bias() + [
        'VFD vdepf 0 %.4f' % vd,
        'VPRE vpre 0 PULSE(0 3.3 %.4g 1n 1n %.4g 1)' % (A.T0 if hasattr(A, 'T0') else 200e-9, 33e-9),
        'VNPRE nvpre 0 PULSE(3.3 0 %.4g 1n 1n %.4g 1)' % (200e-9, 33e-9),
        'VPOST vpost 0 0', 'VNPOST nvpost 0 3.3']
    ctl = ['.ic v(vw)=1.65', '.control', 'tran 0.2n 7e-07',
           'wrdata SALIDA %s' % ' '.join(SB.vec_v() + SB.vec_i()), '.endc', '.end']
    M, _ = A.corre(cuerpo, ctl, SB.CEL_F, extra_puertos=' vdepf')
    if M is None:
        print('  vdep=%.2f  sin datos' % vd)
        continue
    vw = M[:, 1 + 2 * SB.NODOS.index('vw')]
    print('  vdep=%.2f  avisos %3d  vw(0) %8.4f  DVw(vs 1.65) %9.4f mV  '
          'DVw(real) %9.4f mV'
          % (vd, ultimo['avisos'], vw[0], (vw[-1] - 1.65) * 1e3,
             (vw[-1] - vw[0]) * 1e3))
