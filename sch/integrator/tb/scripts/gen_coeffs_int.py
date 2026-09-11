"""Genera coeffs.py de integrator_design a partir de los barridos."""
import itertools, datetime
import numpy as np

EXP = [e for e in itertools.product(range(4), repeat=4) if sum(e) <= 3]

# --- techo ------------------------------------------------------------------
T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE); Z = np.log10(TG[ok])
Bt = np.column_stack([np.ones(ok.sum())] + [Z[:, k]**p for k in (0, 1) for p in (1, 2, 3)])
CT = np.linalg.lstsq(Bt, TE[ok], rcond=None)[0]
ERR_T = 1000*np.abs(Bt@CT - TE[ok]).mean()
def techo(W6, L6):
    z = [np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]] + [[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ CT)

# --- fuga (L1 fijo en 0.28) -------------------------------------------------
D = np.load('criba2.npz'); V = D['v']; I = D['I']; C = D['casos']
msk = C[:, 1] == 0.28
X, Y = [], []
for j in np.where(msk)[0]:
    W1, L1, W2, L2, Ir = C[j]
    y = I[:, j]/Ir
    g = (V >= 1.0) & (V <= 2.45) & (y > 0.30) & np.isfinite(y)
    for k in np.where(g)[0]:
        X.append([np.log10(W1), np.log10(W2), np.log10(L2), V[k]]); Y.append(np.log10(y[k]))
X = np.array(X); Y = np.array(Y)
CF = np.linalg.lstsq(np.column_stack([np.prod(X**np.array(e), axis=1) for e in EXP]), Y, rcond=None)[0]
CAJA_F = [(C[msk][:, k].min(), C[msk][:, k].max()) for k in (0, 2, 3)]
IREF_R = (C[msk][:, 4].min(), C[msk][:, 4].max())

# --- inyeccion --------------------------------------------------------------
J = np.load('iny3.npz'); Cj = J['casos']; V0 = J['V0']; DV = J['dV']
Xi, Yi = [], []
for i in range(len(Cj)):
    W6, L6, Cf = Cj[i]
    if not (0.25 <= W6 <= 2.0 and 0.28 <= L6 <= 2.0): continue
    tc = techo(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i, k]
        if np.isfinite(d) and d > 0.003 and v < tc - 0.05:
            Xi.append([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-v)])
            Yi.append(np.log10(d))
Xi = np.array(Xi); Yi = np.array(Yi)
CI = np.linalg.lstsq(np.column_stack([np.prod(Xi**np.array(e), axis=1) for e in EXP]), Yi, rcond=None)[0]
CAJA_I = [(10**Xi[:, k].min(), 10**Xi[:, k].max()) for k in (0, 1, 2)]

def fmt(c, n=4):
    L = ['(']
    for i in range(0, len(c), n):
        L.append('    ' + ', '.join('%.8g' % x for x in c[i:i+n]) + ',')
    L.append(')')
    return '\n'.join(L)

S = ['"""Coeficientes de integrator_design. GENERADO por gen_coeffs_int.py.',
     '',
     'NO EDITAR A MANO. Procedencia: sch/integrator/results/ y los barridos',
     'criba2.npz (fuga, 1440 geometrias con Iref cruzado), techo.npz (48',
     'geometrias hasta V0=3.25) e iny3.npz (inyeccion, 200 geometrias).',
     '',
     'Generado el %s.' % datetime.date.today().isoformat(),
     '',
     'Error medido (validacion por GEOMETRIA, no por punto):',
     '    fuga        7.37 %% K-fold, 15.2 %% peor geometria',
     '    inyeccion   4.03 %% LOO,    11.4 %% peor geometria',
     '    techo       %.1f mV' % ERR_T,
     '    rizado      dispersion 1.12x SIN coeficientes',
     '    composicion 23.2 mV de error medio en vm',
     '"""', '',
     '# --- base polinomica: exponentes, cubica completa en 4 variables -------',
     'EXPONENTES = (']
S += ['    ' + ', '.join('(%d, %d, %d, %d)' % e for e in EXP[i:i+5]) + ',' for i in range(0, len(EXP), 5)]
S += [')', '',
      '# --- la FUGA: I_fuga/Iref = 10^(FUGA . base(lgW1, lgW2, lgL2, vm)) ----',
      '# L1 va FIJO en 0.28 um: fijarlo cubre el 78 %% del rango de A y el 98 %%',
      '# del de B, y con el fijo la ley baja de 5 variables a 4.',
      'L1_FIJO = 0.28',
      'FUGA = ' + fmt(CF), '',
      '# --- el TECHO: techo[V] = TECHO . (1, u,u^2,u^3, w,w^2,w^3) -----------',
      '# con u = lg10(W6), w = lg10(L6).  C NO interviene (2.735 V para los',
      '# tres condensadores medidos) y W6 apenas 23 mV en un factor 8.',
      'TECHO = ' + fmt(CT), '',
      '# --- la INYECCION: dV = 10^(INYECCION . base(lgW6,lgL6,lgC,lg(techo-vm)))',
      '# La variable NO es vm, es la DISTANCIA AL TECHO. Con eso, 35 terminos',
      '# sustituyen a los 126 de la version anterior, y el peor caso por',
      '# geometria pasa de 43.7 %% a 11.4 %%.',
      'INYECCION = ' + fmt(CI), '',
      '# --- cajas de validez -------------------------------------------------',
      'CAJA_FUGA = (' + ', '.join('(%.3g, %.3g)' % c for c in CAJA_F) + ')   # W1, W2, L2 [um]',
      'IREF_RANGO = (%.3g, %.3g)   # A' % IREF_R,
      'CAJA_INY = (' + ', '.join('(%.3g, %.3g)' % c for c in CAJA_I) + ')    # W6, L6 [um], C [fF]',
      'VM_RANGO = (1.00, 2.45)   # V',
      'FUGA_MIN = 0.30   # la ley de fuga vale donde I_fuga > FUGA_MIN * Iref', '',
      '# --- el ancho del spike del LIF (entrada, no parametro) ---------------',
      '# Medido sobre el netlist real. Amplitud al riel (3.300 V).',
      'ANCHO_F_KHZ = (26.0, 76.0, 203.0, 501.0, 1219.0, 2743.0, 4902.0)',
      'ANCHO_NS = (33.0, 32.0, 33.0, 33.0, 34.0, 36.0, 39.0)', '',
      '# --- la banda que la cadena puede producir ----------------------------',
      '# EncoderSpec -> Iex 15-1307 nA -> NeuronSpec -> esta banda.',
      '# El techo lo pone el reset del LIF (F_MAX), no el integrador.',
      'BANDA_CADENA = (74.0, 4500.0)   # kHz']
open('coeffs_int.py', 'w', encoding='utf-8').write('\n'.join(S) + '\n')
print('coeffs_int.py: %d lineas' % len(S))
print('  fuga %d coef, techo %d, inyeccion %d' % (len(CF), len(CT), len(CI)))
print('  caja fuga W1 %s W2 %s L2 %s' % tuple('%.2g-%.2g' % c for c in CAJA_F))
print('  caja iny  W6 %.2g-%.2g  L6 %.2g-%.2g  C %.0f-%.0f' % (CAJA_I[0]+CAJA_I[1]+CAJA_I[2]))
