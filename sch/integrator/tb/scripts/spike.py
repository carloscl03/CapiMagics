"""Como es el spike que la neurona produce de verdad?

Los 32 ns que use en TODOS los bancos del integrador son una suposicion mia.
La medida de hoy dice que dV depende brutalmente del ancho (+93 % en el
ORIGINAL y +507 % en el MEJORADO al pasar de 32 a 215 ns), asi que este dato
decide si la ley de inyeccion vale o hay que rehacerla.

Se mide sobre el netlist real de la neurona (sch/lif/tb/tb_charac.spice),
variando Vin para recorrer la banda de frecuencias.
"""
import numpy as np, subprocess, re

SUB = open('neurona_sub.txt').read()

def corre(vin, tfin=60e-6, vent=6e-6, paso=1e-10):
    L = [SUB,
         'Vdd Vdd 0 3.3', 'Vss Vss 0 0', 'V2 Vin 0 %.5f' % vin,
         'X1 Vdd Vss Vin spike spike_neg neurona',
         '.control',
         'tran %g %g %g' % (paso, tfin, tfin - vent),
         'wrdata sp.dat v(spike)',
         '.endc', '.end']
    open('sp.spice', 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', 'sp.spice'], capture_output=True)
    A = np.loadtxt('sp.dat')
    return A[:, 0], A[:, 1]

def rasgos(t, v):
    hi = v.max(); lo = v.min(); mid = (hi + lo) / 2
    s = (v > mid).astype(int)
    d = np.diff(s)
    sub = np.where(d > 0)[0]; baj = np.where(d < 0)[0]
    if len(sub) < 2 or len(baj) < 1:
        return None
    per = np.median(np.diff(t[sub]))
    anch = []
    for i in sub:
        j = baj[baj > i]
        if len(j):
            anch.append(t[j[0]] - t[i])
    if not anch:
        return None
    # flancos 20-80 %
    v20, v80 = lo + 0.2*(hi-lo), lo + 0.8*(hi-lo)
    i0 = sub[0]
    w = slice(max(0, i0-200), min(len(t), i0+200))
    tt, vv = t[w], v[w]
    try:
        tr = np.interp(v80, vv, tt) - np.interp(v20, vv, tt)
    except Exception:
        tr = np.nan
    return dict(f=1e-3/per, ancho=np.median(anch)*1e9, amp=hi-lo,
                vhi=hi, vlo=lo, subida=abs(tr)*1e9, ciclo=100*np.median(anch)/per)

print('=== el spike real de la neurona, frente a mis 32 ns ===')
print('  %8s %9s %11s %9s %9s %9s %9s' %
      ('Vin[V]', 'f[kHz]', 'ANCHO[ns]', 'amp[V]', 'V alto', 'V bajo', 'ciclo%'))
for vin in (1.0700, 1.0985, 1.1200, 1.1400, 1.1600):
    try:
        t, v = corre(vin)
        r = rasgos(t, v)
    except Exception as e:
        print('  %8.4f  fallo: %s' % (vin, e)); continue
    if r is None:
        print('  %8.4f  no dispara en la ventana' % vin); continue
    print('  %8.4f %8.1f %10.1f %9.3f %9.3f %9.3f %8.1f'
          % (vin, r['f'], r['ancho'], r['amp'], r['vhi'], r['vlo'], r['ciclo']))
