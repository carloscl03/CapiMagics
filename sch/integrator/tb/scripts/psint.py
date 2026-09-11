import numpy as np, subprocess
def corre(nodo,L2,Ir,W6,L6):
    L=['* sensibilidad del integrador al riel','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
     'VDD avdd 0 3.3','VSS avss 0 0','IREF avdd nref %gn'%Ir,
     'XM3 nref nref avss avss nfet_03v3 L=%gu W=1u nf=1'%L2,
     'XM2 avss nref vg avss nfet_03v3 L=%gu W=1u nf=1'%L2,
     'XM1 vg vg vm avdd pfet_03v3 L=0.28u W=1u nf=1',
     'XM6 vm avss avdd avss nfet_03v3 L=%gu W=%gu nf=1'%(L6,W6),
     'VMM vm 0 2.0',
     '.control','dc %s'%nodo,'wrdata pi.dat i(vmm)','.endc','.end']
    open('pi.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','pi.spice'],capture_output=True)
    A=np.loadtxt('pi.dat'); return A[:,0], np.abs(A[:,1])
print('=== INTEGRADOR: sensibilidad de la FUGA al riel (en vm = 2.0 V) ===')
for nom,(L2,Ir,W6,L6) in [('original  L2=0.28 Iref=50n',(0.28,50,1.0,0.28)),
                          ('mejorado  L2=1.0  Iref=25n',(1.00,25,0.25,1.0))]:
    v,i=corre('VDD 3.25 3.35 0.005',L2,Ir,W6,L6)
    j=int(np.argmin(np.abs(v-3.3))); I0=i[j]; dd=np.gradient(i,v)[j]
    v,i=corre('VSS -0.05 0.05 0.005',L2,Ir,W6,L6)
    j=int(np.argmin(np.abs(v))); ds=np.gradient(i,v)[j]
    print('  %-28s  fuga %6.1f nA'%(nom,1e9*I0))
    print('      dI/dVdd  %7.3f %%/mV      dI/dVss  %7.3f %%/mV'%(100*dd/I0*1e-3,100*ds/I0*1e-3))
    print('      con 8 mV de rebote en Vss:  la fuga cambia %.1f %%'%(abs(100*ds/I0*1e-3)*8))
