"""ancho(f): el ancho del spike del LIF en funcion de la frecuencia.

Medido en `anchoi2.py` sobre el netlist real, excitando por corriente, tirando
el arranque y exigiendo >=6 intervalos. Resolucion 1 ns (paso del transitorio),
asi que los valores estan cuantizados y no tiene sentido ajustar fino.

Interpolacion lineal en log10(f), sujeta en los extremos. La banda util es
74-4500 kHz, dentro del rango medido (26-4902).
"""
import numpy as np

F_KHZ = np.array([26.0, 76.0, 203.0, 501.0, 1219.0, 2743.0, 4902.0])
ANCHO_NS = np.array([33.0, 32.0, 33.0, 33.0, 34.0, 36.0, 39.0])

def ancho_ns(f_kHz):
    """Ancho del pulso [ns] a esa frecuencia de disparo."""
    return float(np.interp(np.log10(f_kHz), np.log10(F_KHZ), ANCHO_NS))

if __name__ == '__main__':
    print('=== ancho(f) interpolado sobre la banda util ===')
    print('  %9s %11s %11s' % ('f[kHz]', 'ancho[ns]', 'vs 32 ns'))
    for f in (74, 150, 300, 600, 1200, 2400, 4500):
        a = ancho_ns(f)
        print('  %9d %10.1f %10.1f%%' % (f, a, 100*(a/32.0 - 1)))
