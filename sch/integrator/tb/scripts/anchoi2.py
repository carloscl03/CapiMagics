"""Ancho del spike frente a la frecuencia. v2, con el aviso de Euler:

LA FRECUENCIA NO SE MIDE DESDE EL PRINCIPIO. La neurona tarda en arrancar: la
membrana tiene que cargarse hasta el umbral la primera vez, y ese tiempo NO es
un periodo. Medir desde t=0 mezcla el arranque con el regimen.

v1 fallaba por eso: ventana de 8 us + 6 periodos ESTIMADOS con una ley que
resulto estar 3.4x desviada, asi que a corriente baja no habia spikes todavia y
a corriente alta medi con DOS spikes -- un solo intervalo, que no es frecuencia.

Aqui: se simula largo, se tiran los primeros spikes, y se exige un minimo de
intervalos para dar el dato.
"""
import numpy as np, subprocess, sys

SUB = open('neurona_i.txt').read()

def mide(iex_nA, tfin, nmin=6, tirar=3):
    L = [SUB, 'Vdd Vdd 0 3.3', 'Vss Vss 0 0', 'Vin Vin 0 3.3',
         'X1 Vdd Vss Vin spike spike_neg nint neurona',
         'Iex Vdd nint %gn' % iex_nA,
         '.control', 'tran 1n %g' % tfin,
         'wrdata ai2.dat v(spike)', '.endc', '.end']
    open('ai2.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','ai2.spice'], capture_output=True)
    try:
        A = np.loadtxt('ai2.dat')
    except Exception:
        return None
    t, v = A[:,0], A[:,1]
    hi, lo = v.max(), v.min()
    if hi-lo < 1.0: return None
    mid=(hi+lo)/2; s=(v>mid).astype(int); d=np.diff(s)
    su=np.where(d>0)[0]; ba=np.where(d<0)[0]
    if len(su) < tirar + nmin: return ('pocos', len(su), t[-1])
    su = su[tirar:]                      # fuera el arranque
    per = np.diff(t[su])
    an = np.array([t[ba[ba>i][0]]-t[i] for i in su if len(ba[ba>i])])
    # deriva: comparar la primera mitad de intervalos con la segunda
    h = len(per)//2
    der = 100*(np.median(per[h:])/np.median(per[:h]) - 1) if h >= 2 else np.nan
    return dict(f=1e-3/np.median(per), anch=np.median(an)*1e9, sd=np.std(an)*1e9,
                n=len(su), deriva=der, t1=t[su[0]]*1e6)

print('=== ancho frente a frecuencia, tirando el arranque ===')
print('  deriva = cuanto cambia el periodo entre la 1a y la 2a mitad (0 = asentado)')
print()
print('  %8s %9s %10s %8s %8s %8s %9s' %
      ('Iex[nA]','f[kHz]','ANCHO[ns]','sigma','ciclo%','deriva','1er spike'))
sys.stdout.flush()
for iex, tfin in ((5,400e-6),(15,200e-6),(40,120e-6),(100,60e-6),
                  (250,40e-6),(600,30e-6),(1200,25e-6)):
    r = mide(iex, tfin)
    if r is None:
        print('  %8d   no dispara en %.0f us' % (iex, tfin*1e6))
    elif isinstance(r, tuple):
        print('  %8d   solo %d spikes en %.0f us (insuficiente)' % (iex, r[1], r[2]*1e6))
    else:
        print('  %8d %8.0f %9.1f %7.1f %7.1f %7.1f%% %8.1fus'
              % (iex, r['f'], r['anch'], r['sd'], 100*r['anch']*1e-9*r['f']*1e3,
                 r['deriva'], r['t1']))
    sys.stdout.flush()
