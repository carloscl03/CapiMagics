"""El spike real de la neurona. Version barata: los 5 casos en UN netlist,
ventana corta (2.5 us bastan para varios periodos) y asentamiento de 20 us.

La v1 pedia 60 us con paso de 0.1 ns POR CASO: 50 min de CPU en el primero.
Mal dimensionado por mi parte, otra vez: la ventana se elige por lo que hay que
resolver (el flanco, ~1 ns) y por cuantos periodos hacen falta (2-3), no a ojo.
"""
import numpy as np, subprocess

SUB = open('neurona_sub.txt').read()
VINS = [1.0700, 1.0985, 1.1200, 1.1400, 1.1600]

L = [SUB, 'Vdd Vdd 0 3.3', 'Vss Vss 0 0']
vec = []
for i, vin in enumerate(VINS):
    L += ['V%d Vin%d 0 %.5f' % (i, i, vin),
          'X%d Vdd Vss Vin%d spike%d spike_neg%d neurona' % (i, i, i, i)]
    vec.append('v(spike%d)' % i)
L += ['.control', 'tran 0.2n 22.5u 20u', 'wrdata sp2.dat ' + ' '.join(vec),
      '.endc', '.end']
open('sp2.spice', 'w').write('\n'.join(L) + '\n')
print('lanzando 5 neuronas en un netlist...', flush=True)
subprocess.run(['ngspice', '-b', 'sp2.spice'], capture_output=True)
A = np.loadtxt('sp2.dat')
t = A[:, 0]

print()
print('=== el spike real, frente a los 32 ns que yo asumi ===')
print('  %8s %9s %11s %9s %9s %9s %8s' %
      ('Vin[V]', 'f[kHz]', 'ANCHO[ns]', 'V alto', 'V bajo', 'flanco', 'ciclo%'))
for i, vin in enumerate(VINS):
    v = A[:, 1 + 2*i]
    hi, lo = v.max(), v.min(); mid = (hi + lo)/2
    s = (v > mid).astype(int); d = np.diff(s)
    sub = np.where(d > 0)[0]; baj = np.where(d < 0)[0]
    if len(sub) < 2 or len(baj) < 1:
        print('  %8.4f   no dispara en la ventana (hi=%.2f lo=%.2f)' % (vin, hi, lo))
        continue
    per = np.median(np.diff(t[sub]))
    anch = [t[baj[baj > k][0]] - t[k] for k in sub if len(baj[baj > k])]
    v20, v80 = lo + 0.2*(hi-lo), lo + 0.8*(hi-lo)
    k = sub[0]; w = slice(max(0, k-100), min(len(t), k+100))
    try:
        fl = abs(np.interp(v80, v[w], t[w]) - np.interp(v20, v[w], t[w]))*1e9
    except Exception:
        fl = float('nan')
    print('  %8.4f %8.1f %10.1f %9.3f %9.3f %8.2fns %7.1f'
          % (vin, 1e-3/per, np.median(anch)*1e9, hi, lo, fl,
             100*np.median(anch)/per))
