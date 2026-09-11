"""La ley del nucleo de potenciacion, y la forma de la frontera del compromiso."""
import numpy as np

A = np.load('/tmp/stdp/nucleo_pot.npz')['filas']     # W, L, tr, suelo, senal
GEOM = sorted(set(map(tuple, A[:, :2])))
FAM = {
    'E1 exp      (2)': lambda v: [v, np.ones_like(v)],
    'E2 exp+cuad (3)': lambda v: [v**2, v, np.ones_like(v)],
    'M1 mixta    (3)': lambda v: [v, np.log(v), np.ones_like(v)],
    'E3 exp+cub  (4)': lambda v: [v**3, v**2, v, np.ones_like(v)],
}

def curva(g):
    m = (A[:,0]==g[0]) & (A[:,1]==g[1])
    v, s = A[m,2], np.abs(A[m,4])
    u = s > 1e-6
    return v[u], s[u]

print('  --- competencia y LOO por geometria entera ---')
print('  %-18s %10s %10s %12s' % ('familia', 'int[%]', 'LOO[%]', 'peor geom[%]'))
for nom, f in FAM.items():
    C = {}
    for g in GEOM:
        v, s = curva(g)
        C[g],*_ = np.linalg.lstsq(np.vstack(f(v)).T, np.log(s), rcond=None)
    n = len(C[GEOM[0]])
    ei = []
    for g in GEOM:
        v, s = curva(g); M = np.vstack(f(v)).T
        ei.append(np.sqrt(np.mean((np.abs(np.exp(M@C[g])-s)/s)**2)))
    el = []
    for fuera in GEOM:
        dentro = [g for g in GEOM if g != fuera]
        X = np.array([[np.log(g[0]), np.log(g[1]), np.log(g[0])*np.log(g[1]), 1.0]
                      for g in dentro])
        xf = [np.log(fuera[0]), np.log(fuera[1]), np.log(fuera[0])*np.log(fuera[1]), 1.0]
        pc = [np.linalg.lstsq(X, np.array([C[g][k] for g in dentro]), rcond=None)[0] @ xf
              for k in range(n)]
        v, s = curva(fuera); M = np.vstack(f(v)).T
        el.append(np.sqrt(np.mean((np.abs(np.exp(M@np.array(pc))-s)/s)**2)))
    print('  %-18s %10.2f %10.2f %12.2f'
          % (nom, 100*np.mean(ei), 100*np.mean(el), 100*max(el)))

print('\n  --- la FRONTERA: suavidad contra senal ---')
print('  %10s %12s %12s %12s' % ('W/L', 'e-pleg[mV]', 'senal@1.0', 'suelo[mV]'))
pts = []
for g in GEOM:
    v, s = curva(g)
    k = np.polyfit(v, np.log(s), 1)[0]
    ef = 1000.0/abs(k)
    m = (A[:,0]==g[0]) & (A[:,1]==g[1])
    sen = np.abs(A[m][np.argmin(np.abs(A[m][:,2]-1.0))][4])*1e3
    su = A[m][0,3]*1e3
    pts.append((ef, sen, g, su))
# frontera de Pareto: mas suave (ef alto) Y mas senal
pts.sort(key=lambda p: -p[0])
mejor = -1
for ef, sen, g, su in pts:
    if sen > mejor:
        mejor = sen
        print('  %10s %12.1f %12.2f %12.4f   <- PARETO'
              % ('%.2f/%.2f'%g, ef, sen, su))
print()
ef = np.array([p[0] for p in pts]); sn = np.array([p[1] for p in pts])
k, b = np.polyfit(np.log(ef), np.log(sn), 1)
r = np.corrcoef(np.log(ef), np.log(sn))[0,1]
print('  senal ~ e-plegado^%.3f   (r = %.4f en log-log)' % (k, r))
print('  -> %s' % ('RECTA en log-log: no hay punto natural, la elige el sistema'
                   if abs(r) > 0.97 else 'hay curvatura: existe un codo'))
