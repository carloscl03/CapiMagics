"""Competencia de familias para el integrador, sobre la banda real.

DOS OBJETIVOS, que son lo que IntegradorSpec necesita:
    vm(f, geometria)      la lectura
    rizado(f, geometria)  el ruido de esa lectura; su cociente es la resolucion

VALIDACION EXTERNA POR GEOMETRIA, no por punto. Separar puntos al azar deja
puntos de la misma geometria a los dos lados y el error sale optimista: la ley
solo tendria que interpolar en frecuencia, que es lo facil.

Variables: L2, Iref, W6, L6, C (geometria) y f. W1, L1, W2 van fijos.
"""
import itertools
import numpy as np

R = [r for r in np.load('barrido_final.npy', allow_pickle=True)
     if not r.get('sat') and np.isfinite(r['vm']) and abs(r['bal']) <= 1.5]

G = np.array([[r['g'][3], r['g'][4], r['g'][5], r['g'][6], r['g'][7]] for r in R])
F = np.array([r['f'] for r in R], float)
VM = np.array([r['vm'] for r in R])
RZ = np.array([r['riz'] for r in R])
IF = np.array([r['ifuga'] for r in R])
X = np.column_stack([np.log10(G), np.log10(F)])          # 6 variables
NOM = ['L2', 'Iref', 'W6', 'L6', 'C', 'f']

geos = sorted({tuple(g) for g in G})
rng = np.random.default_rng(7)
ge = list(geos); rng.shuffle(ge)
ncut = int(0.7 * len(ge))
tr_g, te_g = set(ge[:ncut]), set(ge[ncut:])
tr = np.array([tuple(g) in tr_g for g in G])
te = ~tr
print('=== %d puntos, %d geometrias  (%d entrenan / %d validan) ==='
      % (len(R), len(geos), len(tr_g), len(te_g)))
print('    %d puntos de entrenamiento, %d externos POR GEOMETRIA' % (tr.sum(), te.sum()))
print()

def compite(y, log, titulo, cands, Z=None):
    Z = X if Z is None else Z
    print('=== %s ===' % titulo)
    print('  %-36s %6s %10s %9s' % ('forma', 'coef', 'EXTERNO', 'peor'))
    res = []
    for nm, gr in cands:
        E = [e for e in itertools.product(*[range(g+1) for g in gr]) if sum(e) <= max(gr)]
        B = np.column_stack([np.prod(Z ** np.array(e), axis=1) for e in E])
        if B.shape[1] >= tr.sum():
            print('  %-36s %6d   (mas terminos que datos)' % (nm, B.shape[1])); continue
        c = np.linalg.lstsq(B[tr], y[tr], rcond=None)[0]
        d = B[te] @ c - y[te]
        er = 100*np.abs(10**d - 1) if log else 1000*np.abs(d)
        u = '%' if log else 'mV'
        print('  %-36s %6d %8.2f%s %7.2f%s' % (nm, B.shape[1], er.mean(), u, np.percentile(er,90), u))
        res.append((er.mean(), nm, B.shape[1]))
    print()
    return sorted(res)

C1 = [('potencia / lineal    (1,1,1,1,1,1)', (1,)*6),
      ('cuadratica           (2,2,2,2,2,2)', (2,)*6),
      ('cubica               (3,3,3,3,3,3)', (3,)*6),
      ('cuad geom, cubica f  (2,2,2,2,2,3)', (2,2,2,2,2,3)),
      ('lineal geom, cubica f(1,1,1,1,1,3)', (1,1,1,1,1,3))]

compite(VM, False, 'vm  [se mide en mV de error]', C1)
compite(np.log10(RZ), True, 'rizado  [decadas -> % de error]', C1)

# --- busqueda de colapso para el rizado ------------------------------------
print('=== colapso del rizado: la carga por periodo entre el condensador ===')
print('  Si el rizado es la carga de un periodo dividida por C, entonces')
print('  rizado * C * f / I_fuga deberia ser casi constante. Se comprueba.')
q = RZ * 1e-3 * G[:, 4] * 1e-15 * F * 1e3 / (IF * 1e-9)
print('  rizado*C*f/I_fuga :  mediana %.3f   p10 %.3f   p90 %.3f   dispersion %.2fx'
      % (np.median(q), np.percentile(q, 10), np.percentile(q, 90),
         np.percentile(q, 90)/np.percentile(q, 10)))
print()
Z2 = np.column_stack([np.log10(G), np.log10(F)])
compite(np.log10(q), True, 'el residuo del colapso (que le falta al 1/(f*C))', C1, Z=Z2)
