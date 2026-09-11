"""La ley de fuga es la culpable del suspenso del lazo?

El amperimetro mide I_fuga directamente. Se compara con lo que predice la ley
EN LA GEOMETRIA QUE EL SOLVER ELIGIO, que es donde importa.
"""
import itertools, json, sys
import numpy as np
import banco

C = np.load('criba2.npz')['casos']
D = np.load('criba2.npz')
sol = json.load(open('pedidos.json'))

# la ley de fuga tal como esta en el paquete
EXP = [e for e in itertools.product(range(4), repeat=4) if sum(e) <= 3]
V = D['v']; I = D['I']
msk = C[:, 1] == 0.28
X, Y = [], []
for j in np.where(msk)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(g)[0]:
        X.append([np.log10(W1), np.log10(W2), np.log10(L2), V[k]]); Y.append(np.log10(y[k]))
CF = np.linalg.lstsq(np.column_stack([np.prod(np.array(X)**np.array(e), axis=1) for e in EXP]),
                     np.array(Y), rcond=None)[0]
def fuga_ley(vm, W1, W2, L2, Iref):
    v = np.array([np.log10(W1), np.log10(W2), np.log10(L2), vm])
    return Iref * 10**sum(c*np.prod(v**np.array(e)) for c, e in zip(CF, EXP))

print('=== la ley de fuga en las geometrias que el solver eligio ===')
print('  %-12s %6s %6s %7s %9s %11s %11s %9s' %
      ('banda', 'L2', 'W2', 'Iref', 'f', 'ley [nA]', 'medida [nA]', 'error'))
sys.stdout.flush()
vistos = set()
er = []
for s in sol:
    key = (s['W1'], s['W2'], s['L2'], s['Iref'], s['W6'], s['L6'], s['C'])
    if key in vistos: continue
    vistos.add(key)
    g = (s['W1'], 0.28, s['W2'], s['L2'], s['Iref']*1e-9, s['W6'], s['L6'], s['C'])
    for f, vp in ((s['f_lo'], s['vm_lo']), (s['f_hi'], s['vm_hi'])):
        vic = [vp]
        for _ in range(3):
            o = banco.mide([(g, f)], nset=12, nmed=8, tag='cu', vic=vic)[0]
            vic = [o['vm']]
            if abs(o['bal']) <= 1.5: break
        pred = 1e9*fuga_ley(o['vm'], s['W1'], s['W2'], s['L2'], s['Iref']*1e-9)
        e = 100*(pred/o['ifuga'] - 1); er.append(e)
        print('  %-12s %6.2f %6.1f %6.0fn %8.0f %10.2f %10.2f %+8.1f%%'
              % ('%d-%d' % (s['f_lo'], s['f_hi']), s['L2'], s['W2'], s['Iref'],
                 f, pred, o['ifuga'], e))
        sys.stdout.flush()
print()
print('  error de la ley de fuga aqui: medio %+.1f%%, peor %+.1f%%'
      % (np.mean(er), max(er, key=abs)))
print('  (en su K-fold por geometria daba 7.37%%)')
