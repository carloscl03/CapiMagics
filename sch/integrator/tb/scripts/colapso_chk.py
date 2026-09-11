"""Sobrevive el colapso rizado = I_fuga/(f*C) al cambiar el ancho del pulso?

Con 32 ns fijos daba mediana 1.002 y dispersion 1.12x sobre 344 puntos. Yo
argumente que era conservacion de carga y por tanto independiente del estimulo.
Si al ensanchar el pulso un 20 % el rizado sube un 48 %, o I_fuga sube con el,
o mi argumento estaba mal.
"""
import sys
import numpy as np
import banco

R = list(np.load('barrido_final.npy', allow_pickle=True))
rng = np.random.default_rng(4)
print('=== el colapso, con el ancho corregido ===')
print('  q = rizado * C * f / I_fuga   (deberia ser ~1 si la ley aguanta)')
print()
print('  %7s %5s %11s %11s %11s %11s' %
      ('f[kHz]', 'n', 'q ANTES', 'q AHORA', 'I_fuga ant', 'I_fuga ahora'))
sys.stdout.flush()
for f in (300, 1200, 2400, 4500):
    idx = [i for i, r in enumerate(R)
           if r['f'] == f and not r.get('sat') and abs(r['bal']) <= 1.5]
    if len(idx) > 18:
        idx = [idx[k] for k in rng.choice(len(idx), 18, replace=False)]
    out = banco.mide([(R[i]['g'], f) for i in idx], nset=12, nmed=8,
                     tag='col%d' % f, vic=[R[i]['vm'] for i in idx])
    qa, qn, ia, ino = [], [], [], []
    for i, o in zip(idx, out):
        C = R[i]['g'][7] * 1e-15
        qa.append(R[i]['riz']*1e-3 * C * f*1e3 / (R[i]['ifuga']*1e-9))
        qn.append(o['riz']*1e-3 * C * f*1e3 / (o['ifuga']*1e-9))
        ia.append(R[i]['ifuga']); ino.append(o['ifuga'])
    print('  %7d %5d %10.3f %10.3f %9.2fnA %9.2fnA'
          % (f, len(idx), np.median(qa), np.median(qn), np.median(ia), np.median(ino)))
    sys.stdout.flush()
