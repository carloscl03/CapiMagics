"""Piloto v2: ventana de un numero ENTERO de periodos + test de equilibrio.

En v1 el balance de carga fallaba un 35 % a 74 kHz. No era el circuito: la
ventana de 20 us fijos son 1.48 periodos a esa frecuencia, y atrapa a veces uno
y a veces dos spikes. Aqui la ventana se ata al periodo.

El equilibrio se comprueba comparando DOS ventanas consecutivas: si vm todavia
deriva, el transitorio no ha acabado y el dato no vale.
"""
import numpy as np, subprocess, math

def corre(g, f_kHz, nper=8, nset=60):
    """nper periodos de medida; nset periodos de asentamiento previos."""
    W1,L1,W2,L2,Ir,W6,L6,Cf = g
    T = 1e6/f_kHz*1e-9
    vent = 2*nper*T                    # DOS ventanas seguidas, para el test
    tfin = 5e-6 + (nset + 2*nper)*T
    paso = min(2e-9, T/200)
    L=['* piloto2','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD avdd 0 3.3','VSS avss 0 0',
       'IREF avdd nref %gn'%(Ir*1e9),
       'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'VAMF nf avss 0',
       'XM2 nf nref vg avss nfet_03v3 L=%gu W=%gu nf=1'%(L2,W2),
       'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1'%(L1,W1),
       'VAMI ni avdd 0',
       'XM6 vm Vext ni avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
       'C3 vm avss %gf'%Cf,
       'VSPK Vext 0 PULSE(0 3.3 5u 2n 2n 32n %.8gs)'%T,
       '.ic v(vm)=2.0','.control',
       'tran %g %g %g uic'%(paso,tfin,tfin-vent),
       'wrdata p2.dat v(vm) i(vamf) i(vami)','.endc','.end']
    open('p2.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','p2.spice'],capture_output=True)
    A=np.loadtxt('p2.dat'); t=A[:,0]; vm=A[:,1]; ifg=A[:,3]; iny=A[:,5]
    mit=t[0]+(t[-1]-t[0])/2
    a=t<mit; b=~a
    res={}
    for nm,m in (('1',a),('2',b)):
        res[nm]=(vm[m].mean(), vm[m].max()-vm[m].min(),
                 np.trapezoid(np.abs(ifg[m]),t[m]), np.trapezoid(np.abs(iny[m]),t[m]))
    v1,r1,qf1,qi1=res['1']; v2,r2,qf2,qi2=res['2']
    return dict(vm=v2, riz=1000*r2, deriva=1000*(v2-v1),
                bal=100*(qi2/qf2-1) if qf2>0 else float('nan'),
                ifuga=1e9*qf2/(t[b][-1]-t[b][0]))

G=[(1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111),
   (1.0,0.28,1.0,1.00,25e-9,0.25,1.0,5111)]
NOM=['ORIGINAL','MEJORADO']
FS=[74,150,300,600,1200,2400,4500]
print('=== piloto v2: ventana entera de periodos ===')
print('  deriva = cuanto se mueve vm entre dos ventanas seguidas (0 = equilibrio)')
print()
print('  %-9s %7s %9s %8s %9s %9s %10s'%('diseño','f[kHz]','vm','rizado','deriva','balance','I_fuga'))
for g,nom in zip(G,NOM):
    for f in FS:
        r=corre(g,f)
        print('  %-9s %7d %8.3fV %7.0fmV %8.1fmV %8.2f%% %8.2fnA'
              %(nom,f,r['vm'],r['riz'],r['deriva'],r['bal'],r['ifuga']))
    print()
