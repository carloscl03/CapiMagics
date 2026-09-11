"""Las ecuaciones del integrador, con coeficientes, tras el trabajo de hoy."""
import itertools
import numpy as np

S = []
def P(s=''): S.append(s)

def poli(c, exps, nom, ancho=74, sang='    '):
    ter = []
    for j, ex in enumerate(exps):
        t = ''.join(nom[k] + ('' if ex[k]==1 else '^%d'%ex[k]) for k in range(len(ex)) if ex[k])
        ter.append((c[j], t))
    ter.sort(key=lambda x: -abs(x[0]))
    ln = sang
    for v, t in ter:
        s = '%+.5f'%v + (('*'+t) if t else '')
        if len(ln)+len(s) > ancho:
            P(ln); ln = sang
        ln += s + ' '
    P(ln)

# --- 1. techo --------------------------------------------------------------
T = np.load('techo.npz'); TG, TE = T['geos'], T['techo']
ok = np.isfinite(TE); Z = np.log10(TG[ok])
B = np.column_stack([np.ones(ok.sum())] + [Z[:,k]**p for k in (0,1) for p in (1,2,3)])
ct = np.linalg.lstsq(B, TE[ok], rcond=None)[0]
err_t = 1000*np.abs(B@ct - TE[ok]).mean()
np.save('ct_techo.npy', ct)

P('## 1. El TECHO de la inyeccion')
P()
P('Tension a la que dV se anula: por encima no hay equilibrio y el integrador')
P('SATURA. Depende solo de W6 y L6; C no lo mueve nada (2.735 V para los tres')
P('condensadores). Con  u = lg10(W6),  w = lg10(L6):')
P()
P('```')
P('techo [V] = %+.5f %+.5f*u %+.5f*u^2 %+.5f*u^3' % (ct[0], ct[1], ct[2], ct[3]))
P('            %+.5f*w %+.5f*w^2 %+.5f*w^3' % (ct[4], ct[5], ct[6]))
P()
P('   7 coeficientes, error medio %.1f mV sobre 48 geometrias.' % err_t)
P('   L6=0.28 -> 2.73 V    L6=1.00 -> 2.35 V')
P('   L6=0.50 -> 2.42      L6=2.00 -> 2.33')
P('')
P('   CORRIGE al knowledge base, que tenia 2.323 y 1.953: aquellos estaban')
P('   topados por una malla de V0 que acababa en 2.45 V.')
P('```')
P()

# --- 2. inyeccion colapsada -------------------------------------------------
def techo_ley(W6, L6):
    z = [np.log10(W6), np.log10(L6)]
    return float(np.concatenate([[1.0]] + [[z[k]**p] for k in (0,1) for p in (1,2,3)]) @ ct)

J = np.load('iny3.npz'); C = J['casos']; V0 = J['V0']; DV = J['dV']
X, Y, GI = [], [], []
for i in range(len(C)):
    W6, L6, Cf = C[i]
    if not (0.25 <= W6 <= 2.0 and 0.28 <= L6 <= 2.0): continue
    tc = techo_ley(W6, L6)
    for k, v in enumerate(V0):
        d = DV[i,k]
        if np.isfinite(d) and d > 0.003 and v < tc-0.05:
            X.append([np.log10(W6), np.log10(L6), np.log10(Cf), np.log10(tc-v)])
            Y.append(np.log10(d)); GI.append(i)
X = np.array(X); Y = np.array(Y); GI = np.array(GI)
E = [e for e in itertools.product(range(4), repeat=4) if sum(e) <= 3]
Bi = np.column_stack([np.prod(X**np.array(e), axis=1) for e in E])
ci = np.linalg.lstsq(Bi, Y, rcond=None)[0]
np.save('ci_iny.npy', ci)

