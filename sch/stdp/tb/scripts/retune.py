"""Con M4 estrecho, donde queda el nulo de M3?

Las dos palancas se suman (interferencia -3.3 %), pero el objetivo es ANULAR el
suelo, no desplazarlo lo mas posible. M3 solo ya cruza cero; sumarle M4 se pasa.
Asi que con M4 en 0.22/0.28 hay que reajustar la L de M3.
"""
import sys
sys.path.insert(0, '/tmp/stdp')
import comp_suelo as C

M4 = (0.22, 0.28)
print('  M4 fijo en %.2f/%.2f  ->  se busca la L de M3 que anula\n' % M4)
print('  %6s %6s %12s %12s %10s' % ('W(M3)', 'L(M3)', 'suelo[mV]', 'senal[mV]', 'ratio'))
for W in (0.22, 0.30, 0.50):
    for L in (1.50, 2.20, 3.00, 4.00, 6.00):
        s = C.caso((W, L), M4)
        g = C.caso((W, L), M4, 0.85)
        if s is None or g is None:
            print('  %6.2f %6.2f   RECHAZADO' % (W, L)); continue
        sen = g - s
        print('  %6.2f %6.2f %12.4f %12.2f %10.1f'
              % (W, L, s, sen, abs(sen / s) if abs(s) > 1e-4 else float('inf')))
    print()
