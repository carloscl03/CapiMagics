"""Repite el chequeo del colapso, pero VALIDANDO que ha asentado.

El intento anterior arranco del vm viejo, que se movio ~7 mV al corregir el
ancho. Sin comprobar el balance no se puede distinguir "la ley se rompe" de
"no ha asentado" -- y ya me paso una vez.

Se encadenan dos pasadas y solo se usan los puntos con |balance| <= 1.5 %.
"""
import sys
import numpy as np
import banco

R = list(np.load('barrido_final.npy', allow_pickle=True))
rng = np.random.default_rng(4)
print('=== colapso con el ancho corregido, exigiendo asentamiento ===')
print('  %7s %6s %10s %10s %10s %10s' %
      ('f[kHz]', 'validos', 'bal med', 'q ANTES', 'q AHORA', 'd(riz)'))
sys.stdout.flush()
for f in (300, 1200, 2400, 4500):
    idx = [i for i, r in enumerate(R)
           if r['f'] == f and not r.get('sat') and abs(r['bal']) <= 1.5]
    if len(idx) > 18:
        idx = [idx[k] for k in rng.choice(len(idx), 18, replace=False)]
    vic = [R[i]['vm'] for i in idx]
    for pasada in range(3):                      # encadenar hasta asentar
        out = banco.mide([(R[i]['g'], f) for i in idx], nset=12, nmed=8,
                         tag='c2_%d_%d' % (f, pasada), vic=vic)
        vic = [o['vm'] for o in out]
    ok = [(i, o) for i, o in zip(idx, out) if abs(o['bal']) <= 1.5]
    if not ok:
        print('  %7d   ninguno asienta' % f); continue
    qa = [R[i]['riz']*1e-3*R[i]['g'][7]*1e-15*f*1e3/(R[i]['ifuga']*1e-9) for i, o in ok]
    qn = [o['riz']*1e-3*R[i]['g'][7]*1e-15*f*1e3/(o['ifuga']*1e-9) for i, o in ok]
    dr = [100*(o['riz']/R[i]['riz']-1) for i, o in ok if R[i]['riz'] > 0]
    print('  %7d %6d %9.2f%% %10.3f %10.3f %9.1f%%'
          % (f, len(ok), np.median([abs(o['bal']) for i, o in ok]),
             np.median(qa), np.median(qn), np.median(dr)))
    sys.stdout.flush()
