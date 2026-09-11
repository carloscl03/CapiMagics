"""El "rizado" medido, es integracion o es el patadon capacitivo de la puerta?

En regimen no puede entrar mas carga de la que sale, y sin embargo el pico a
pico medido implica 8x la carga que se fuga en un periodo. La unica salida es
que el max-min NO sea la excursion de integracion: el pulso de 3.3 V en la
puerta de M6 acopla por Cgd al nodo vm.

Se mide el rizado de dos formas sobre el MISMO transitorio:
  TOTAL     max-min de toda la ventana        <- lo que media hasta ahora
  ENTRE     max-min excluyendo el pulso y su cola  <- la integracion de verdad
"""
import json, subprocess, sys
import numpy as np
import banco

sol = json.load(open('pedidos.json'))
print('=== rizado total contra rizado entre spikes ===')
print('  %-12s %8s %10s %10s %9s %11s' %
      ('banda', 'f', 'TOTAL', 'ENTRE', 'glitch', 'ley I/(fC)'))
sys.stdout.flush()

def corre(g, f, vic):
    W1, L1, W2, L2, Ir, W6, L6, Cf = g
    T = 1e6/f*1e-9; an = banco.ancho_ns(f)
    nset, nmed = 12, 8
    tfin = T*(1+nset+nmed); vent = T*nmed
    L = ['*', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0', 'IREF avdd nref %gn' % (Ir*1e9),
         'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1' % (L2, W2),
         'VAMF nf avss 0',
         'XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1' % (L2, W2),
         'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1' % (L1, W1),
         'VAMI ni avdd 0',
         'XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1' % (L6, W6),
         'C3 vm avss %gf' % Cf,
         'VSPK Vext 0 PULSE(0 3.3 %.8gs 2n 2n %.8gn %.8gs)' % (T, an, T),
         '.ic v(vm)=%.5f' % vic, '.control', 'tran 2n %.8g %.8g uic' % (tfin, tfin-vent),
         'wrdata gl.dat v(vm) v(Vext)', '.endc', '.end']
    open('gl.spice', 'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice', '-b', 'gl.spice'], capture_output=True)
    A = np.loadtxt('gl.dat')
    return A[:, 0], A[:, 1], A[:, 3]

vistos = set()
for s in sol:
    key = (s['L2'], s['W2'], s['Iref'], s['C'])
    if key in vistos: continue
    vistos.add(key)
    g = (s['W1'], 0.28, s['W2'], s['L2'], s['Iref']*1e-9, s['W6'], s['L6'], s['C'])
    for f, vp, rp in ((s['f_lo'], s['vm_lo'], s['riz_lo']), (s['f_hi'], s['vm_hi'], s['riz_hi'])):
        t, vm, vx = corre(g, f, vp)
        tot = 1000*(vm.max() - vm.min())
        alto = vx > 1.65
        # excluir el pulso y 3 ns de cola a cada lado
        mala = np.zeros(len(t), bool)
        for i in np.where(np.diff(alto.astype(int)) != 0)[0]:
            mala |= (t > t[i]-4e-9) & (t < t[i]+6e-9)
        mala |= alto
        lim = vm[~mala]
        ent = 1000*(lim.max() - lim.min()) if len(lim) > 10 else float('nan')
        print('  %-12s %8.0f %9.3fmV %9.3fmV %8.1fx %10.3fmV'
              % ('%d-%d' % (s['f_lo'], s['f_hi']), f, tot, ent,
                 tot/ent if ent > 0 else float('nan'), rp))
        sys.stdout.flush()
