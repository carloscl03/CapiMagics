"""Pasadas encadenadas hasta converger, y la SATURACION como categoria propia.

Lo aprendido: no es que hiciera falta un asentamiento largo, es que converge
POR ITERACION -- cada pasada arranca del vm de la anterior y se acerca. Encadenar
pasadas cortas es mas barato que una larga.

Y hay puntos donde no hay equilibrio ninguno: vm pegado al techo (~2.45 V), donde
dV->0 y la inyeccion ya no sostiene a la fuga. El integrador esta SATURADO. Eso
no es un dato malo: dice donde esa geometria deja de leer, que es justo lo que
IntegradorSpec tiene que reportar. Se marca, no se tira.

(Descartado por medida: el paso de integracion. De 2 ns a 0.2 ns el balance no
se mueve -- 2.65 -> 2.96 %, 0.46 -> 0.46 %. No era resolucion temporal.)
"""
import sys, time
import numpy as np
import banco

R = list(np.load('barrido_banda2.npy', allow_pickle=True))
TECHO = 2.40          # V. Por encima se considera pegado al techo.

for r in R:
    r['sat'] = False

print('=== pasadas encadenadas hasta converger ===')
sys.stdout.flush()
t00 = time.time()
for it in range(4):
    pend = [i for i, r in enumerate(R)
            if r['f'] >= 300 and not r['sat']
            and (not np.isfinite(r['vm']) or abs(r['bal']) > 1.5)]
    if not pend:
        print('   todo convergido en %d pasadas' % it); break
    # los pegados al techo no van a converger: son saturacion
    sat = [i for i in pend if R[i]['vm'] > TECHO]
    for i in sat:
        R[i]['sat'] = True
    pend = [i for i in pend if i not in sat]
    print('   pasada %d: %3d pendientes  (%d marcados SATURADOS)'
          % (it + 1, len(pend), len(sat)))
    sys.stdout.flush()
    if not pend:
        break
    for f in sorted(set(R[i]['f'] for i in pend)):
        idx = [i for i in pend if R[i]['f'] == f]
        out = []
        for k in range(0, len(idx), 20):
            sub = idx[k:k+20]
            out += banco.mide([(R[i]['g'], f) for i in sub], nset=12, nmed=8,
                              tag='p3_%d_%d_%d' % (it, f, k),
                              vic=[R[i]['vm'] for i in sub])
        for i, o in zip(idx, out):
            R[i] = dict(g=R[i]['g'], f=f, sat=False, **o)
    np.save('barrido_banda3.npy', np.array(R, dtype=object))

np.save('barrido_banda3.npy', np.array(R, dtype=object))
print()
print('=== estado final, %.0f min ===' % ((time.time() - t00) / 60))
print('  %7s %8s %10s %10s' % ('f[kHz]', 'buenos', 'saturados', 'sin cerrar'))
for f in sorted(set(r['f'] for r in R)):
    s = [r for r in R if r['f'] == f]
    ok = sum(1 for r in s if not r['sat'] and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5)
    st = sum(1 for r in s if r['sat'])
    print('  %7d %8d %10d %10d' % (f, ok, st, len(s) - ok - st))
