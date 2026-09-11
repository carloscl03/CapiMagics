import numpy as np, itertools
J=np.load('iny3.npz'); C=J['casos']; V0=J['V0']; dV=J['dV']
print('=== por que la inyeccion no tiene forma corta ===')
print('  dV va de %.4f a %.4f V'%(np.nanmin(dV),np.nanmax(dV)))
neg=(dV<=0)&np.isfinite(dV)
print('  casos con dV <= 0: %d de %d (%.1f%%)  <- una potencia NO puede hacer esto'
      %(neg.sum(),dV.size,100*neg.sum()/dV.size))
fin=np.isfinite(dV)
print('  dV minimo positivo: %.2e V   maximo: %.4f V   -> %.0f decadas'
      %(dV[fin&(dV>0)].min(),np.nanmax(dV),np.log10(np.nanmax(dV)/dV[fin&(dV>0)].min())))
print()
print('  V0 barrido:',np.round(V0,3))
print('  fraccion de dV<=0 por V0:')
for k,v0 in enumerate(V0):
    col=dV[:,k]; f=np.isfinite(col)
    print('     %.3f V  ->  %5.1f %% se anula o invierte' % (v0,100*(col[f]<=0).mean()))
