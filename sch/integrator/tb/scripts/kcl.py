"""El desbalance de carga, es un camino que no mido o es deriva residual?

Ley de nodo en vm:   i_iny - i_fuga = C dvm/dt
Integrando en la ventana:   Q_iny - Q_fuga = C * (vm_final - vm_inicial)

Si esa igualdad se cumple, no falta ningun camino: el "desbalance" es solo que
vm todavia deriva, y a frecuencia alta las cargas son tan pequenas que un
milivoltio de deriva se ve como un 10 % de desbalance.

Si NO se cumple, hay carga yendose por donde no miro.
"""
import numpy as np, subprocess, banco

G = [(1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111),
     (1.0,0.28,1.0,1.00,25e-9,0.25,1.0,5111),
     (1.0,0.28,1.0,0.50,50e-9,0.50,0.28,12000)]

def corre(g, f, nset, paso=2e-9):
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    T = 1e6/f*1e-9; nmed = 8
    tfin = T*(1+nset+nmed); vent = T*nmed
    vic = banco.equilibrio(g,f); vic = 2.0 if not np.isfinite(vic) else vic
    L=['* kcl','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'VAMF nf avss 0','XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'VAMI ni avdd 0','XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 %.8gs 2n 2n 32n %.8gs)'%(T,T),
       '.ic v(vm)=%.4f'%vic,'.control','tran %g %.8g %.8g uic'%(paso,tfin,tfin-vent),
       'wrdata k.dat v(vm) i(vamf) i(vami)','.endc','.end']
    open('k.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','k.spice'],capture_output=True)
    A=np.loadtxt('k.dat'); t=A[:,0]; vm=A[:,1]; ifg=A[:,3]; iny=A[:,5]
    Qi=np.trapezoid(iny,t); Qf=np.trapezoid(ifg,t)
    dQ=abs(Qi)-abs(Qf)                       # carga neta que entra
    CdV=Cf*1e-15*(vm[-1]-vm[0])              # la que explica el cambio de vm
    return dict(bal=100*(abs(Qi)/abs(Qf)-1), dQ=dQ, CdV=CdV,
                dvm=1000*(vm[-1]-vm[0]), riz=1000*(vm.max()-vm.min()),
                vm=vm.mean(), Qf=abs(Qf))

print('=== ley de nodo: la carga que no cuadra, explica el cambio de vm? ===')
print('  %6s %5s %6s %10s %11s %11s %9s' %
      ('f[kHz]','caso','nset','balance','dQ [C]','C*dvm [C]','coinciden'))
for f in (1200, 4500):
    for i,g in enumerate(G):
        r = corre(g,f,6)
        rel = 100*abs(r['dQ']-r['CdV'])/max(abs(r['dQ']),1e-20)
        print('  %6d %5d %6d %9.2f%% %11.3e %11.3e %8.1f%%'
              % (f,i,6,r['bal'],r['dQ'],r['CdV'],100-rel))
print()
print('=== y si asiento mas, baja el desbalance? ===')
print('  %6s %5s %6s %10s %9s %9s'%('f[kHz]','caso','nset','balance','dvm','rizado'))
for f in (4500,):
    for i,g in enumerate(G):
        for ns in (6, 40, 200):
            r = corre(g,f,ns)
            print('  %6d %5d %6d %9.2f%% %7.2fmV %7.2fmV'
                  % (f,i,ns,r['bal'],r['dvm'],r['riz']))
