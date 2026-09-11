"""La proyeccion que usa el diseno: a CORRIENTE OBJETIVO FIJA, que geometria
da la menor sensibilidad.

La tabla anterior (sensibilidad sobre todo el rango de Vgs) engana, porque cada
geometria cubre ese rango en una zona distinta de inversion. Lo que el disenador
necesita es: "quiero 1 nA aqui; que W y L me lo dan con menos deriva".
"""
import numpy as np

W_G = [0.30, 0.80, 2.0, 5.0, 12.0]
L_G = [0.35, 0.75, 1.6, 2.8, 6.0]

# las cuatro fuentes: (nombre, tipo, corriente objetivo, Vds en que trabaja)
FUENTES = [('Idep', 'pfet', 2.57e-6, 2.43),
           ('Ipot', 'nfet', 5.00e-6, 1.89),
           ('Itd', 'nfet', 1.10e-9, 0.60),
           ('Itp', 'pfet', 2.00e-9, 0.30)]


def carga(t):
    A = np.load('dev_%s.npz' % t)['filas']
    return dict(W=A[:, 0], L=A[:, 1], vg=A[:, 2], vd=A[:, 3], i=np.abs(A[:, 4]))


D = {t: carga(t) for t in ('nfet', 'pfet')}


def en_punto(tipo, W, L, vds, itgt):
    """Vgs que da la corriente objetivo, y la sensibilidad AHI mismo."""
    d = D[tipo]
    vd = min(sorted(set(d['vd'])), key=lambda x: abs(x - vds))
    m = (d['W'] == W) & (d['L'] == L) & (d['vd'] == vd)
    vg, ii = d['vg'][m], d['i'][m]
    o = np.argsort(vg)
    vg, ii = vg[o], ii[o]
    u = ii > 1e-13
    vg, ii = vg[u], ii[u]
    if len(ii) < 4 or not (ii.min() <= itgt <= ii.max()):
        return None                      # la geometria NO alcanza esa corriente
    vgs = float(np.interp(np.log(itgt), np.log(ii), vg))
    # pendiente local: +-40 mV alrededor
    s = (np.abs(vg - vgs) < 0.045)
    if s.sum() < 3:
        return None
    k = np.polyfit(vg[s], np.log(ii[s]), 1)[0]
    return vgs, 100 * (np.exp(k / 1000) - 1)


for nom, tipo, itgt, vds in FUENTES:
    print('\n' + '=' * 74)
    print('%s   objetivo %.4g A   (%s, Vds = %.2f V)' % (nom, itgt, tipo, vds))
    print('=' * 74)
    print('  Vgs necesaria [V]  y  sensibilidad [%/mV].  "-" = no alcanza')
    print('  %6s' % 'W\\L' + ''.join('%15.2f' % L for L in L_G))
    mejor = None
    for W in W_G:
        fila = '  %6.2f' % W
        for L in L_G:
            r = en_punto(tipo, W, L, vds, itgt)
            if r is None:
                fila += '%15s' % '-'
                continue
            vgs, s = r
            fila += '%9.3f/%5.2f' % (vgs, s)
            if mejor is None or s < mejor[0]:
                mejor = (s, W, L, vgs)
        print(fila)
    if mejor:
        s, W, L, vgs = mejor
        print('  -> minima deriva: W=%.2f L=%.2f con Vgs=%.3f  ->  %.2f %%/mV'
              % (W, L, vgs, s))
