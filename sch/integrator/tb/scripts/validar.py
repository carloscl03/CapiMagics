"""Validacion grande de IntegradorSpec. Pensada para dejarla corriendo.

TRES COSAS QUE APRENDI A LA MALA Y VAN AQUI:

  1. EL ASENTAMIENTO SE DERIVA DE tau, NO SE FIJA. tau = C*vm/I_fuga va de 300
     us a milisegundos segun geometria. Fijar "12 periodos" da 81 us a 74 kHz y
     2.7 us a 4500: por eso la validez caia con la frecuencia y por eso anuncie
     tres conclusiones falsas hoy.

  2. UN DATO SIN ASENTAR NO SE DEVUELVE. Antes lo devolvia con una etiqueta que
     luego ignoraba. Aqui, si el balance de carga no baja del 1 %, el punto se
     marca INVALIDO y no entra en ninguna estadistica.

  3. SE GUARDA DESPUES DE CADA PUNTO. Dos trabajos murieron por su propio
     timeout y se perdio la tanda.

Mide, para cada pedido y tres frecuencias: vm, rizado, I_fuga y q.
"""
import json, sys, time
import numpy as np
import banco

PED = json.load(open('pedidos_val.json'))
print('=== validacion: %d pedidos x 3 frecuencias = %d puntos ==='
      % (len(PED), 3*len(PED)))
sys.stdout.flush()

R = []
t00 = time.time()
for i, p in enumerate(PED):
    g = (p['W1'], 0.28, p['W2'], p['L2'], p['Iref']*1e-9, p['W6'], p['L6'], p['C'])
    for nm in ('lo', 'mid', 'hi'):
        f = p['f_' + nm]; vp = p['vm_' + nm]; rp = p['riz_' + nm]
        T = 1e6/f*1e-9
        # asentamiento en TIEMPO ABSOLUTO: 3 tau, repartido en periodos
        nset = int(min(4000, max(12, 3*p['tau']*1e-6/T)))
        o, ok = None, False
        vic = [vp]
        for intento in range(4):
            o = banco.mide([(g, f)], nset=nset, nmed=8,
                           tag='v%d_%s_%d' % (i, nm, intento), vic=vic)[0]
            vic = [o['vm']]
            if np.isfinite(o['vm']) and abs(o['bal']) <= 1.0:
                ok = True
                break
            nset = min(4000, nset*3)
        q = (o['riz']*1e-3*p['C']*1e-15*f*1e3/(o['ifuga']*1e-9)
             if o and o['ifuga'] > 0 else float('nan'))
        R.append(dict(banda=p['banda'], f=f, tau=p['tau'], resol=p['resol'],
                      vm_mot=vp, vm_spice=o['vm'] if o else float('nan'),
                      riz_mot=rp, riz_spice=o['riz'] if o else float('nan'),
                      ifuga=o['ifuga'] if o else float('nan'),
                      bal=o['bal'] if o else float('nan'), q=q, valido=ok,
                      W1=p['W1'], W2=p['W2'], L2=p['L2'], Iref=p['Iref'],
                      W6=p['W6'], L6=p['L6'], C=p['C']))
        np.save('validacion.npy', np.array(R, dtype=object))
    v = [r for r in R if r['valido']]
    print('  %2d/%d  %-10s tau %4.0fus   validos %d/%d   %5.0f min'
          % (i+1, len(PED), p['banda'], p['tau'], len(v), len(R),
             (time.time()-t00)/60))
    sys.stdout.flush()

v = [r for r in R if r['valido']]
print()
print('=== RESULTADO: %d validos de %d ===' % (len(v), len(R)))
if v:
    dv = np.array([1000*(r['vm_mot']-r['vm_spice']) for r in v])
    dr = np.array([100*(r['riz_mot']/r['riz_spice']-1) for r in v if r['riz_spice'] > 0])
    qq = np.array([r['q'] for r in v if np.isfinite(r['q'])])
    print('  vm:     medio %+.1f mV, |medio| %.1f, peor %.1f, negativos %d/%d'
          % (dv.mean(), np.abs(dv).mean(), np.abs(dv).max(), (dv < 0).sum(), len(dv)))
    print('  rizado: medio %+.1f %%, |medio| %.1f %%, peor %.1f %%'
          % (dr.mean(), np.abs(dr).mean(), np.abs(dr).max()))
    print('  q:      mediana %.3f, p10 %.3f, p90 %.3f' %
          (np.median(qq), np.percentile(qq, 10), np.percentile(qq, 90)))
    print()
    print('  dentro de +-25 mV: %d/%d     dentro de +-50 mV: %d/%d'
          % ((np.abs(dv) <= 25).sum(), len(dv), (np.abs(dv) <= 50).sum(), len(dv)))
