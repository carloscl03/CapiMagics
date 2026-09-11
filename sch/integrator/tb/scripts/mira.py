"""Primera mirada a los datos limpios, ANTES de ajustar nada.

Lo primero no es una ley, es comprobar que el Pareto que le dimos al equipo
sobrevive: el "5.9x mejor resolucion a igual area" se calculo con rizados que
a frecuencia alta estaban hasta un 90 % mal.

  sensibilidad = d(vm)/d(log10 f)   [mV/decada]
  resolucion   = sensibilidad / rizado
"""
import numpy as np

R = [r for r in np.load('barrido_final.npy', allow_pickle=True)
     if not r.get('sat') and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]
print('=== %d puntos buenos ===' % len(R))

geos = sorted({tuple(r['g']) for r in R})
print('   %d geometrias con al menos un punto' % len(geos))
print()

filas = []
for g in geos:
    s = sorted([r for r in R if tuple(r['g']) == g], key=lambda r: r['f'])
    if len(s) < 4:
        continue
    f = np.array([r['f'] for r in s], float)
    v = np.array([r['vm'] for r in s])
    rz = np.array([r['riz'] for r in s])
    # sensibilidad por regresion sobre log10 f
    p = np.polyfit(np.log10(f), v, 1)
    sens = 1000 * p[0]
    filas.append(dict(g=g, n=len(s), sens=sens, riz_peor=rz.max(),
                      resol=sens / rz.max(), fmin=f.min(), fmax=f.max(),
                      vmin=v.min(), vmax=v.max()))

filas.sort(key=lambda x: -x['resol'])
print('=== los 8 mejores en resolucion (sensibilidad / rizado peor) ===')
print('  %6s %6s %6s %7s %8s %10s %9s %8s' %
      ('L2', 'Iref', 'W6', 'L6', 'C[fF]', 'sens', 'riz peor', 'RESOL'))
for x in filas[:8]:
    g = x['g']
    print('  %6.2f %5.0fn %6.2f %7.2f %8.0f %8.0fmV/d %7.1fmV %8.2f'
          % (g[3], g[4]*1e9, g[5], g[6], g[7], x['sens'], x['riz_peor'], x['resol']))
print()
print('=== y los 4 peores ===')
for x in filas[-4:]:
    g = x['g']
    print('  %6.2f %5.0fn %6.2f %7.2f %8.0f %8.0fmV/d %7.1fmV %8.2f'
          % (g[3], g[4]*1e9, g[5], g[6], g[7], x['sens'], x['riz_peor'], x['resol']))
print()
ORIG = (1.0, 0.28, 1.0, 0.28, 50e-9, 1.0, 0.28, 5111)
o = [x for x in filas if x['g'] == ORIG]
print('=== el ORIGINAL del equipo esta en el barrido? ===')
if o:
    x = o[0]
    print('   si: sens %.0f mV/dec, rizado peor %.1f mV, RESOL %.2f' %
          (x['sens'], x['riz_peor'], x['resol']))
    print('   el mejor del barrido da RESOL %.2f  ->  mejora %.1fx'
          % (filas[0]['resol'], filas[0]['resol'] / x['resol']))
    print()
    print('   (el knowledge base, con los rizados MALOS, decia 5.9x)')
else:
    print('   no exactamente; comparo con el mas parecido')
