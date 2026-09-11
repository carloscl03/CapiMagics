"""A/B de los dos montajes, sobre LAS MISMAS geometrias.

  VIEJO: vm forzado por una fuente, sin C3 y sin M6. DC puro.
  REAL:  el circuito entero, con C3 y M6 presentes, vm forzado igual.

Si difieren, el 6.4 % es de montaje y no de ley. Si no difieren, el 6.4 % viene
del promedio sobre el rizado en el transitorio, y entonces la ley no esta mal:
lo que esta mal es compararla con una media temporal.
"""
import numpy as np, subprocess, itertools

MO = 'nf=1'
def barre(casos, con_real):
    L = ['* ab','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3','VSS avss 0 0','VM vm 0 1.0']
    vec = []
    for i, (W1,L1,W2,L2,Ir,W6,L6,Cf) in enumerate(casos):
        p = 'b%d' % i
        L += ['I%s avdd %sref %gn' % (p,p,Ir*1e9),
              'XM3_%s %sref %sref avss avss nfet_03v3 L=%gu W=%gu %s' % (p,p,p,L2,W2,MO),
              'XM2_%s avss %sref %svg avss nfet_03v3 L=%gu W=%gu %s' % (p,p,p,L2,W2,MO),
              'XM1_%s %svg %svg %ss avdd pfet_03v3 L=%gu W=%gu %s' % (p,p,p,p,L1,W1,MO),
              'VAM%s vm %ss 0' % (p,p)]
        if con_real:                      # el resto del circuito, colgando de vm
            L += ['XM6_%s vm 0 avdd avss nfet_03v3 L=%gu W=%gu %s' % (p,L6,W6,MO),
                  'C3_%s vm avss %gf' % (p,Cf)]
        vec.append('i(vam%s)' % p)
    L += ['.control','dc VM 0.9 2.45 0.05','wrdata ab.dat ' + ' '.join(vec),'.endc','.end']
    open('ab.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','ab.spice'], capture_output=True)
    A = np.loadtxt('ab.dat')
    return A[:,0], np.abs(A[:,1::2])

rng = np.random.default_rng(2)
R = [r for r in np.load('barrido_final.npy', allow_pickle=True)
     if not r.get('sat') and abs(r['bal']) <= 1.5]
G = sorted({tuple(r['g']) for r in R})
sel = [G[i] for i in rng.choice(len(G), 12, replace=False)]

v, Ia = barre(sel, False)
_, Ib = barre(sel, True)
print('=== el montaje viejo contra el circuito real, mismo vm forzado ===')
print('  %6s %6s %6s %8s %11s %11s %9s' % ('L2','W6','L6','C[fF]','viejo@2.0V','real@2.0V','difer'))
k = int(np.argmin(np.abs(v-2.0)))
d = []
for j, g in enumerate(sel):
    e = 100*(Ib[k,j]/Ia[k,j]-1); d.append(e)
    print('  %6.2f %6.2f %6.2f %8.0f %10.2fnA %10.2fnA %8.2f%%'
          % (g[3],g[5],g[6],g[7],1e9*Ia[k,j],1e9*Ib[k,j],e))
print()
print('  diferencia de montaje: mediana %.2f%%, |max| %.2f%%' % (np.median(d), np.max(np.abs(d))))
print()
print('  Y a lo largo de vm:')
for V in (1.0,1.4,1.8,2.2,2.4):
    kk = int(np.argmin(np.abs(v-V)))
    dd = 100*(Ib[kk,:]/Ia[kk,:]-1)
    print('    vm=%.1f V  mediana %+.2f%%  max %+.2f%%' % (V, np.median(dd), np.max(np.abs(dd))))
