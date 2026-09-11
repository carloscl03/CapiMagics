"""Si NO hay espejos, la variable de diseno es la TENSION de bias, no la
corriente. Entonces lo que importa no es solo que corriente da cada vb, sino
CUANTO SE MUEVE la corriente por cada mV -- porque un bias de tension desnudo
deriva con esquina y temperatura, y no hay espejo que lo sujete.

Los cuatro barridos ya tienen el dato: solo hay que leerlo al reves.
"""
import numpy as np

CU = 54.5e-15


def pendiente(vb, ii, nom, unidad='nA'):
    """e-plegado en mV de vb. En subumbral vale n*VT (~40-50 mV) y NO depende
    de la geometria: W/L escala la corriente, no la sensibilidad. Un valor
    mayor dice que el dispositivo esta en inversion moderada o fuerte, que es
    donde se puede disenar la robustez."""
    o = np.argsort(vb)
    v, i = vb[o], np.abs(ii[o])
    m = i > 0
    v, i = v[m], i[m]
    # ajuste log-lineal sobre el tramo completo
    k = np.polyfit(v, np.log(i), 1)[0]
    ef = 1000.0 / abs(k)                       # mV por e-plegado
    print('  %-6s  %7.4f - %7.4f V  ->  %8.4g - %8.4g %s   '
          'e-plegado %6.1f mV  =>  %5.2f %%/mV'
          % (nom, v.min(), v.max(), i.min() * 1e9, i.max() * 1e9, unidad,
             ef, 100 * (np.exp(1.0 / ef) - 1)))
    return ef


print('SENSIBILIDAD DE CADA FUENTE A SU TENSION DE BIAS')
print()
ef = {}
A = np.load('L1_dep.npz')['filas']
ef['idep'] = pendiente(A[:, 0], A[:, 3], 'Idep')
A = np.load('L1_pot.npz')['filas']
ef['pot'] = pendiente(A[:, 0], A[:, 3], 'Ipot')
A = np.load('L2_dep.npz')['filas']
ef['itd'] = pendiente(A[:, 0], A[:, 2], 'Itd')
A = np.load('L2_pot.npz')['filas']
ef['itp'] = pendiente(A[:, 0], A[:, 2], 'Itp')

print()
print('LO QUE ESO SIGNIFICA AGUAS ABAJO')
print()

# Idep -> Vdep0 -> DVw.  La cadena de dos exponenciales.
A = np.load('L1_dep.npz')['filas']
m = (np.abs(A[:, 1] - 33e-9) < 1e-12) & (A[:, 2] == 2)
ii, v0 = A[m, 3], A[m, 6]
o = np.argsort(ii)
ii, v0 = ii[o], v0[o]
u = (v0 > 0.6) & (v0 < 1.05)
mVdec = np.polyfit(np.log(ii[u]), v0[u], 1)[0] * 1000.0   # mV de Vdep0 por e-plegado de I
print('  Idep -> Vdep0 :  %.0f mV de traza por e-plegado de corriente'
      ' (region util 0.6-1.05 V)' % mVdec)

EFOLD_DVW = 73.9      # medido en L3: mV de traza por e-plegado de DVw
cadena = (1.0 / ef['idep']) * mVdec / EFOLD_DVW
print('  Vdep0 -> DVw  :  e-plegado cada %.1f mV de traza  (L3)' % EFOLD_DVW)
print()
print('  => 1 mV en vb_idep  =  %.1f %% en la TASA DE APRENDIZAJE'
      % (100 * (np.exp(cadena) - 1)))
print('     50 mV de deriva  =  factor %.1f' % np.exp(50 * cadena))
print()
s_itd = 1.0 / ef['itd']
print('  => 1 mV en vb_itd   =  %.1f %% en Itd  =  %.1f %% en la VENTANA tau-'
      % (100 * (np.exp(s_itd) - 1), 100 * (np.exp(s_itd) - 1)))
print('     10 mV de deriva  =  %.0f %% de cambio en tau-'
      % (100 * (np.exp(10 * s_itd) - 1)))
