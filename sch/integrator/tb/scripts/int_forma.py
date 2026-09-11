"""Se puede escribir el integrador como potencia x correccion, como el encoder?"""
import numpy as np, itertools
# --- la fuga ---------------------------------------------------------------
D=np.load('fuga_bar.npz'); v=D['v']; I=D['I']; cas=D['casos']
X=[];Y=[];VM=[]
for a in range(len(cas)):
    y=np.abs(I[:,a])/cas[a,4]
    m=(y>0.7)&(v<=2.30)
    for k in np.where(m)[0]:
        X.append(list(cas[a,:4])); VM.append(v[k]); Y.append(y[k])
X=np.log10(np.array(X)); VM=np.array(VM); Y=np.array(Y)
print('=== LA FUGA ===')
print('  %d muestras, I/Iref de %.3f a %.3f  (rango %.2fx, NO cruza cero)'
      %(len(Y),Y.min(),Y.max(),Y.max()/Y.min()))
# --- la inyeccion ----------------------------------------------------------
J=np.load('iny3.npz')
print()
print('=== LA INYECCION ===')
print('  claves:',list(J.keys()))
for k in J: print('    %-10s %s'%(k,J[k].shape))
