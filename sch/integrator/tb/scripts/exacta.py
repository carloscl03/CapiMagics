"""La geometria EXACTA que el solver eligio, medida con asentamiento validado.

Sin comparar con nada de otra tanda: motor contra ngspice, mismo circuito,
mismo banco, y el balance de carga como testigo.
"""
import json, sys
import numpy as np
import banco

sol = json.load(open('pedidos.json'))
print('=== motor contra ngspice, geometria por geometria ===')
print('  %-11s %6s %8s %9s %9s %9s %9s %8s %7s' %
      ('banda', 'f', 'vm mot', 'vm spice', 'riz mot', 'riz spice', 'I_fuga', 'q', 'bal'))
sys.stdout.flush()
for s in sol:
    g = (s['W1'], 0.28, s['W2'], s['L2'], s['Iref']*1e-9, s['W6'], s['L6'], s['C'])
    for f, vp, rp in ((s['f_lo'], s['vm_lo'], s['riz_lo']),
                      (s['f_hi'], s['vm_hi'], s['riz_hi'])):
        vic = [vp]
        o = None
        for _ in range(4):
            o = banco.mide([(g, f)], nset=16, nmed=8, tag='ex', vic=vic)[0]
            vic = [o['vm']]
            if abs(o['bal']) <= 1.0:
                break
        q = (o['riz']*1e-3 * s['C']*1e-15 * f*1e3 / (o['ifuga']*1e-9)
             if o['ifuga'] > 0 else float('nan'))
        print('  %-11s %6d %7.3fV %8.3fV %8.3f %9.3f %8.2fnA %7.2f %6.2f%%'
              % ('%d-%d' % (s['f_lo'], s['f_hi']), f, vp, o['vm'], rp, o['riz'],
                 o['ifuga'], q, o['bal']))
        sys.stdout.flush()
