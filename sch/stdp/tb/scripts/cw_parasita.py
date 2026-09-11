"""El 8 % sistematico: hay capacidad parasita fija en `vw`?

Si `vw` tiene una capacidad extra C0 que NO escala con el array, entonces
    DVw = Q / (nCW*Cu + C0)
y lo constante no es `senal*nCW` sino `senal*(nCW + C0/Cu)`.

Se ajusta ese unico numero por rejilla y se mira si el 8 % se cierra. Si se
cierra, la ley vale EXACTA para cualquier CW con una sola correccion; si no, la
capacidad no es el problema.
"""
import numpy as np

CU = 54.5e-15
for lado, vmax in (('dep', 1.15), ('pot', 9.9)):
    A = np.load('/tmp/stdp/L3_%s.npz' % lado)['filas']
    CW = np.array(sorted(set(A[:, 1])))
    best = None
    for x in np.linspace(0.0, 3.0, 601):
        disp = []
        for v in sorted(set(A[:, 0])):
            if lado == 'dep' and v > vmax:
                continue
            p = []
            for c in CW:
                m = (np.abs(A[:, 0] - v) < 1e-9) & (A[:, 1] == c)
                if m.sum() and abs(A[m, 4][0]) > 5e-5:
                    p.append(abs(A[m, 4][0]) * (c + x))
            if len(p) == len(CW):
                disp.append((max(p) - min(p)) / np.mean(p))
        if disp:
            s = float(np.mean(disp))
            if best is None or s < best[0]:
                best = (s, x)
    s0 = None
    for x in (0.0,):
        disp = []
        for v in sorted(set(A[:, 0])):
            if lado == 'dep' and v > vmax:
                continue
            p = [abs(A[(np.abs(A[:,0]-v)<1e-9)&(A[:,1]==c), 4][0])*(c+x)
                 for c in CW if abs(A[(np.abs(A[:,0]-v)<1e-9)&(A[:,1]==c), 4][0])>5e-5]
            if len(p) == len(CW):
                disp.append((max(p)-min(p))/np.mean(p))
        s0 = float(np.mean(disp))
    print('  %s:  C0 = %.3f unidades = %.1f fF   ->  dispersion %.2f %% -> %.2f %%'
          % (lado, best[1], best[1]*CU*1e15, 100*s0, 100*best[0]))