P('## 2. La INYECCION: lo que sube vm con cada spike')
P()
P('La variable no es `vm`, es la DISTANCIA AL TECHO. Con')
P('  a = lg10(W6), b = lg10(L6), c = lg10(C[fF]), s = lg10(techo - vm)')
P()
P('```')
P('lg10( dV [V] ) =')
poli(ci, E, ['a','b','c','s'])
P('')
P('   35 terminos.  LOO por geometria 4.03 %%, peor geometria 11.4 %%.')
P('   SUSTITUYE a la quintica de 126 terminos, que daba 4.86 %% de media')
P('   pero 43.7 %% en su peor geometria.')
P('```')
P()

P('## 3. La FUGA: lo que descarga el condensador entre spikes')
P()
P('```')
P('I_fuga = Iref * P3(lgW1, lgL1, lgW2, lgL2, vm)    56 terminos, en leyes.npz')
P('   Externo 2.08 %% sobre su propia malla (fuga_bar.npz).')
P('')
P('FORMA LEGIBLE (4.97 %%):   I_fuga/Iref = A + B*vm,  con A y B cuadraticas')
P('   en (lgW1, lgL1, lgW2, lgL2), 15 coeficientes cada una.')
P('')
P('AVISO: su barrido fija Iref=50 nA en la malla y solo lo mueve sobre UNA')
P('linea de geometria (12 puntos de 93). Iref esta casi confundido, y por eso')
P('la ley falla hasta 12 %% en L2=0.28 con Iref lejos de 50 nA. Discrepa un')
P('6.4 %% de la medida directa con amperimetro. PENDIENTE de rehacer con Iref')
P('cruzado -- el cribado ya esta (criba.npz, 1536 geometrias).')
P('```')
P()

P('## 4. El RIZADO: sin coeficientes')
P()
P('```')
P('rizado = I_fuga / (f * C)')
P('')
P('   Dispersion 1.12x sobre 344 puntos: mediana 1.002, p10 0.954, p90 1.069.')
P('   Con 7 coeficientes de correccion baja a 3.58 %%.')
P('   (La cubica directa de 84 coeficientes daba 14.38 %%.)')
P('')
P('   Correccion de ciclo de trabajo: q cae a 0.90 en 4500 kHz, donde el pulso')
P('   ocupa el 19 %% del periodo y la fuga tambien corre durante la inyeccion.')
P('```')
P()

P('## 5. La COMPOSICION: vm no se ajusta, se resuelve')
P()
P('```')
P('   dV(vm) = I_fuga(vm) / (f * C)   ->   resolver en vm')
P('')
P('   23.2 mV de error medio, CERO coeficientes nuevos.')
P('   (Una cubica de 84 coeficientes ajustada directamente da 38.8 mV.)')
P('   Peor a frecuencia baja: 56 mV a 74 kHz, 8 mV a 4500 -- por mal')
P('   condicionamiento del equilibrio, no porque la ley sea peor ahi.')
P('')
P('   sensibilidad = d(vm)/d(log10 f)      [mV/decada]')
P('   resolucion   = sensibilidad / rizado')
P('```')
P()

P('## 6. El ANCHO del spike (entrada, no parametro)')
P()
P('```')
P('   f[kHz]   26    76   203   501  1219  2743  4902')
P('   ancho    33    32    33    33    34    36    39   ns')
P('')
P('   Interpolacion lineal en log10(f). Amplitud al riel (3.300 V).')
P('   Su efecto sobre el rizado es <=2 %%: medido, no supuesto.')
P('```')
P()
P('## Cuenta de coeficientes')
P()
P('```')
P('   techo          7')
P('   inyeccion     35   (antes 126)')
P('   fuga          56   (pendiente de rehacer con Iref cruzado)')
P('   rizado         0   (+7 si se quiere la correccion)')
P('   ancho          7   (tabla)')
P('   ------------------')
P('   TOTAL        105   frente a 196 antes de hoy')
P('```')

open('ECUACIONES_INTEGRADOR.md','w',encoding='utf-8').write('\n'.join(S)+'\n')
print('\n'.join(S))
