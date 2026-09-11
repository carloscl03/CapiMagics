"""Sirve W6 = 2.0? El barrido de banda solo probo W6 en {0.25, 0.5, 1.0}.

Concluir "el motor usa W6 <= 1" desde un barrido que nunca probo mas era
justamente el error de fondo: no es que W6=2 sea inutil, es que no lo mire.

Se miden geometrias con W6=2.0 sobre la misma banda, MAS controles con W6=0.25
y 0.5 medidos con el MISMO banco corregido, para que la comparacion sea interna
y no contra datos de otra tanda.

Resolucion = sensibilidad [mV/decada] / rizado peor de la banda.
"""
import itertools, sys, time
import numpy as np
import banco

FS = [74, 150, 300, 600, 1200, 2400, 4500]
rng = np.random.default_rng(21)

# 12 con W6=2.0, y 6 controles con W6 pequeno
alto = [(1.0,0.28,1.0,l2,ir,2.0,l6,c) for l2,ir,l6,c in
        itertools.product([0.5,1.0,2.0],[12e-9,25e-9,50e-9],[0.28,1.0,2.0],[5111.0,12000.0])]
rng.shuffle(alto); alto = alto[:12]
ctrl = [(1.0,0.28,1.0,l2,ir,w6,l6,c) for l2,ir,w6,l6,c in
        itertools.product([1.0],[12e-9,25e-9],[0.25,0.5],[1.0,2.0],[12000.0])]
rng.shuffle(ctrl); ctrl = ctrl[:6]
GEOS = alto + ctrl
print('=== %d geometrias (%d con W6=2.0, %d de control) x %d frecuencias ==='
      % (len(GEOS), len(alto), len(ctrl), len(FS)))
sys.stdout.flush()

D = {}
t00 = time.time()
for f in FS:
    t0 = time.time()
    lote = [(g, f) for g in GEOS]
    out = banco.mide(lote, nset=12, nmed=8, tag='w6_%d' % f)
    for _ in range(2):                                   # encadenar hasta asentar
        mal = [i for i, r in enumerate(out) if not np.isfinite(r['vm']) or abs(r['bal']) > 1.5]
        if not mal: break
        re = banco.mide([(GEOS[i], f) for i in mal], nset=16, nmed=8,
                        tag='w6r_%d' % f, vic=[out[i]['vm'] for i in mal])
        for i, r in zip(mal, re): out[i] = r
    ok = sum(1 for r in out if np.isfinite(r['vm']) and abs(r['bal']) <= 1.5)
    for g, r in zip(GEOS, out):
        D.setdefault(g, {})[f] = r
    print('   %5d kHz  %2d/%d validos  %4.0f s' % (f, ok, len(GEOS), time.time()-t0))
    sys.stdout.flush()
    np.save('w6alto.npy', np.array([{'g': g, 'f': f, **r}
                                    for g, dd in D.items() for f, r in dd.items()], dtype=object))

print()
print('=== resolucion: sirve W6 = 2.0? ===')
print('  %5s %6s %6s %8s %10s %9s %9s' % ('W6','L6','Iref','C[fF]','sens','riz peor','RESOL'))
res = []
for g, dd in D.items():
    s = [(f, r) for f, r in sorted(dd.items())
         if np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]
    if len(s) < 4: continue
    f = np.array([x[0] for x in s], float); v = np.array([x[1]['vm'] for x in s])
    rz = np.array([x[1]['riz'] for x in s])
    sens = 1000*np.polyfit(np.log10(f), v, 1)[0]
    res.append((sens/rz.max(), g, sens, rz.max()))
res.sort(key=lambda x: -x[0])
for rr, g, sens, rzm in res:
    print('  %5.2f %6.2f %5.0fn %8.0f %8.0fmV/d %8.1fmV %8.2f'
          % (g[5], g[6], g[4]*1e9, g[7], sens, rzm, rr))
print()
a = [r for r, g, _, _ in res if g[5] >= 2.0]
b = [r for r, g, _, _ in res if g[5] <= 0.5]
if a and b:
    print('  W6=2.0   mediana %.2f  (n=%d)   mejor %.2f' % (np.median(a), len(a), max(a)))
    print('  W6<=0.5  mediana %.2f  (n=%d)   mejor %.2f' % (np.median(b), len(b), max(b)))
print('  total %.0f min' % ((time.time()-t00)/60))
