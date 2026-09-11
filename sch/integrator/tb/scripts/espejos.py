"""Escalar el espejo de salida cambia el NIVEL o tambien la FORMA?

Los 4 espejos del encoder son identicos (Wo=0.93, Lo=1.86) y copian dos nodos:
Iex_1/2 del nodo x, Iex_3/4 del nodo y. Si se quiere que cada salida cubra un
rango distinto de frecuencia, habria que escalar cada espejo.

La pregunta: al escalar, la EXCURSION (Iex_max/Iex_min) se mantiene? Si se
mantiene, cada salida puede tener otro NIVEL pero no otro SPAN, y eso es un
limite duro que IntegradorSpec/EncoderSpec tienen que declarar.
"""
import numpy as np, subprocess

MO = 'nf=1'
LD, W9, WD, WL, LL, L9 = 1.60, 0.26, 0.725, 0.947, 0.394, 1.811
ESP = [(0.93,1.86), (1.86,1.86), (0.465,1.86), (0.93,0.93), (0.93,3.72), (3.72,1.86)]

def corre(vdif):
    vcm = 1.69
    L = ['* espejos','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD Vdd 0 3.3','VB Vb 0 1.2',
         'VP p 0 %.5f' % (vcm+vdif/2), 'VN n 0 %.5f' % (vcm-vdif/2),
         'XM1 x p a 0 nfet_03v3 L=%gu W=%gu %s' % (LD,WD,MO),
         'XM2 y n a 0 nfet_03v3 L=%gu W=%gu %s' % (LD,WD,MO),
         'XM3 x x Vdd Vdd pfet_03v3 L=%gu W=%gu %s' % (LL,WL,MO),
         'XM4 y y Vdd Vdd pfet_03v3 L=%gu W=%gu %s' % (LL,WL,MO),
         'XM9 a Vb 0 0 nfet_03v3 L=%gu W=%gu %s' % (L9,W9,MO)]
    vec = []
    for i,(wo,lo) in enumerate(ESP):
        L += ['XMO%d o%d x Vdd Vdd pfet_03v3 L=%gu W=%gu %s' % (i,i,lo,wo,MO),
              'VO%d o%d 0 1.0' % (i,i)]
        vec.append('i(vo%d)' % i)
    L += ['.control','op','print '+' '.join(vec),'.endc','.end']
    open('es.spice','w').write('\n'.join(L)+'\n')
    r = subprocess.run(['ngspice','-b','es.spice'],capture_output=True,text=True)
    d = {}
    for t in r.stdout.splitlines():
        t = t.strip()
        if '=' in t and t.split('=')[0].strip().startswith('i(vo'):
            try: d[t.split('=')[0].strip()] = abs(float(t.split('=')[1]))
            except: pass
    return np.array([d.get('i(vo%d)'%i, np.nan) for i in range(len(ESP))])

lo_ = corre(-0.14); hi_ = corre(+0.14)
print('  %6s %6s %12s %12s %10s %10s' % ('Wo','Lo','Iex(-)[nA]','Iex(+)[nA]','EXCURSION','vs base'))
base = None
for i,(wo,lo) in enumerate(ESP):
    ex = hi_[i]/lo_[i]
    if base is None: base = ex
    print('  %6.3f %6.2f %11.2f %11.2f %10.3f %9.2f%%'
          % (wo, lo, 1e9*lo_[i], 1e9*hi_[i], ex, 100*(ex/base-1)))
print()
print('  Si la EXCURSION es la misma para todos: cada salida puede tener otro')
print('  NIVEL pero no otro SPAN. Ese es el limite que hay que declarar.')
