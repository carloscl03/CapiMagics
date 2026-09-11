"""Las leyes gordas del integrador, escritas como POTENCIA x CORRECCION.

Reescritura EXACTA alrededor de un punto de referencia, como se hizo con el
encoder: la constante pasa a ser el valor en ese punto y los coeficientes
lineales pasan a ser los exponentes locales. Los terminos de grado 2 y 3 quedan
aparte, etiquetados como correccion.

No reduce nada. Sirve para LEER.
"""
import itertools
import numpy as np

def centra(X, Y, ref, nvar):
    """Reajusta en la base centrada en `ref`. Exacto: mismo subespacio."""
    E = [e for e in itertools.product(range(4), repeat=nvar) if sum(e) <= 3]
    Z = X - ref
    B = np.column_stack([np.prod(Z**np.array(e), axis=1) for e in E])
    c = np.linalg.lstsq(B, Y, rcond=None)[0]
    res = np.abs(B@c - Y).max()
    icte = E.index(tuple([0]*nvar))
    ipot = [E.index(tuple(1 if i == j else 0 for i in range(nvar))) for j in range(nvar)]
    icor = [k for k, e in enumerate(E) if sum(e) >= 2]
    return c, E, icte, ipot, icor, res

# ---------------- FUGA -----------------------------------------------------
D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
msk = C[:, 1] == 0.28
X, Y = [], []
for j in np.where(msk)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(g)[0]:
        X.append([np.log10(W1), np.log10(W2), np.log10(L2), V[k]])
        Y.append(np.log10(y[k]))
X = np.array(X); Y = np.array(Y)
REF = np.array([0.0, 0.0, 0.0, 1.80])          # W1=1, W2=1, L2=1, vm=1.8
c, E, ic, ip, ico, res = centra(X, Y, REF, 4)
print('=== LA FUGA ===   (residuo de la reescritura: %.1e decadas)' % res)
print()
print('  I_fuga / Iref = %.4f' % 10**c[ic])
print('                x (W1/1.00)^%+.4f  (W2/1.00)^%+.4f  (L2/1.00)^%+.4f'
      % (c[ip[0]], c[ip[1]], c[ip[2]]))
print('                x 10^(%+.4f * (vm - 1.80))' % c[ip[3]])
print('                x 10^correccion            <- 30 terminos de grado 2 y 3')
print()
m = np.array([1.0 if sum(e) <= 1 else 0.0 for e in E])
Bc = np.column_stack([np.prod((X-REF)**np.array(e), axis=1) for e in E])
er = 100*np.abs(10**(Bc@(c*m) - Y) - 1)
print('  la potencia SOLA: %.1f%% de media  (la ley entera: 7.4%% K-fold)' % er.mean())
print('  -> sirve para entender, no para calcular')
print()

# ---------------- INYECCION ------------------------------------------------
T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE); Zt = np.log10(TG[ok])
Bt = np.column_stack([np.ones(ok.sum())] + [Zt[:, k]**p for k in (0,1) for p in (1,2,3)])
ct = np.linalg.lstsq(Bt, TE[ok], rcond=None)[0]
def techo_ley(W6, L6):
    z = [np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]] + [[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ ct)
J = np.load('iny3.npz'); Cj = J['casos']; V0 = J['V0']; DV = J['dV']
Xi, Yi = [], []
for i in range(len(Cj)):
    W6, L6, Cf = Cj[i]
    if not (0.25 <= W6 <= 2.0 and 0.28 <= L6 <= 2.0): continue
    tc = techo_ley(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.003 and v < tc-0.05:
            Xi.append([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-v)])
            Yi.append(np.log10(d))
Xi = np.array(Xi); Yi = np.array(Yi)
REFi = np.array([np.log10(0.25), 0.0, np.log10(5111.0), np.log10(0.5)])
ci, Ei, ici, ipi, icoi, resi = centra(Xi, Yi, REFi, 4)
print('=== LA INYECCION ===   (residuo: %.1e decadas)' % resi)
print()
print('  dV = %.2f mV' % (1000*10**ci[ici]))
print('       x (W6/0.25)^%+.4f  (L6/1.00)^%+.4f  (C/5111)^%+.4f'
      % (ci[ipi[0]], ci[ipi[1]], ci[ipi[2]]))
print('       x ((techo - vm)/0.50)^%+.4f' % ci[ipi[3]])
print('       x 10^correccion            <- 30 terminos de grado 2 y 3')
print()
mi = np.array([1.0 if sum(e) <= 1 else 0.0 for e in Ei])
Bci = np.column_stack([np.prod((Xi-REFi)**np.array(e), axis=1) for e in Ei])
eri = 100*np.abs(10**(Bci@(ci*mi) - Yi) - 1)
print('  la potencia SOLA: %.1f%% de media  (la ley entera: 4.0%% LOO)' % eri.mean())
