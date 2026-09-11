"""Ley ancho(f) del spike del LIF, sobre la banda 74-4500 kHz.

Medido de los .raw del equipo: 42.4 ns a 307 kHz, 33.0 a 501, 18.0 a 801.
El ancho NO es constante y yo use 32 ns fijos en toda la banda.

La neurona se excita por CORRIENTE (como la excita el encoder), no por tension.
Un transitorio por corriente, paso 1 ns, ventana corta: el coste que me arruino
antes fue pedir 0.2 ns y cinco copias a la vez.
"""
import numpy as np, subprocess, sys

SUB = open('neurona_sub.txt').read()

def mide(vin, tfin=14e-6, vent=4e-6):
    # La neurona se excita por Vin: es la puerta del pfet M6, que hace de fuente
    # de corriente. Vin BAJO -> mas corriente -> mas frecuencia.
    # (Primer intento fallido: puse Vin=0, que abre M6 del todo e inunda el nodo
    #  de integracion; salian 4700 kHz con 10 nA "inyectados".)
    L = [SUB, 'Vdd Vdd 0 3.3', 'Vss Vss 0 0',
         'Vin Vin 0 %.5f' % vin,
         'X1 Vdd Vss Vin spike spike_neg neurona',
         '.control', 'tran 1n %g %g' % (tfin, tfin - vent),
         'wrdata af.dat v(spike)', '.endc', '.end']
    open('af.spice', 'w').write('\n'.join(L) + '\n')
    r = subprocess.run(['ngspice', '-b', 'af.spice'], capture_output=True, text=True)
    try:
        A = np.loadtxt('af.dat')
    except Exception:
        return None
    t, v = A[:, 0], A[:, 1]
    hi, lo = np.percentile(v, 99), np.percentile(v, 1)
    if hi - lo < 1.0:
        return None
    mid = (hi + lo) / 2
    s = (v > mid).astype(int); d = np.diff(s)
    su = np.where(d > 0)[0]; ba = np.where(d < 0)[0]
    if len(su) < 2:
        return None
    per = np.median(np.diff(t[su]))
    an = [t[ba[ba > i][0]] - t[i] for i in su if len(ba[ba > i])]
    if not an:
        return None
    return 1e-3/per, np.median(an)*1e9, len(su)

print('=== ancho del spike frente a la frecuencia ===')
print('  %9s %10s %11s %8s' % ('Vin[V]', 'f[kHz]', 'ANCHO[ns]', 'spikes'))
sys.stdout.flush()
for vin in (1.1600, 1.1400, 1.1200, 1.0985, 1.0800, 1.0600, 1.0400, 1.0200, 1.0000):
    r = mide(vin)
    if r is None:
        print('  %9.4f   sin spikes en la ventana' % vin)
    else:
        print('  %9.4f %9.0f %10.1f %8d' % (vin, r[0], r[1], r[2]))
    sys.stdout.flush()
