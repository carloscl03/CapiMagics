"""Ley de inyeccion nueva, sobre el barrido denso de la region util.

Competencia de familias + LOO por geometria. Y despues LO QUE DE VERDAD
IMPORTA: evaluarla en el punto de trabajo del motor, porque la ley vieja tenia
4.03 % de LOO y fallaba un 35 % ahi. El error externo, aunque sea por
geometria, NO ve que la caja este mal centrada.
"""
import itertools, sys
import numpy as np

D = np.load('iny_util.npz'); G = D['geos']; V0 = D['v0']; DV = D['dv']
T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE); Zt = np.log10(TG[ok])
Bt = np.column_stack([np.ones(ok.sum())] + [Zt[:, k]**p for k in (0,1) for p in (1,2,3)])
ct = np.linalg.lstsq(Bt, TE[ok], rcond=None)[0]
def techo(W6, L6):
    z = [np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]] + [[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ ct)

X, Y, GI = [], [], []
for i, (W6, L6, Cf) in enumerate(G):
    tc = techo(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 1e-5 and v < tc - 0.05:
            X.append([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-v)])
            Y.append(np.log10(d)); GI.append(i)
X = np.array(X); Y = np.array(Y); GI = np.array(GI)
gs = np.array(sorted(set(GI)))
print('=== %d puntos, %d geometrias ===' % (len(Y), len(gs)))
print('   (L6=2.8 esta fuera de la caja del techo, que llega a 2.0: extrapola)')
print()

def loo(cols, grado, nf=20):
    Z = X[:, cols]
    E = [e for e in itertools.product(range(grado+1), repeat=len(cols)) if sum(e) <= grado]
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    rng = np.random.default_rng(3); er, pg = [], []
    for f in np.array_split(rng.permutation(gs), nf):
        m = np.isin(GI, f)
        if B.shape[1] >= (~m).sum(): return None
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
        for g in f:
            q = GI == g
            if q.sum(): pg.append((100*np.abs(10**(B[q]@c - Y[q]) - 1)).mean())
    return B.shape[1], np.concatenate(er).mean(), max(pg), E, B

print('  %-40s %5s %9s %11s' % ('forma', 'coef', 'LOO', 'peor geom'))
mejor = None
for nm, cols, gr in (('COLAPSADA g2 (W6,L6,C,s)', [0,1,2,3], 2),
                     ('COLAPSADA g3', [0,1,2,3], 3),
                     ('COLAPSADA g4', [0,1,2,3], 4),
                     ('sin C: (W6,L6,s) g3', [0,1,3], 3),
                     ('sin W6: (L6,C,s) g3', [1,2,3], 3)):
    r = loo(cols, gr)
    if r is None: continue
    print('  %-40s %5d %8.2f%% %10.1f%%' % (nm, r[0], r[1], r[2]))
    if cols == [0,1,2,3] and (mejor is None or r[1] < mejor[1]):
        mejor = (r[3], r[1], r[4], gr)
E, err, B, gr = mejor
c = np.linalg.lstsq(B, Y, rcond=None)[0]
np.save('ci_util.npy', c); np.save('ci_util_exp.npy', np.array(E))
print()
print('  elegida: colapsada grado %d, %d coeficientes, %.2f%% LOO' % (gr, len(c), err))

# --- LO QUE IMPORTA: en el punto de trabajo -------------------------------
R = [r for r in np.load('validacion.npy', allow_pickle=True) if r['valido']]
sys.path.insert(0, '/tmp/integ/pkg')
import integrator_design as I
def dv_nueva(vm, W6, L6, Cf):
    tc = techo(W6, L6)
    if tc - vm <= 0: return 0.0
    z = np.array([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-vm)])
    return 10**sum(k*np.prod(z**np.array(e)) for k, e in zip(c, E))
print()
print('=== las dos leyes en el punto de trabajo del motor (84 puntos) ===')
vieja, nueva = [], []
for r in R:
    vm = r['vm_spice']
    a = 1000*I.inyeccion(vm, r['W6'], r['L6'], r['C'])
    b = 1000*dv_nueva(vm, r['W6'], r['L6'], r['C'])
    # lo que la fisica exige ahi: dV = I_fuga/(f*C)
    exig = r['ifuga']*1e-9/(r['f']*1e3 * r['C']*1e-15) * 1000
    vieja.append(100*(a/exig - 1)); nueva.append(100*(b/exig - 1))
vieja = np.array(vieja); nueva = np.array(nueva)
print('  ley VIEJA:  %+.1f %% de media, |%.1f|, peor %.1f' %
      (vieja.mean(), np.abs(vieja).mean(), np.abs(vieja).max()))
print('  ley NUEVA:  %+.1f %% de media, |%.1f|, peor %.1f' %
      (nueva.mean(), np.abs(nueva).mean(), np.abs(nueva).max()))
print()
print('  (dV exigido = I_fuga/(f*C), con I_fuga MEDIDO por amperimetro:')
print('   es la condicion de equilibrio, no una prediccion)')
print('  un +35%% en dV se traduce en -43 mV de sesgo en vm (pendiente 6.9/V)')
