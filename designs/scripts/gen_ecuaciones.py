"""Genera el documento con TODAS las ecuaciones, desde los ajustes."""
import itertools

import numpy as np

SAL = []
def P(s=''):
    SAL.append(s)


def poli(c, exps, nombres, ancho=74, sangria='    '):
    """Escribe un polinomio, terminos ordenados por magnitud."""
    ter = []
    for j, ex in enumerate(exps):
        t = ''.join(('%s%s' % (nombres[k], '' if ex[k] == 1 else '^%d' % ex[k]))
                    for k in range(len(ex)) if ex[k])
        ter.append((c[j], t))
    ter.sort(key=lambda x: -abs(x[0]))
    ln = sangria
    for v, t in ter:
        s = '%+.5f' % v + (('·' + t) if t else '')
        if len(ln) + len(s) > ancho:
            P(ln); ln = sangria
        ln += s + ' '
    P(ln)


def cubica4(y, X):
    E = [e for e in itertools.product(range(4), repeat=4) if sum(e) <= 3]
    B = np.column_stack([np.prod(X ** np.array(e), axis=1) for e in E])
    return np.linalg.lstsq(B, y, rcond=None)[0], E


# ============================ ENCODER =====================================
D = np.load('siete.npz'); G = D['geos']; R = D['res']
ok = (R[:, 3] > 0.15) & np.isfinite(R).all(1) & (R[:, 0] > 0)
X = np.log10(G[ok])
NG = ['a', 'b', 'd', 'e']

P('# Todas las ecuaciones (CapiMagics, GF180MCU)')
P()
P('Generado desde los ajustes. Procedencia y metodo: los knowledge base de')
P('`sch/encoder/results/` y `sch/integrator/results/`.')
P()
P('---')
P()
P('## ENCODER')
P()
P('Dimensiones fijas: `Ld = 1.60 um`, `W9 = 0.26 um`, espejo `Wo = 0.93`, `Lo = 1.86 um`.')
P('Variables libres: `Wd`, `Wl`, `Ll`, `L9` en um.')
P('Validas para `Vbias = 1.2 V`, `Vcm >= 1.55 V`, y dentro de la caja')
P('`Wd 0.26-1.80  Wl 0.30-2.70  Ll 0.28-0.62  L9 0.80-3.78`.')
P()
P('En todas: **a = lg10(Wd), b = lg10(Wl), d = lg10(Ll), e = lg10(L9)**')
P()

for nom, y, err, uni in [
        ('lg10( Iex(-) [A] )', np.log10(R[ok, 0]), '0.65 %', 'Iex a Vdif = -0.14 V'),
        ('lg10( Iex(+) [A] )', np.log10(R[ok, 1]), '0.58 %', 'Iex a Vdif = +0.14 V'),
        ('lg10( ganancia )', np.log10(R[ok, 2]), '0.26 %', 'dV(x)/dVdif en el centro'),
        ('V(a) [V]', R[ok, 3], '0.12 %', 'margen de saturacion de M9')]:
    c, E = cubica4(y, X)
    P('### %s' % uni)
    P()
    P('```')
    P('%s =' % nom)
    poli(c, E, NG)
    P('')
    P('   35 terminos.  Error externo %s' % err)
    P('```')
    P()

# --- viabilidad, sigma, ro, C_in (exactas, de coeffs.py) -------------------
import sys
sys.path.insert(0, r'C:\Users\Usuario\eda\CapiMagics\designs\scripts')
from encoder_design import coeffs as C

P('### Viabilidad: los tres objetivos no son independientes')
P()
P('```')
P('lg10( Iex(+) / Iex(-) )  =   con  A = lg10(Iex(-) [A]),  Gg = lg10(ganancia)')
P('    %+.5f  %+.5f·A  %+.5f·Gg  %+.5f·A²  %+.5f·Gg²  %+.5f·A·Gg'
  % tuple(C.VIABILIDAD))
P('')
P('   Error externo 1.26 %.  Reproducida por dos barridos independientes.')
P('```')
P()
P('### Desviacion de entrada por desapareamiento')
P()
P('```')
P('lg10( sigma_Vos [V] ) = %+.4f %+.4f·a %+.4f·b %+.4f·d %+.4f·e' % tuple(C.SIGMA_VOS))
P('')
P('   Error externo 5.6 %.  Manda `Ll`; `Wl` y `L9` no intervienen.')
P('```')
P()
P('### Impedancia de salida (la que NeuronSpec pide como `source_ro`)')
P()
P('```')
P('lg10( ro [ohm] ) = %+.4f %+.4f·lg10(Wo) %+.4f·lg10(Lo) %+.4f·lg10(Iex [A])'
  % tuple(C.RO_SALIDA))
P('')
P('   Error externo 9.4 %.  Con Wo=0.93 y Lo=1.86 fijos, solo depende de Iex.')
P('   Por encima de 126 nA el LIF ve mas del 1 % de error.')
P('```')
P()
P('### Capacidad de entrada')
P()
P('```')
P('lg10( C_in [F] ) = %+.4f %+.4f·a %+.4f·b %+.4f·d %+.4f·e' % tuple(C.C_IN))
P('')
P('   Error externo 0.73 %.  Depende casi solo de `Wd`.')
P('```')
P()

open('ECUACIONES.md', 'w', encoding='utf-8').write('\n'.join(SAL) + '\n')
print('escritas %d lineas' % len(SAL))
