import numpy as np, subprocess
CUERPO=['XM3 x x avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM4 y y avdd avdd pfet_03v3 L=0.394u W=0.947u nf=1',
 'XM1 x Vin  a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM2 y Vinn a avss nfet_03v3 L=1.60u W=0.725u nf=1',
 'XM8 o x avdd avdd pfet_03v3 L=1.86u W=0.93u nf=1','VI o Vmem 0']
def corre(pol,nodo):
    L=['* encoder con dos polarizaciones distintas',
     '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
     'VDD avdd 0 3.3','VSS avss 0 0','VMEM Vmem 0 1.0',
     'VIN Vin 0 1.58','VINN Vinn 0 1.72']+CUERPO
    if pol=='tension':
        L+=['VB Vb 0 1.2','XM9 a Vb avss avss nfet_03v3 L=1.811u W=0.26u nf=1']
    else:
        # la puerta de M9 la fija un diodo alimentado por una corriente inyectada
        L+=['IR avdd nr 90n','XMR nr nr avss avss nfet_03v3 L=1.811u W=0.26u nf=1',
            'XM9 a nr avss avss nfet_03v3 L=1.811u W=0.26u nf=1']
    L+=['.control','dc %s'%nodo,'wrdata pr.dat i(vi)','.endc','.end']
    open('pr.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b','pr.spice'],capture_output=True)
    A=np.loadtxt('pr.dat'); return A[:,0],np.abs(A[:,1])
print('=== la MISMA etapa diferencial, con la puerta de M9 fijada de dos maneras ===')
print()
for pol,nom in [('tension','puerta a una tension fija (Vb = 1.2 V)'),
                ('corriente','puerta a un diodo alimentado por 90 nA')]:
    v,i=corre(pol,'VSS -0.05 0.05 0.005')
    j=int(np.argmin(np.abs(v))); I0=i[j]; d=np.gradient(i,v)[j]
    v2,i2=corre(pol,'VDD 3.25 3.35 0.005')
    j2=int(np.argmin(np.abs(v2-3.3))); d2=np.gradient(i2,v2)[j2]
    print('  %s'%nom)
    print('     Iex = %.1f nA'%(1e9*I0))
    print('     dIex/dVss = %+.3f %%/mV   ->  con 8 mV de rebote: %+.1f %%'%(100*d/I0*1e-3,100*d/I0*1e-3*8))
    print('     dIex/dVdd = %+.3f %%/mV'%(100*d2/I0*1e-3))
    print()
