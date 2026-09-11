"""Por que el LIF admite leyes de potencia y el encoder / integrador no?

Hipotesis medible: no es que un circuito sea mas simple, sino si su respuesta
SE SEPARA en (factor de geometria) x (funcion universal del estimulo).

Si la matriz log-respuesta[geometria, estimulo] es de RANGO 1, separa perfecto y
basta una ley de potencia por geometria mas una curva. Cuanto mas rango haga
falta, mas terminos cruzados hay que ajustar.

Se mide con SVD: la fraccion de varianza que explica el primer valor singular.
"""
import numpy as np


def separabilidad(M, nom):
    """M[geometria, estimulo] en log. Devuelve varianza explicada por rango 1,2,3."""
    M = M - M.mean()
    s = np.linalg.svd(M, compute_uv=False)
    var = s ** 2 / (s ** 2).sum()
    ac = np.cumsum(var)
    print('  %-34s rango1 %5.1f%%   rango2 %5.1f%%   rango3 %5.1f%%'
          % (nom, 100 * ac[0], 100 * ac[1], 100 * ac[2]))
    return ac


print('=== cuanta varianza explica una separacion de rango 1? ===')
print()

# --- ENCODER: Iex(geometria, Vdif) -----------------------------------------
C = np.load('caja.npz')
jb = int(np.argmin(np.abs(C['vbias'] - 1.2)))
ie = np.abs(C['iex'][:, jb, :])
vd = C['vd']
m = (vd >= -0.3) & (vd <= 0.3)
ok = (ie[:, m] > 1e-12).all(1)
separabilidad(np.log10(ie[ok][:, m]), 'ENCODER   Iex(geom, Vdif)')

# --- INTEGRADOR: fuga(geometria, vm) ---------------------------------------
D = np.load('fuga_bar.npz')
v = D['v']; I = D['I']; cas = D['casos']
mm = (v >= 1.5) & (v <= 2.3)
Y = []
for a in range(len(cas)):
    y = np.abs(I[:, a])[mm] / cas[a, 4]
    if (y > 0.5).all():
        Y.append(np.log10(y))
separabilidad(np.array(Y), 'INTEGRADOR fuga(geom, vm)')

# --- INTEGRADOR: inyeccion(geometria, vm) ----------------------------------
E = np.load('iny3.npz')
d = E['dV']
ok = (d[:, :6] > 0.005).all(1)
separabilidad(np.log10(d[ok][:, :6]), 'INTEGRADOR inyeccion(geom, vm)')

# --- LIF: f(geometria, Iex) ------------------------------------------------
# se reconstruye con SU PROPIA ley publicada, que es lo que hay que juzgar
W = np.repeat(np.linspace(0.3, 3.4, 12), 8)
L = np.tile(np.linspace(21, 49, 8), 12)
IEX = np.array([10, 20, 40, 80, 150, 300, 600, 900])
k = 111.6 * W ** -1.076 * L ** -0.940          # forma de su ley de ganancia
F = np.outer(k, IEX)
separabilidad(np.log10(F), 'LIF        f(geom, Iex)  [su ley]')

print()
print('  rango 1 = separa perfecto -> ley de potencia por geometria + una curva')
print('  rango >1 = hay terminos cruzados geometria-estimulo -> polinomio')
