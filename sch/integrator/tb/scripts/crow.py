import numpy as np, subprocess
# 1) corriente estatica del inversor en funcion de la tension de entrada
L=['* corriente de cortocircuito del inversor de entrada',
 '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
 '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
 'VDD vdd 0 3.3','VSS vss 0 0','VIN Iin 0 1.0',
 'M1 sn Iin vdd vdd pfet_03v3 L=0.28u W=0.5u nf=1',
 'M2 sn Iin vss vss nfet_03v3 L=0.28u W=0.5u nf=1',
 '.control','dc VIN 0 3.3 0.02','wrdata cw.dat i(vdd) v(sn)','.endc','.end']
open('cw.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','cw.spice'],capture_output=True)
A=np.loadtxt('cw.dat'); v=A[:,0]; i=np.abs(A[:,1]); vo=A[:,3]
print('=== corriente del inversor SOLO, segun la entrada ===')
for V in (0.5,1.0,1.4,1.6,1.65,1.8,2.0,2.5,3.0):
    j=int(np.argmin(np.abs(v-V))); print('   Vin=%.2f V -> %9.1f nA   (salida %.2f V)'%(V,1e9*i[j],vo[j]))
print()
print('   pico: %.1f uA en Vin=%.2f V'%(1e6*i.max(),v[np.argmax(i)]))
# 2) cuanto tiempo pasa la membrana en la zona de conduccion?
j=np.where(i>0.1*i.max())[0]
print('   la zona donde conduce >10%% del pico: Vin de %.2f a %.2f V (%.0f mV de ancho)'%(v[j[0]],v[j[-1]],1000*(v[j[-1]]-v[j[0]])))
print()
print('=== y la membrana? sube de 0 a ~2.1 V en cada ciclo ===')
print('   asi que cruza esa ventana ENTERA en cada disparo, despacio.')
