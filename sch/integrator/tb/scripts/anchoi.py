"""Ancho del spike frente a la frecuencia, excitando por CORRIENTE.

Asi es como lo excita el encoder, y ademas Vin apenas mueve la frecuencia
(1.0 a 1.16 V solo va de 1617 a 1976 kHz). Para recorrer 74-4500 kHz hace falta
inyectar corriente en el nodo de integracion, con M6 apagado (Vin = Vdd).

AVISO sobre los .raw del equipo: `tb_charac.raw` es de agosto y da 307 kHz,
pero su propio testbench corrido hoy da 1923 kHz. El .raw esta caducado respecto
del netlist actual. Los anchos leidos de ahi (33 y 18 ns) son de otra version.
"""
import numpy as np, subprocess, sys

SUB = open('neurona_i.txt').read()

def mide(iex_nA, tfin=None, nper=6):
    # ventana estimada con la ley del LIF (16.41 kHz/nA), luego se remide
    fest = max(50.0, 16.41*iex_nA)
    T = 1e-3/fest
    tfin = tfin or (8e-6 + nper*T)
    L = [SUB, 'Vdd Vdd 0 3.3', 'Vss Vss 0 0', 'Vin Vin 0 3.3',
         'X1 Vdd Vss Vin spike spike_neg nint neurona',
         'Iex Vdd nint %gn' % iex_nA,
         '.control', 'tran 1n %g %g' % (tfin, max(0, tfin - nper*T)),
         'wrdata ai.dat v(spike)', '.endc', '.end']
    open('ai.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','ai.spice'], capture_output=True)
    try:
        A = np.loadtxt('ai.dat')
    except Exception:
        return None
    t, v = A[:,0], A[:,1]
    hi, lo = np.percentile(v,99), np.percentile(v,1)
    if hi-lo < 1.0: return None
    mid=(hi+lo)/2; s=(v>mid).astype(int); d=np.diff(s)
    su=np.where(d>0)[0]; ba=np.where(d<0)[0]
    if len(su)<2: return None
    per=np.median(np.diff(t[su]))
    an=[t[ba[ba>i][0]]-t[i] for i in su if len(ba[ba>i])]
    if not an: return None
    return 1e-3/per, np.median(an)*1e9, np.std(an)*1e9, len(su)

print('=== ancho del spike frente a la frecuencia (excitacion por corriente) ===')
print('  %9s %10s %11s %9s %8s %8s' % ('Iex[nA]','f[kHz]','ANCHO[ns]','sigma','ciclo%','spikes'))
sys.stdout.flush()
for iex in (5, 15, 40, 100, 250, 600, 1200):
    r = mide(iex)
    if r is None:
        print('  %9d   sin spikes en la ventana' % iex)
    else:
        f, a, sd, n = r
        print('  %9d %9.0f %10.1f %8.1f %7.1f %8d' % (iex, f, a, sd, 100*a*1e-9*f*1e3, n))
    sys.stdout.flush()
