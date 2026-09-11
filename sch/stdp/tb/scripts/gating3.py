"""La puerta va en el TRANSCONDUCTOR, no en la salida del espejo.

Con la puerta en la salida, el espejo sigue empujando corriente al nodo
intermedio mientras esta cortada: se carga hasta avdd y al abrir vuelca de
golpe. Por eso el paquete salia de 120-223 fC en vez de los ~8 que da
`Iout x tp`, y ademas dependia de la frecuencia (mas tiempo, mas acumulacion).

Cortando en la fuente de Mn no circula NADA mientras el pre esta callado, y
durante el spike el espejo entrega su corriente limpia.
"""
import sys
import numpy as np
sys.path.insert(0,'/tmp/stdp')
import gating as G

def con_puerta_abajo(txt):
    out, d = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp'): d = True
        if d and t.startswith('Mn '):
            out.append(t.replace(' avss avss ', ' ng   avss '))
            out.append('Mg  ng vpre avss avss nfet_03v3 W=0.5u L=0.28u nf=1')
            continue
        out.append(l)
    return '\n'.join(out)

G.CEL = con_puerta_abajo(open('/tmp/stdp/stdp_propuesta.spice').read())
print('  puerta en la FUENTE del transconductor\n')
print('  %14s %16s %16s' % ('f pre [kHz]','Iout medio[nA]','carga/spike[fC]'))
for f in (0, 100, 500, 1000, 2000):
    v = G.carga_media(f)*1e9
    q = (v*1e-9/(f*1e3)*1e15) if f else 0
    print('  %14s %16.4f %16s' % ('callado' if f==0 else '%d'%f, v,
          '--' if not f else '%.3f' % q))
print()
print('  esperado: Iout(pico) x tp = 252 nA x 33 ns = 8.3 fC, constante con f')
