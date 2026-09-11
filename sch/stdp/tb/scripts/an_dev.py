"""Analisis de los 8600 puntos de dispositivo.

Tres preguntas, ninguna supuesta:

  1. COLAPSA `I` a `W/L`?  Si colapsa, la ley baja de 4 variables a 3 y
     esta justificado tratarlas juntas. Si no, `W` y `L` son dos variables
     de verdad y hay que decir donde falla.
  2. CUANTO SE MUEVE `I` por mV de `Vgs`, y se puede bajar con geometria?
     Sin espejos, esto es la robustez de todo el circuito.
  3. CUANTO SE MUEVE `I` con `Vds`?  El drenador de cada fuente es un nodo
     VIVO (n5, n4, vdep, vpot): si la corriente depende de `Vds`, el bias deja
     de ser constante y pasa a depender de si la sinapsis esta disparando.
"""
import numpy as np

W_G = [0.30, 0.80, 2.0, 5.0, 12.0]
L_G = [0.35, 0.75, 1.6, 2.8, 6.0]


def carga(t):
    A = np.load('dev_%s.npz' % t)['filas']
    return dict(W=A[:, 0], L=A[:, 1], vg=A[:, 2], vd=A[:, 3], i=np.abs(A[:, 4]))


def sep(t):
    print('\n' + '=' * 74)
    print(t)
    print('=' * 74)


for tipo in ('nfet', 'pfet'):
    d = carga(tipo)
    sep('%s  --  1. TEST DE COLAPSO:  I depende solo de W/L?' % tipo.upper())
    print('  dispersion de  I*L/W  entre geometrias, a igual (Vgs, Vds).')
    print('  1.00 = colapso perfecto.\n')
    print('  %8s %30s' % ('Vds', 'razon max/min de I*L/W'))
    print('  %8s %12s %12s %12s' % ('', 'todas', 'sin L=0.35', 'solo L>=1.6'))
    for vd in sorted(set(d['vd'])):
        fil = []
        for sel, nom in ((None, 'todas'), (0.35, 'sin corta'), (1.6, 'largas')):
            r = []
            for vg in sorted(set(d['vg']))[::6]:
                m = (d['vd'] == vd) & (np.abs(d['vg'] - vg) < 1e-6)
                if sel == 0.35:
                    m &= d['L'] > 0.4
                elif sel == 1.6:
                    m &= d['L'] >= 1.6
                j = d['i'][m] * d['L'][m] / d['W'][m]
                j = j[j > 1e-14]
                if len(j) > 2:
                    r.append(j.max() / j.min())
            fil.append(np.median(r) if r else np.nan)
        print('  %8.2f %12.2f %12.2f %12.2f' % (vd, fil[0], fil[1], fil[2]))

    sep('%s  --  2. SENSIBILIDAD  d(lnI)/dVgs   [%%/mV]' % tipo.upper())
    print('  Se puede bajar con geometria, o es n*VT y no hay nada que hacer?\n')
    print('  %6s' % 'W\\L' + ''.join('%9.2f' % L for L in L_G))
    for W in W_G:
        fila = '  %6.2f' % W
        for L in L_G:
            m = (d['W'] == W) & (d['L'] == L) & (d['vd'] == 2.1)
            vg, ii = d['vg'][m], d['i'][m]
            o = np.argsort(vg)
            vg, ii = vg[o], ii[o]
            u = (ii > 1e-11) & (ii < 1e-5)
            if u.sum() < 5:
                fila += '        -'
                continue
            k = np.polyfit(vg[u], np.log(ii[u]), 1)[0]
            fila += '%9.2f' % (100 * (np.exp(k / 1000) - 1))
        print(fila)

    sep('%s  --  3. DEPENDENCIA DE Vds:  I(3.0V)/I(0.3V)' % tipo.upper())
    print('  El drenador es un nodo vivo. 1.00 = fuente de corriente de verdad.\n')
    print('  %6s' % 'W\\L' + ''.join('%9.2f' % L for L in L_G))
    for W in W_G:
        fila = '  %6.2f' % W
        for L in L_G:
            m = (d['W'] == W) & (d['L'] == L)
            r = []
            for vg in sorted(set(d['vg']))[::6]:
                a = d['i'][m & (d['vd'] == 0.3) & (np.abs(d['vg'] - vg) < 1e-6)]
                b = d['i'][m & (d['vd'] == 3.0) & (np.abs(d['vg'] - vg) < 1e-6)]
                if len(a) and len(b) and a[0] > 1e-13:
                    r.append(b[0] / a[0])
            fila += '%9.2f' % (np.median(r) if r else np.nan)
        print(fila)
