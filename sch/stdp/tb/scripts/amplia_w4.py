"""Ampliar la caja de W4: 0.90 era donde deje de medir, no un limite.

El motor recortaba W1 de 0.80 a 0.785 porque A+ se pasaba 7.5 mV del maximo de
la depresion -- y ese maximo salia de W4 = 0.90, que es solo el ultimo punto
del barrido. El bin del PDK llega a 10 um.

Se extiende hasta donde deje de tener sentido, y se anota DONDE ESTA EL LIMITE
DE VERDAD si aparece alguno.
"""
import os, sys, time
import numpy as np
sys.path.insert(0, '/tmp/stdp'); os.chdir('/tmp/stdp')
import carac_stdp as K
import sw_barrido as S

L4 = 0.28
W_G = [1.15, 1.50, 2.00, 2.80, 4.00]     # continua donde acababa (0.90)
VDEP = np.round(np.arange(0.500, 1.0001, 0.025), 4)
NCW = 10

t0 = time.time(); filas = []
print('  %6s %12s %12s %12s' % ('W4','suelo[mV]','senal@0.75','senal@1.00'), flush=True)
for W in W_G:
    cel = K.forzado(K.caps(S.dim(K.BASE, ['M4'], W, L4), ncw=NCW), 'vdep')
    vals, mal = [], False
    for v in [0.0] + list(VDEP):
        cuerpo = (K.bias() + ['VFvdep vdepf 0 %.4f' % v]
                  + K.pulso('vpre','nvpre',K.T0,K.DTP0) + K.quieto('vpost','nvpost'))
        d = K.corre(cuerpo, K.tran(K.T0+K.DTP0+300e-9, forzado='vdep'), cel,
                    extra=' vdepf')
        if not K.arranco_bien(d): mal = True; break
        vals.append(float(d['V']['vw'][-1] - K.VW0))
    if mal:
        print('  %6.2f   RECHAZADO' % W, flush=True); continue
    suelo, sen = vals[0], np.array(vals[1:]) - vals[0]
    for v, s in zip(VDEP, sen): filas.append((W, L4, v, suelo, s))
    k = int(np.argmin(np.abs(VDEP-0.75)))
    print('  %6.2f %12.4f %12.4f %12.4f'
          % (W, suelo*1e3, sen[k]*1e3, sen[-1]*1e3), flush=True)
    np.savez('nucleo_w_ext.npz', filas=np.array(filas, float))
print('  %d puntos [%.1f min]' % (len(filas), (time.time()-t0)/60), flush=True)
