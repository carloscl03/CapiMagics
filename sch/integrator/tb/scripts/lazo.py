"""EL LAZO CERRADO del integrador: pedido -> motor -> ngspice -> comparar.

Es el unico examen que valida un motor de verdad. Del encoder aprendimos que el
error de la LEY y el del MOTOR no son lo mismo: la cuadratica parecia bastar por
error de ley (2.98 %) y en el lazo daba 21/25 contra 25/25 de la cubica, porque
el solver busca los bordes de la caja.

El modelo no toca ninguno de los dos lados: se le pide una banda, devuelve
geometria, y se simula esa geometria.
"""
import json, subprocess, sys, time
import numpy as np
import banco

PED = [(150, 1200), (300, 2400), (74, 600), (600, 4500),
       (150, 2400), (1200, 4500), (300, 1200), (74, 300)]

sol = json.load(open('pedidos.json'))
print('=== lazo cerrado: %d pedidos ===' % len(sol))
print('  %-14s %8s %10s %10s %9s %9s' %
      ('banda [kHz]', 'f', 'vm motor', 'vm ngspice', 'error', 'rizado err'))
sys.stdout.flush()

ev, er = [], []
for s in sol:
    g = (s['W1'], 0.28, s['W2'], s['L2'], s['Iref']*1e-9, s['W6'], s['L6'], s['C'])
    for f, vpred, rpred in ((s['f_lo'], s['vm_lo'], s['riz_lo']),
                            (s['f_hi'], s['vm_hi'], s['riz_hi'])):
        vic = [vpred]
        for _ in range(3):
            out = banco.mide([(g, f)], nset=12, nmed=8, tag='lz', vic=vic)[0]
            vic = [out['vm']]
            if abs(out['bal']) <= 1.5:
                break
        dv = 1000*(vpred - out['vm'])
        dr = 100*(rpred/out['riz'] - 1) if out['riz'] > 0 else float('nan')
        ev.append(abs(dv)); er.append(abs(dr))
        print('  %-14s %8.0f %9.3fV %9.3fV %+7.0fmV %+8.1f%%'
              % ('%d-%d' % (s['f_lo'], s['f_hi']), f, vpred, out['vm'], dv, dr))
        sys.stdout.flush()

ev = np.array(ev); er = np.array(er)
print()
print('  vm:     medio %.0f mV, peor %.0f mV   (%d de %d bajo 50 mV)'
      % (ev.mean(), ev.max(), (ev < 50).sum(), len(ev)))
print('  rizado: medio %.1f %%, peor %.1f %%' % (er.mean(), er.max()))
