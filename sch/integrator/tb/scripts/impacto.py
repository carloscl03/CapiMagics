"""Cuanto cambian vm y el rizado al usar el ancho real en vez de 32 ns fijos?

No se rehace el barrido entero antes de saber si hace falta. Se remide un
subconjunto con el banco ya corregido y se compara contra lo guardado.

Se arranca del vm ya convergido (vic), asi que 12 periodos bastan.
"""
import sys, time
import numpy as np
import banco

R = list(np.load('barrido_final.npy', allow_pickle=True))
rng = np.random.default_rng(4)

print('=== impacto de ancho(f) frente a 32 ns fijos ===')
print('  la correccion del ancho es +3.1%% a 300 kHz y +20.5%% a 4500')
print()
print('  %7s %5s %11s %11s %11s %11s' %
      ('f[kHz]', 'n', 'd(vm) medio', 'd(vm) p90', 'd(riz) medio', 'd(riz) p90'))
sys.stdout.flush()
for f in (300, 1200, 2400, 4500):
    idx = [i for i, r in enumerate(R)
           if r['f'] == f and not r.get('sat') and abs(r['bal']) <= 1.5]
    if len(idx) > 18:
        idx = [idx[k] for k in rng.choice(len(idx), 18, replace=False)]
    out = banco.mide([(R[i]['g'], f) for i in idx], nset=12, nmed=8,
                     tag='imp%d' % f, vic=[R[i]['vm'] for i in idx])
    dv = np.array([1000*(o['vm'] - R[i]['vm']) for i, o in zip(idx, out)])
    dr = np.array([100*(o['riz']/R[i]['riz'] - 1) for i, o in zip(idx, out)
                   if R[i]['riz'] > 0])
    print('  %7d %5d %9.1fmV %9.1fmV %9.1f%% %9.1f%%'
          % (f, len(idx), np.mean(dv), np.percentile(np.abs(dv), 90),
             np.mean(dr), np.percentile(np.abs(dr), 90)))
    sys.stdout.flush()
