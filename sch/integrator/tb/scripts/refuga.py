"""Reajustar la fuga con los dos conjuntos: el barrido viejo y las 344 medidas
directas del amperimetro.

El viejo (`fuga_bar.npz`) es una malla de geometria x vm, pero solo se uso donde
I > 0.7*Iref. El nuevo mide I_fuga en el punto de equilibrio de cada (geometria,
f), o sea a lo largo de una curva, no de una malla -- pero con amperimetro y en
la banda que la cadena produce de verdad.

Se compite: solo viejo, solo nuevo, y los dos juntos. Validacion externa POR
GEOMETRIA en los dos casos.
"""
import itertools
import numpy as np

def base(Z, g, nv):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g+1), repeat=nv):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)

# --- viejo -----------------------------------------------------------------
D = np.load('fuga_bar.npz'); v = D['v']; I = D['I']; cas = D['casos']
XV, YV, GV = [], [], []
for a in range(len(cas)):
    y = np.abs(I[:, a]) / cas[a, 4]
    m = (y > 0.7) & (v <= 2.30)
    for k in np.where(m)[0]:
        XV.append([np.log10(cas[a,0]), np.log10(cas[a,1]), np.log10(cas[a,2]),
                   np.log10(cas[a,3]), v[k]])
        YV.append(np.log10(y[k])); GV.append(tuple(cas[a,:4]))
XV = np.array(XV); YV = np.array(YV)

# --- nuevo -----------------------------------------------------------------
R = [r for r in np.load('barrido_final.npy', allow_pickle=True)
     if not r.get('sat') and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]
XN, YN, GN = [], [], []
for r in R:
    W1,L1,W2,L2,Ir,W6,L6,Cf = r['g']
    XN.append([np.log10(W1), np.log10(L1), np.log10(W2), np.log10(L2), r['vm']])
    YN.append(np.log10(r['ifuga']*1e-9/Ir)); GN.append((W1,L1,W2,L2))
XN = np.array(XN); YN = np.array(YN)

print('=== datos ===')
print('  viejo (malla, I>0.7Iref): %4d puntos, %2d geometrias de fuga'
      % (len(YV), len({g for g in GV})))
print('  nuevo (amperimetro):      %4d puntos, %2d geometrias de fuga'
      % (len(YN), len({g for g in GN})))
print('  el nuevo mide vm de %.3f a %.3f V; el viejo de %.3f a %.3f'
      % (XN[:,4].min(), XN[:,4].max(), XV[:,4].min(), XV[:,4].max()))
print()

def prueba(X, y, G, gr=3):
    gg = sorted({g for g in G}); rng = np.random.default_rng(5)
    gl = list(gg); rng.shuffle(gl); nc = max(1, int(0.7*len(gl)))
    trg = set(gl[:nc])
    tr = np.array([g in trg for g in G]); te = ~tr
    if te.sum() < 5:
        return None
    B = base(X, gr, 5)
    c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
    e = 100*np.abs(10**(B[te] @ c - y[te]) - 1)
    return e.mean(), B.shape[1], np.linalg.lstsq(B, y, rcond=None)[0]

print('=== competencia: con que datos se ajusta mejor? ===')
print('  %-28s %6s %10s' % ('conjunto', 'coef', 'EXTERNO'))
for nm, X, y, G in (('solo el viejo', XV, YV, GV),
                    ('solo el nuevo', XN, YN, GN),
                    ('los dos juntos', np.vstack([XV, XN]), np.concatenate([YV, YN]), GV+GN)):
    r = prueba(X, y, G)
    if r: print('  %-28s %6d %8.2f%%' % (nm, r[1], r[0]))
print()

# --- la ley combinada, evaluada contra las 344 medidas del amperimetro -----
Xa = np.vstack([XV, XN]); ya = np.concatenate([YV, YN])
cA = np.linalg.lstsq(base(Xa, 3, 5), ya, rcond=None)[0]
cV = np.linalg.lstsq(base(XV, 3, 5), YV, rcond=None)[0]
BN = base(XN, 3, 5)
for nm, c in (('ley actual (solo viejo)', cV), ('ley reajustada (los dos)', cA)):
    e = 100*np.abs(10**(BN @ c - YN) - 1)
    print('  %-26s contra el amperimetro: mediana %.2f%%  p90 %.2f%%'
          % (nm, np.median(e), np.percentile(e, 90)))
np.save('cf_nuevo.npy', cA)
print()
print('  guardada en cf_nuevo.npy (%d coeficientes)' % len(cA))
