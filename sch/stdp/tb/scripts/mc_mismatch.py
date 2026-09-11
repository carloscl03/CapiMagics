"""Monte Carlo de desapareo sobre las fuentes de corriente.

El PDK trae el modelo:  var_vth = 0.7071 * 0.007148 * 1e-6 / sqrt(Leff*Weff)
o sea sVth(1 um2) = 5.05 mV, pero esta APAGADO por defecto
(design.ngspice:65  sw_stat_mismatch = 0).

La pregunta que decide la geometria: bajar `Idep` de W=10.2/L=2.8 a
W=0.30/L=0.75 gana 3x en DERIVA SISTEMATICA (0.90 -> 0.30 %/mV) pero pierde
area por 127x. Cuanto se paga en DISPERSION ALEATORIA?

Son cosas distintas: la deriva la comparten todas las sinapsis (misma linea de
bias), el desapareo las separa entre si.

TRUCO: N instancias en paralelo en UN solo netlist. `agauss` se evalua por
instancia, asi que cada una saca su propio Vth. Una simulacion en vez de N.
TEST DE ACEPTACION: si las N corrientes salen IDENTICAS, agauss no esta
sorteando por instancia y el metodo no vale.
"""
import os
import subprocess

import numpy as np

os.chdir('/tmp/stdp')
PID = os.getpid()
NG = '/foss/tools/bin/ngspice'
PDK = '/foss/pdks/gf180mcuD/libs.tech/ngspice'
VDD = 3.3
N = 200


def corre(tipo, W, L, vgs, vds, n=N, mismatch=True, serie=1, prefijo='X'):
    """`serie` > 1 apila ese numero de dispositivos en serie, cada uno con su
    propio sorteo -- que es lo que hace de verdad la pila de Itd."""
    L_ = []
    for k in range(n):
        if tipo == 'nfet':
            nodos, vfuente, vpuerta = 'd%d' % k, vds, vgs
        else:
            nodos, vfuente, vpuerta = 'd%d' % k, VDD - vds, VDD - vgs
        if serie == 1:
            L_.append('%s%d %s g %s %s %s_03v3 w=%.6gu l=%.6gu'
                      % (prefijo, k, nodos, 'avss' if tipo == 'nfet' else 'avdd',
                         'avss' if tipo == 'nfet' else 'avdd', tipo, W, L))
        else:
            ant = nodos
            for j in range(serie):
                sig = ('avss' if tipo == 'nfet' else 'avdd') if j == serie - 1 \
                    else 'n%d_%d' % (k, j)
                L_.append('%s%d_%d %s g %s %s %s_03v3 w=%.6gu l=%.6gu'
                          % (prefijo, k, j, ant, sig,
                             'avss' if tipo == 'nfet' else 'avdd', tipo, W, L))
                ant = sig
        L_.append('VD%d d%d 0 %.6f' % (k, k, vfuente))
    cab = ['* monte carlo desapareo',
           '.include %s/design.ngspice' % PDK,
           '.lib %s/sm141064.ngspice typical' % PDK,
           '.param sw_stat_mismatch=%d' % (1 if mismatch else 0),
           'VAVDD avdd 0 %.4f' % VDD, 'VAVSS avss 0 0',
           'VG g 0 %.6f' % vpuerta]
    vec = ' '.join('i(VD%d)' % k for k in range(n))
    sp, dat = 'mc_%d.spice' % PID, 'mc_%d.dat' % PID
    open(sp, 'w').write('\n'.join(
        cab + L_ + ['.control', 'dc VG %.6f %.6f 1' % (vpuerta, vpuerta),
                    'wrdata %s %s' % (dat, vec), '.endc', '.end']) + '\n')
    r = subprocess.run([NG, '-b', sp], capture_output=True, text=True)
    try:
        A = np.atleast_2d(np.loadtxt(dat))
    except Exception:
        return None, r
    return np.abs(A[0, 1::2]), r


def informa(nom, tipo, W, L, vgs, vds, sens, serie=1):
    ii, r = corre(tipo, W, L, vgs, vds, serie=serie)
    if ii is None:
        print('  %-26s FALLO: %s'
              % (nom, (r.stderr.strip().splitlines() or ['?'])[-1]))
        return
    if np.ptp(ii) == 0:
        print('  %-26s TODAS IGUALES -> agauss no sortea por instancia')
        return
    s = 100 * ii.std() / ii.mean()
    area = W * L * serie
    print('  %-26s W=%-6.2f L=%-5.2f x%d  area %7.3f um2   I %9.4g A   '
          'sI/I %6.2f %%   deriva %.2f %%/mV'
          % (nom, W, L, serie, area, ii.mean(), s, sens))


if __name__ == '__main__':
    print('=== control: M vs X con el desapareo APAGADO (deben coincidir) ===')
    for pre in ('M', 'X'):
        ii, r = corre('nfet', 0.61, 2.8, 1.30, 1.89, n=1, mismatch=False,
                      prefijo=pre)
        print('  prefijo %s -> %s' % (pre, 'FALLO' if ii is None else '%.6g A' % ii[0]))

    print('\n=== Idep  (pfet, 2.57 uA, Vds 2.43) ===')
    informa('hoy', 'pfet', 10.2, 2.8, 0.980, 2.43, 0.90)
    informa('propuesto', 'pfet', 0.30, 0.75, 1.391, 2.43, 0.30)
    informa('intermedio', 'pfet', 2.00, 2.80, 1.289, 2.43, 0.37)

    print('\n=== Ipot  (nfet, 5.0 uA, Vds 1.89) ===')
    informa('hoy', 'nfet', 0.61, 2.8, 1.300, 1.89, 0.50)
    informa('propuesto', 'nfet', 0.80, 6.00, 1.492, 1.89, 0.23)

    print('\n=== Itd  (nfet, ~1.1 nA, Vds 0.60) ===')
    informa('la pila de 5 del equipo', 'nfet', 0.5, 10.0, 0.600, 0.60, 1.89,
            serie=5)
    informa('uno solo de L=50', 'nfet', 0.5, 50.0, 0.600, 0.60, 1.89)
