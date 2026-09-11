"""El sesgo positivo del balance, es el valor absoluto de la integral?

banco.mide integra |i|. El camino de INYECCION tiene corriente de desplazamiento
bidireccional por la puerta de M6 (flancos de 2 ns): con |i| las dos mitades se
SUMAN en vez de cancelarse, e inflan Q_iny. El de FUGA es unidireccional y no se
infla. De ahi que el error salga siempre positivo -- en los 129 pendientes, sin
una sola excepcion.

Se comprueba sobre datos YA ASENTADOS (arrancando del vm convergido), calculando
las dos versiones sobre el mismo transitorio.
"""
import numpy as np, subprocess

R = list(np.load('barrido_banda3.npy', allow_pickle=True))
P = [r for r in R if r['f'] >= 300 and not r['sat'] and abs(r['bal']) > 1.5]
rng = np.random.default_rng(3)
M = [P[i] for i in rng.choice(len(P), size=14, replace=False)]

def corre(g, f, vic):
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    T = 1e6/f*1e-9; nset, nmed = 12, 8
    tfin = T*(1+nset+nmed); vent = T*nmed
    L=['*','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'VAMF nf avss 0','XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'VAMI ni avdd 0','XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,'VSPK Vext 0 PULSE(0 3.3 %.8gs 2n 2n 32n %.8gs)'%(T,T),
       '.ic v(vm)=%.5f'%vic,'.control','tran 2n %.8g %.8g uic'%(tfin,tfin-vent),
       'wrdata sn.dat v(vm) i(vamf) i(vami)','.endc','.end']
    open('sn.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','sn.spice'],capture_output=True)
    A=np.loadtxt('sn.dat'); t=A[:,0]; vm=A[:,1]; ifg=A[:,3]; iny=A[:,5]
    ba = 100*(np.trapezoid(np.abs(iny),t)/np.trapezoid(np.abs(ifg),t)-1)
    bs = 100*(abs(np.trapezoid(iny,t))/abs(np.trapezoid(ifg,t))-1)
    # cuanta carga bidireccional hay en cada camino
    fi = 100*(np.trapezoid(np.abs(iny),t)-abs(np.trapezoid(iny,t)))/np.trapezoid(np.abs(iny),t)
    ff = 100*(np.trapezoid(np.abs(ifg),t)-abs(np.trapezoid(ifg,t)))/np.trapezoid(np.abs(ifg),t)
    return ba, bs, fi, ff, 1000*(vm.max()-vm.min())

print('=== balance con |i| y con i, sobre datos ya asentados ===')
print('  %7s %10s %10s %10s %10s %9s' %
      ('f[kHz]','bal |i|','bal signo','bidir iny','bidir fuga','rizado'))
ok_a = ok_s = 0
for r in M:
    ba, bs, fi, ff, rz = corre(r['g'], r['f'], r['vm'])
    ok_a += abs(ba) <= 1.5; ok_s += abs(bs) <= 1.5
    print('  %7d %9.2f%% %9.2f%% %9.1f%% %9.1f%% %7.2fmV' % (r['f'], ba, bs, fi, ff, rz))
print()
print('  pasan con |i|: %d/%d      pasan con signo: %d/%d' % (ok_a, len(M), ok_s, len(M)))
