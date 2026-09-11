"""Matriz de acoplo del ENCODER, calculada de las leyes.

Cuatro dimensiones (Wd, Wl, Ll, L9) contra seis salidas. Es el sitio donde mas
probable es que aparezca otro caso como el `W4` del STDP: una perilla que yo
trato como palanca de calidad y que en realidad mueve numerador y denominador
por igual.

El punto nominal es el REF del desarrollo potencia x correccion.
"""
import sys

import numpy as np

sys.path.insert(0, 'designs/scripts')
from encoder_design import coeffs as C, laws as L

NOM = dict(Wd=0.725, Wl=0.947, Ll=0.394, L9=1.811)


def sal(p):
    q = dict(NOM)
    q.update(p)
    a = (q['Wd'], q['Wl'], q['Ll'], q['L9'])
    # UNIDADES: iex_min y iex_max en nA, c_in en fF, sigma en V.
    # Antes multiplicaba por 1e9 lo que ya venia en nA, y a `source_ro` le
    # pasaba 8e10 nA: esa columna salia en 1e-20 ohm, sin sentido.
    imin = L.iex_min(*a)
    g = L.gain(*a)
    return dict(iex_min=imin, gain=g, iex_max=L.iex_max(imin, g),
                c_in=L.c_in(*a), area=L.area(*a),
                sigma=L.sigma_vos(*a), va=abs(L.v_a(*a)),
                ro=L.source_ro(imin))


SAL = ['iex_min', 'gain', 'iex_max', 'c_in', 'area', 'sigma', 'va', 'ro']
CAB = {'iex_min': 'Iex-', 'gain': 'G', 'iex_max': 'Iex+', 'c_in': 'C_in',
       'area': 'area', 'sigma': 'sVos', 'va': 'V(a)', 'ro': 'r_o'}

base = sal({})
print('  ENCODER -- d(ln salida)/d(ln perilla) en el punto nominal')
print('  +1 proporcional   ~0 ORTOGONAL   -1 inversa\n')
print('  %-6s' % 'dim' + ''.join('%9s' % CAB[s] for s in SAL))
for k in ('Wd', 'Wl', 'Ll', 'L9'):
    v = NOM[k]
    d = 1.02
    hi, lo = sal({k: v * d}), sal({k: v / d})
    fila = '  %-6s' % k
    for s in SAL:
        if lo[s] <= 0 or hi[s] <= 0:
            fila += '%9s' % '-'
            continue
        e = (np.log(hi[s]) - np.log(lo[s])) / (2 * np.log(d))
        fila += '%9s' % ('~0' if abs(e) < 0.02 else '%+.2f' % e)
    print(fila)
print()
print('  valores en el nominal:')
for s in SAL:
    u = {'iex_min': 'nA', 'iex_max': 'nA', 'c_in': 'fF', 'area': 'um2',
         'sigma': 'V', 'va': 'V', 'ro': 'ohm'}.get(s, '')
    print('    %-8s %12.4g %s' % (CAB[s], base[s], u))
