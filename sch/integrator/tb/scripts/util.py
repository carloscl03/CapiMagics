"""Estamos caracterizando donde el motor va a operar, o pagando territorio inutil?

Misma pregunta que en el encoder, donde fijar `Ld` y `W9` costo el 0 % de la
region util. Aqui hay dos cosas que mirar:

  1. que (W6, L6, C) eligen los diseños con buena resolucion
  2. que rango de vm se visita de verdad en la banda 74-4500 kHz

Y luego: si reajustamos SOLO en esa region, baja el error? Si baja mucho,
estabamos gastando coeficientes en describir zonas que el motor no toca.
"""
import itertools
import numpy as np

# --- 1. que region usa el motor -------------------------------------------
R = [r for r in np.load('barrido_final.npy', allow_pickle=True)
     if not r.get('sat') and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]
G = sorted({tuple(r['g']) for r in R})
fil = []
for g in G:
    s = sorted([r for r in R if tuple(r['g']) == g], key=lambda r: r['f'])
    if len(s) < 4: continue
    f = np.array([r['f'] for r in s], float); v = np.array([r['vm'] for r in s])
    rz = np.array([r['riz'] for r in s])
    sens = 1000*np.polyfit(np.log10(f), v, 1)[0]
    fil.append((sens/rz.max(), g, v.min(), v.max()))
fil.sort(key=lambda x: -x[0])
n = max(1, len(fil)//3)
buenos = fil[:n]
print('=== la region que el motor SI usa (tercio superior en resolucion) ===')
print('   %d de %d geometrias' % (n, len(fil)))
for k, nm in ((5, 'W6'), (6, 'L6'), (7, 'C')):
    vals = [g[k] for _, g, _, _ in buenos]
    todos = [g[k] for _, g, _, _ in fil]
    print('   %-3s buenos: %s' % (nm, sorted(set(vals))))
    print('       todos : %s' % sorted(set(todos)))
vm0 = min(v0 for _, _, v0, _ in buenos); vm1 = max(v1 for _, _, _, v1 in buenos)
print('   vm visitado por los buenos: %.3f a %.3f V' % (vm0, vm1))
vm0t = min(v0 for _, _, v0, _ in fil); vm1t = max(v1 for _, _, _, v1 in fil)
print('   vm visitado por todos     : %.3f a %.3f V' % (vm0t, vm1t))

# --- 2. donde se ajusto la ley de inyeccion --------------------------------
J = np.load('iny3.npz'); C = J['casos']; V0 = J['V0']
print()
print('=== donde se ajusto la ley de inyeccion (iny3.npz) ===')
for k, nm in ((0,'W6'), (1,'L6'), (2,'C')):
    print('   %-3s de %.3f a %.3f' % (nm, C[:,k].min(), C[:,k].max()))
print('   vm  de %.2f a %.2f' % (V0.min(), V0.max()))

# --- 3. reajustar solo en la region util -----------------------------------
T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
okt = np.isfinite(TE); Zt = np.log10(TG[okt])
Bt = np.column_stack([np.ones(okt.sum())] + [Zt[:,k]**p for k in (0,1) for p in (1,2,3)])
ct = np.linalg.lstsq(Bt, TE[okt], rcond=None)[0]
def techo_ley(W6, L6):
    z=[np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]]+[[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ ct)

DV = J['dV']
def arma(w6max, l6max, cmin, cmax, vmin, vmax):
    X, Y, GI = [], [], []
    for i in range(len(C)):
        W6, L6, Cf = C[i]
        if not (0.25 <= W6 <= w6max and 0.28 <= L6 <= l6max and cmin <= Cf <= cmax):
            continue
        tc = techo_ley(W6, L6)
        for k, v in enumerate(V0):
            d = DV[i, k]
            if np.isfinite(d) and d > 0.003 and v < tc-0.05 and vmin <= v <= vmax:
                X.append([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-v)])
                Y.append(np.log10(d)); GI.append(i)
    return np.array(X), np.array(Y), np.array(GI)

def loo(X, Y, GI, grado=3):
    E = [e for e in itertools.product(range(grado+1), repeat=4) if sum(e) <= grado]
    B = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
    er = []
    for g in sorted(set(GI)):
        m = GI == g
        if B.shape[1] >= (~m).sum(): return None
        c = np.linalg.lstsq(B[~m], Y[~m], rcond=None)[0]
        er.append(100*np.abs(10**(B[m]@c - Y[m]) - 1))
    e = np.concatenate(er)
    return B.shape[1], e.mean(), np.array([x.mean() for x in er]).max(), len(Y), len(set(GI))

print()
print('=== reajustar solo donde el motor opera ===')
print('  %-34s %5s %5s %4s %10s %11s' % ('region', 'ptos', 'geom', 'coef', 'LOO medio', 'peor geom'))
for nm, args in (('todo lo medido', (2.0, 2.0, 0, 1e9, 0, 9)),
                 ('vm util (1.4-2.45)', (2.0, 2.0, 0, 1e9, 1.4, 2.45)),
                 ('W6<=1 (los buenos)', (1.0, 2.0, 0, 1e9, 1.4, 2.45)),
                 ('W6<=1 y C 2000-12000', (1.0, 2.0, 1800, 13000, 1.4, 2.45))):
    X, Y, GI = arma(*args)
    r = loo(X, Y, GI)
    if r is None or r[4] < 20:
        print('  %-34s %5d %5d   pocos datos' % (nm, len(Y), len(set(GI)))); continue
    print('  %-34s %5d %5d %4d %9.2f%% %10.1f%%' % (nm, r[3], r[4], r[0], r[1], r[2]))
