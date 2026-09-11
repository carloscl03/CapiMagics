"""Los interruptores de escritura del peso: M3 (depresion) y M2 (potenciacion).

Son los duenos del SUELO DE INYECCION, que es el termino no hebbiano -- el que
hace derivar el peso con actividad presinaptica sola, y el que limita la cola
util de la ventana.

HIPOTESIS, y es comprobable:
  El suelo es carga de puerta: Cgdo*W (solapamiento) + Cox*W*L*Vov (canal).
  Va con W, y con L solo la parte de canal.
  La SENAL, en cambio, no la limita M3: su puerta esta a 3.3 V mientras que
  M4 (puerta = vdep ~ 0.77 V) esta subumbral y es el cuello de botella.
  => estrechar M3 deberia bajar el suelo SIN tocar la senal.
Si es verdad, el interruptor minimo es estrictamente mejor y no hay compromiso.
Si es falso, la senal caera con W y habra un optimo.

Aqui `W` y `L` van SEPARADAS: la parte de solapamiento va solo con W, la de
canal con W*L. Colapsarlas a W/L perderia justo la distincion que se busca.
"""
import os
import re
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import carac_stdp as K

W_G = [0.22, 0.30, 0.50, 1.00, 2.00]
# CORREGIDO: el suelo BAJA al alargar L (5.48 -> 3.79 mV de 0.63 a 2.0),
# al reves de lo que predije con el modelo de carga de canal. La rejilla se
# extiende hacia L largas, que es donde esta la mejora.
L_G = [0.28, 0.63, 1.50, 3.00, 6.00]
NCW = 5                       # suelo grande = mas facil de medir limpio
VDEP_SENAL = 0.85
VPOT_SENAL = 3.30 - 0.85      # el espejo: la traza pot baja desde avdd


def dim(txt, devs, W, L):
    """Reescribe W y L de dispositivos concretos. Nada de W/L: dos numeros."""
    out = []
    for l in txt.splitlines():
        t = l.strip()
        if any(t.startswith(d + ' ') for d in devs):
            l = re.sub(r'\bL=\S+', 'L=%.6gu' % L, l)
            l = re.sub(r'\bW=\S+', 'W=%.6gu' % W, l)
        out.append(l)
    return '\n'.join(out)


def mide(lado, W, L):
    """Devuelve (suelo, senal) en voltios para una geometria del interruptor."""
    dep = lado == 'dep'
    nodo = 'vdep' if dep else 'vpot'
    dev = ['M3'] if dep else ['M2']
    base = dim(K.BASE, dev, W, L)
    cel = K.forzado(K.caps(base, ncw=NCW), nodo)
    r = []
    for v in ((0.0, VDEP_SENAL) if dep else (3.3, VPOT_SENAL)):
        cuerpo = K.bias() + ['VF%s %sf 0 %.4f' % (nodo, nodo, v)]
        cuerpo += (K.pulso('vpre', 'nvpre', K.T0, K.DTP0)
                   + K.quieto('vpost', 'nvpost') if dep else
                   K.pulso('vpost', 'nvpost', K.T0, K.DTP0)
                   + K.quieto('vpre', 'nvpre'))
        d = K.corre(cuerpo, K.tran(K.T0 + K.DTP0 + 300e-9, forzado=nodo), cel,
                    extra=' %sf' % nodo)
        if not K.arranco_bien(d):
            return None, None
        r.append(float(d['V']['vw'][-1] - K.VW0))
    return r[0], r[1] - r[0]


if __name__ == '__main__':
    t0 = time.time()
    for lado in ('dep', 'pot'):
        print('\n=== interruptor de %s  (%s) ==='
              % (lado, 'M3, nfet' if lado == 'dep' else 'M2, pfet'), flush=True)
        print('  %6s %6s %12s %12s %10s'
              % ('W', 'L', 'suelo[mV]', 'senal[mV]', 'senal/suelo'), flush=True)
        filas = []
        for W in W_G:
            for L in L_G:
                s, g = mide(lado, W, L)
                if s is None:
                    print('  %6.2f %6.2f   RECHAZADO' % (W, L), flush=True)
                    continue
                r = abs(g / s) if abs(s) > 1e-9 else float('nan')
                filas.append((W, L, s, g, r))
                print('  %6.2f %6.2f %12.4f %12.4f %10.2f'
                      % (W, L, s * 1e3, g * 1e3, r), flush=True)
                np.savez('sw_%s.npz' % lado, filas=np.array(filas, float))
        print('  [%.1f min]' % ((time.time() - t0) / 60), flush=True)
