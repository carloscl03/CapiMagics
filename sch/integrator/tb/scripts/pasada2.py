"""Segunda pasada del barrido: corrige los puntos que no habian asentado.

QUE ESTABA MAL. El asentamiento se especificaba en PERIODOS, y la constante de
tiempo del integrador es C/g, que no depende de la frecuencia. Con 6 periodos,
a 74 kHz son 81 us (de sobra) y a 4500 kHz 1.3 us (nada). Por eso la validez
caia monotonamente con la frecuencia: no era el circuito, era que a cada
frecuencia le daba menos tiempo real.

Consecuencia medida: a 4500 kHz el RIZADO salia 1.93 mV cuando el valor
asentado es 1.02 -- un 90 % de mas. Y el rizado es el denominador de la
resolucion, o sea la metrica con la que se decide el diseño entero.

QUE SE HACE. Arrancar del `vm` de la primera pasada (que si habia convergido;
lo que no convergia era el rizado) y asentar 12 periodos mas. Validado contra
una referencia de 200 periodos: rizado dentro de 0.3 mV, vm dentro de 0.4 mV.

El criterio de aceptacion pasa a ser el BALANCE DE CARGA, no la deriva: a
frecuencia alta 0.9 mV de deriva ya son un 10 % de desbalance, o sea que el
balance es el sensible y la deriva no discrimina.
"""
import sys, time
import numpy as np
import banco

R = list(np.load('barrido_banda.npy', allow_pickle=True))
FS = sorted(set(r['f'] for r in R))
print('=== 2a pasada: %d puntos, se recorrigen los de f >= 300 kHz ===' % len(R))
sys.stdout.flush()

t00 = time.time()
for f in FS:
    if f < 300:
        print('   %5d kHz  se conserva (6 periodos ya son %.0f us)' % (f, 6e6/f))
        sys.stdout.flush()
        continue
    t0 = time.time()
    idx = [i for i, r in enumerate(R) if r['f'] == f]
    lote = [(R[i]['g'], f) for i in idx]
    vic = [R[i]['vm'] for i in idx]
    out = []
    for k in range(0, len(lote), 20):
        out += banco.mide(lote[k:k+20], nset=12, nmed=8,
                          tag='p2_%d_%d' % (f, k), vic=vic[k:k+20])
    # los que aun no cierran, con 4x
    mal = [j for j, r in enumerate(out) if not np.isfinite(r['vm']) or abs(r['bal']) > 1.5]
    if mal:
        re = []
        for k in range(0, len(mal), 20):
            sub = [(R[idx[j]]['g'], f) for j in mal[k:k+20]]
            re += banco.mide(sub, nset=48, nmed=8, tag='p2r_%d_%d' % (f, k),
                             vic=[out[j]['vm'] for j in mal[k:k+20]])
        for j, r in zip(mal, re):
            out[j] = r
    ok = sum(1 for r in out if np.isfinite(r['vm']) and abs(r['bal']) <= 1.5)
    cam = np.mean([abs(o['riz'] - R[i]['riz']) for i, o in zip(idx, out)])
    for i, o in zip(idx, out):
        R[i] = dict(g=R[i]['g'], f=f, **o)
    print('   %5d kHz  %3d/%d con balance <=1.5%%  (%d reintentos)  '
          'el rizado cambia %.2f mV de media   %4.0f s'
          % (f, ok, len(idx), len(mal), cam, time.time()-t0))
    sys.stdout.flush()
    np.save('barrido_banda2.npy', np.array(R, dtype=object))

np.save('barrido_banda2.npy', np.array(R, dtype=object))
print()
print('   total %.0f min -> barrido_banda2.npy' % ((time.time()-t00)/60))
