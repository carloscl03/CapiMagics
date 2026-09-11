"""Los dos grupos de transistores que quedan, cada uno con su figura de merito.

GRUPO DIODO  (M9 en depresion, M7 en potenciacion)
  Son los duenos del REPARTO. La fuente de bias entrega su corriente al nodo
  intermedio y el diodo se lleva la parte que no va al condensador. Por eso
  `Idep` es corriente PERMANENTE: 2.57 uA por sinapsis, ~21 uA con las ocho.
  Figura de merito:  Vdep0 conseguido POR uA de corriente permanente.
  Cuanto mas alta, menos potencia hace falta para la misma traza.

GRUPO LECTURA  (M4 en depresion, M1 en potenciacion)
  Son los duenos del E-PLEGADO: 73.9 mV en depresion, 138.0 en potenciacion.
  Eso es la pendiente subumbral de la lectura, y decide cuanto cambia la tasa
  de aprendizaje por cada mV de deriva del bias -- el factor 180 por 600 mV.
  Figura de merito:  mV de traza por e-plegado. Cuanto mas ALTO, mas suave.

W y L separadas en los dos, por lo mismo de siempre.
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

W_G = [0.22, 0.50, 1.20, 3.00, 8.00]
L_G = [0.28, 0.63, 1.50, 3.00, 6.00]
NCW = 10
# La ventana de ajuste TIENE que estar fijada: el e-plegado es la pendiente
# local de una curva que no es exponencial pura. Con 0.6-1.1 sale 100.4 mV, con
# la zona subumbral de verdad sale 73.9, que es la referencia de L3. Mismo dato,
# distinta ventana -> si no se declara, el numero no significa nada.
VDEP_EXP = [0.58, 0.65, 0.72, 0.79, 0.86, 0.93]


def diodo(lado, W, L):
    """Corriente permanente y amplitud de traza conseguida con ella."""
    dep = lado == 'dep'
    dev, nodo = (['M9'], 'vdep') if dep else (['M7'], 'vpot')
    amp_i, amp_q = ('vam_dep', 'vam_c') if dep else ('vam_pot', 'vam_cp')
    cel = K.caps(S.dim(K.BASE, dev, W, L), ncw=NCW)
    cuerpo = K.bias()
    cuerpo += (K.pulso('vpost', 'nvpost', K.T0, K.DTP0) + K.quieto('vpre', 'nvpre')
               if dep else
               K.pulso('vpre', 'nvpre', K.T0, K.DTP0) + K.quieto('vpost', 'nvpost'))
    d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9), cel)
    if not K.arranco_bien(d):
        return None
    t, v = d['t'], d['V'][nodo]
    ii = float(np.median(np.abs(d['I'][amp_i][t < K.T0 - 10e-9])))   # permanente
    qq = abs(K.q(d['I'][amp_q], t, K.T0 - 5e-9, K.T0 + K.DTP0 + 20e-9))
    v0 = float(v.max() - v[0]) if dep else float(v[0] - v.min())
    return ii, v0, qq


def lectura(lado, W, L):
    """e-plegado del nucleo: mV de traza por factor e en DVw."""
    dep = lado == 'dep'
    dev, nodo = (['M4'], 'vdep') if dep else (['M1'], 'vpot')
    cel = K.forzado(K.caps(S.dim(K.BASE, dev, W, L), ncw=NCW), nodo)
    vals = []
    for v in ([0.0] + VDEP_EXP if dep else
              [3.3] + [3.3 - x for x in VDEP_EXP]):
        cuerpo = K.bias() + ['VF%s %sf 0 %.4f' % (nodo, nodo, v)]
        cuerpo += (K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
                   + K.quieto('vpost', 'nvpost') if dep else
                   K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
                   + K.quieto('vpre', 'nvpre'))
        d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado=nodo), cel,
                    extra=' %sf' % nodo)
        if not K.arranco_bien(d):
            return None
        vals.append(float(d['V']['vw'][-1] - K.VW0))
    suelo, sen = vals[0], np.abs(np.array(vals[1:]) - vals[0])
    u = sen > 1e-5
    if u.sum() < 4:
        return None
    x = np.array(VDEP_EXP)[u]
    k = np.polyfit(x, np.log(sen[u]), 1)[0]
    return 1000.0 / abs(k), suelo * 1e3, sen.max() * 1e3


if __name__ == '__main__':
    t0 = time.time()
    for lado in ('dep', 'pot'):
        print('\n=== DIODO de %s (%s) ===' % (lado, 'M9' if lado == 'dep' else 'M7'),
              flush=True)
        print('  %6s %6s %12s %10s %14s'
              % ('W', 'L', 'I perm[uA]', 'V0[V]', 'V0/I [V/uA]'), flush=True)
        f = []
        for W in W_G:
            for L in L_G:
                r = diodo(lado, W, L)
                if r is None:
                    print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True)
                    continue
                ii, v0, qq = r
                fom = v0 / (ii * 1e6) if ii > 1e-12 else float('nan')
                f.append((W, L, ii, v0, qq))
                print('  %6.2f %6.2f %12.4f %10.4f %14.4f'
                      % (W, L, ii * 1e6, v0, fom), flush=True)
                np.savez('dio_%s.npz' % lado, filas=np.array(f, float))
        print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)

    for lado in ('dep', 'pot'):
        print('\n=== LECTURA de %s (%s) ===' % (lado, 'M4' if lado == 'dep' else 'M1'),
              flush=True)
        print('  %6s %6s %14s %12s %12s'
              % ('W', 'L', 'e-plegado[mV]', 'suelo[mV]', 'max senal[mV]'), flush=True)
        f = []
        for W in W_G:
            for L in L_G:
                r = lectura(lado, W, L)
                if r is None:
                    print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True)
                    continue
                ef, su, mx = r
                f.append((W, L, ef, su, mx))
                print('  %6.2f %6.2f %14.1f %12.4f %12.4f'
                      % (W, L, ef, su, mx), flush=True)
                np.savez('lec_%s.npz' % lado, filas=np.array(f, float))
        print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)
