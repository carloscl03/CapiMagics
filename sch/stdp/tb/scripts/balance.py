"""Que geometria de M1 equilibra la regla?

Criterio, no opinion: en STDP aditivo con pre y post no correlacionados a tasa
`r`, la deriva media del peso va como  r^2 * (A+ tau+ - A- tau-).  Si no es
cero, los pesos se van al rail. Con tau+ = tau- la condicion queda A+ = A-.

Punto de trabajo medido de la celda:
    vb_idep = 2.32  ->  Vdep0 = 0.767 V
    vb_pot  = 1.30  ->  vpot cae 1213 mV, o sea Vtr = 1.213 V
"""
import numpy as np

VDEP0, VTR0 = 0.767, 1.213

D = np.load('/tmp/stdp/nucleo_w.npz')['filas']     # depresion, L4=0.28
P = np.load('/tmp/stdp/pot_denso.npz')['filas']    # potenciacion

def interp(A, w, l, x):
    m = (A[:,0]==w) & (A[:,1]==l) if l is not None else (A[:,0]==w)
    v, s = A[m,2], np.abs(A[m,4])
    o = np.argsort(v)
    return float(np.exp(np.interp(x, v[o], np.log(np.maximum(s[o],1e-12)))))

print('  A- (depresion, L4=0.28) en Vdep = %.3f V:' % VDEP0)
for w in sorted(set(D[:,0])):
    print('    W4=%.2f  ->  %8.2f mV' % (w, 1e3*interp(D, w, None, VDEP0)))

print('\n  A+ (potenciacion) en Vtr = %.3f V, y que A- iguala:' % VTR0)
print('  %6s %6s %12s %14s' % ('W1','L1','A+[mV]','W4 que iguala'))
W4 = sorted(set(D[:,0]))
AM = np.array([interp(D, w, None, VDEP0) for w in W4])
for l in sorted(set(P[:,1])):
    for w in sorted(set(P[:,0])):
        ap = interp(P, w, l, VTR0)
        if ap < AM.min() or ap > AM.max():
            q = '-- fuera de rango --'
        else:
            q = '%.3f um' % np.interp(np.log(ap), np.log(AM), W4)
        print('  %6.2f %6.2f %12.2f %14s' % (w, l, ap*1e3, q))
    print()
