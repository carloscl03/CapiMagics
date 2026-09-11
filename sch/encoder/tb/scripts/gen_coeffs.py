"""Genera coeffs.py del paquete encoder_design a partir de los barridos."""
import numpy as np, itertools, datetime
LD, W9 = 1.60, 0.26
CAJA = [(0.260,1.796),(0.300,2.699),(0.280,0.620),(0.801,3.781)]
EXP = [e for e in itertools.product(range(4),repeat=4) if sum(e)<=3]
# Punto de referencia del desarrollo. Las leyes se escriben alrededor de el como
# POTENCIA x CORRECCION, que es exacto y se lee. Es un punto FIJO, no el nominal
# que deriva el solver: si ese se mueve, las leyes siguen siendo exactas.
REF = (0.725, 0.947, 0.394, 1.811)
X0 = np.log10(np.array(REF))
IDX_POT = [EXP.index(tuple(1 if i==j else 0 for i in range(4))) for j in range(4)]
IDX_CTE = EXP.index((0,0,0,0))
IDX_COR = [k for k,e in enumerate(EXP) if sum(e)>=2]

D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok])
def B(Z): return np.column_stack([np.prod(Z**np.array(e),axis=1) for e in EXP])
BB=B(X-X0)     # CENTRADA en REF
rng=np.random.default_rng(3); ii=rng.permutation(ok.sum()); n=int(.7*ok.sum()); tr,te=ii[:n],ii[n:]
LEY={}; ERR={}
for nom,y,es_log in [('IEX_MIN',np.log10(R[ok,0]),True),('GAIN',np.log10(R[ok,2]),True),('VA',R[ok,3],False)]:
    c=np.linalg.lstsq(BB[tr],y[tr],rcond=None)[0]
    r=BB[te]@c-y[te]
    ERR[nom]=(100*np.abs(10**r-1)).mean() if es_log else (100*np.abs(r/y[te])).mean()
    LEY[nom]=np.linalg.lstsq(BB,y,rcond=None)[0]

CV=np.load('viabilidad7.npy')
a,b,g=np.log10(R[ok,0]),np.log10(R[ok,1]),np.log10(R[ok,2])
def P(x,y): return np.column_stack([np.ones(np.size(x)),x,y,x*x,y*y,x*y])
ERR['VIAB']=(100*np.abs(10**(P(a,g)@CV-(b-a))-1)).mean()

M=np.load('mcley7.npz'); mo=M['n']>180
Xs=np.log10(M['geos'][mo]); ys=np.log10(M['sig'][mo])
Bs=np.column_stack([np.ones(mo.sum()),Xs])
r2=np.random.default_rng(2); jj=r2.permutation(mo.sum()); m=int(.7*mo.sum())
cs_t=np.linalg.lstsq(Bs[jj[:m]],ys[jj[:m]],rcond=None)[0]
ERR['SIGMA']=(100*np.abs(10**(Bs[jj[m:]]@cs_t-ys[jj[m:]])-1)).mean()
CS=np.linalg.lstsq(Bs,ys,rcond=None)[0]


# --- impedancia de salida del espejo (ro_fijo.npz) ---------------------------
# CORRECCION 2026-09-03: antes salia de `rox.npz`, donde Wo, Lo y la corriente
# estaban ACOPLADOS -- la geometria fijaba la corriente. Evaluar eso en el
# espejo fijo a corriente arbitraria era extrapolar, y daba 3.5e-17 ohm a 20 nA.
# Ahora es el espejo REAL (WO, LO) con fuente de corriente independiente, asi
# que la ley es de UNA variable: lg10(Iex).
Dr=np.load('ro_fijo.npz')
ur=np.log10(Dr['iex']); yr=np.log10(Dr['ro'])
mr=np.isfinite(ur)&np.isfinite(yr)&(Dr['ro']>0)
CR=np.polyfit(ur[mr],yr[mr],3)
ERR['RO']=(100*np.abs(10**(np.polyval(CR,ur[mr])-yr[mr])-1)).mean()


# --- corriente del divisor de bias (iref2.npz) ------------------------------
# Caja PROPIA y mucho mas ancha: el punto recomendado (Ln=10, Lp=20) quedaba
# fuera del primer barrido, que llegaba a Ln <= 3, Lp <= 4.
Di=np.load('iref2.npz'); Ci=Di['geos']; Ii=Di['I']; oki=Di['ok']
Xi=np.log10(Ci[oki]); yi=np.log10(Ii[oki])
Bi=np.column_stack([np.prod(Xi**np.array(e),axis=1) for e in EXP])
r4=np.random.default_rng(7); i4=r4.permutation(oki.sum()); n4=int(.7*oki.sum())
ci_t=np.linalg.lstsq(Bi[i4[:n4]],yi[i4[:n4]],rcond=None)[0]
ERR['IREF']=(100*np.abs(10**(Bi[i4[n4:]]@ci_t-yi[i4[n4:]])-1)).mean()
CI=np.linalg.lstsq(Bi,yi,rcond=None)[0]
CAJA_BIAS=tuple((Ci[:,k].min(),Ci[:,k].max()) for k in range(4))


# --- capacidad de entrada (cin.dat / cin_geos.npy) --------------------------
Gc=np.load('cin_geos.npy'); Ac=np.loadtxt('cin.dat')
Cc=np.abs(Ac[1::2]) if Ac.ndim==1 else np.abs(Ac[0,1::2])
okc=(Cc>1e-16)&np.isfinite(Cc)
Xc=np.log10(Gc[okc]); yc=np.log10(Cc[okc])
Bc=np.column_stack([np.ones(okc.sum()),Xc])
r4=np.random.default_rng(5); i4=r4.permutation(okc.sum()); n4=int(.7*okc.sum())
cc_t=np.linalg.lstsq(Bc[i4[:n4]],yc[i4[:n4]],rcond=None)[0]
ERR['CIN']=(100*np.abs(10**(Bc[i4[n4:]]@cc_t-yc[i4[n4:]])-1)).mean()
CC=np.linalg.lstsq(Bc,yc,rcond=None)[0]

E=np.load('esquinas7.npz'); GE=E['geos']
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
RR={'%s|%d'%(c,t):E['%s|%d'%(c,t)] for c,t in itertools.product(COR,TMP)}
v=np.ones(len(GE),bool)
for k in RR: v &= (RR[k][:,3]>0.15)&np.isfinite(RR[k]).all(1)&(RR[k][:,0]>0)
ref=RR['typical|27'][v]; ESQ={}; ERRE=0.0
for c,t in itertools.product(COR,TMP):
    k='%s|%d'%(c,t); Rk=RR[k][v]
    fi=float(np.median(Rk[:,0]/ref[:,0])); fg=float(np.median(Rk[:,2]/ref[:,2]))
    ESQ[(c,t)]=(fi,fg)
    ERRE=max(ERRE,(100*np.abs((Rk[:,0]/ref[:,0])/fi-1)).mean())

def fmt(v,n=8): return '(' + ', '.join('%.*g'%(n,x) for x in v) + ')'
L=['"""Coeficientes medidos del encoder de CapiMagics (GF180MCU).',
   '',
   'GENERADO por sch/encoder/tb/scripts/gen_coeffs.py -- no editar a mano.',
   'Procedencia y método: sch/encoder/results/encoder_knowledge_base.md',
   '',
   'Barridos: siete.npz (800 geometrías, leyes directas y viabilidad),',
   'mcley7.npz (150 x 200 tiradas Monte Carlo, desviación),',
   'esquinas7.npz (400 geometrías x 5 esquinas x 3 temperaturas),',
   'ro_fijo.npz (el espejo real con fuente independiente),',
   'iref2.npz (900 divisores de bias, 3.24 décadas).',
   '',
   'Error externo medido (validación 70/30, fuera de muestra):',
   '    Iex(-)      %.2f %%'%ERR['IEX_MIN'],
   '    ganancia    %.2f %%'%ERR['GAIN'],
   '    V(a)        %.2f %%'%ERR['VA'],
   '    viabilidad  %.2f %%'%ERR['VIAB'],
   '    sigma_Vos   %.1f %%'%ERR['SIGMA'],
   '    ro salida   %.2f %%'%ERR['RO'],
   '    I_ref       %.2f %%'%ERR['IREF'],
   '    esquinas    %.1f %% (peor caso del factor único; la deriva real es 5x)'%ERRE,
   '"""','',
   '# --- dimensiones fijas de la celda ---------------------------------------',
   'LD = %.3f   # um, largo del par de entrada M1/M2'%LD,
   'W9 = %.3f   # um, ancho de la cola M9'%W9,'',
   '# --- caja de validez (Wd, Wl, Ll, L9) en um -------------------------------',
   'CAJA = (' + ', '.join('(%.3f, %.3f)'%c for c in CAJA) + ')',
   'VBIAS_NOMINAL = 1.2   # V',
   'VDIF_MIN, VDIF_MAX = -0.14, 0.14   # V, donde se miden Iex(-) e Iex(+)','',
   '# --- punto de referencia del desarrollo -----------------------------------',
   '# Las tres leyes principales se escriben POTENCIA x CORRECCION alrededor de',
   '# este punto. Es una reescritura EXACTA (discrepancia 1e-14), elegida para',
   '# que se lean: la constante es el valor aquí y los exponentes son los de la',
   '# ley de potencia local. REF es FIJO; no es el nominal que deriva el solver.',
   'REF = (%.3f, %.3f, %.3f, %.3f)   # Wd, Wl, Ll, L9 en um'%REF,'',
   '# --- base polinómica: exponentes de lg10(v/REF) ---------------------------',
   '# cúbica completa en 4 variables = 35 términos. Los 4 de grado 1 salen',
   '# aparte (son los exponentes) y la constante también; quedan 30 de',
   '# corrección, que son los términos de grado 2 y 3.',
   'EXPONENTES = (']
L+= ['    '+', '.join('(%d, %d, %d, %d)'%e for e in EXP[i:i+5])+',' for i in range(0,len(EXP),5)]
L+= [')','',
   '# índices de EXPONENTES que son corrección (grado >= 2)',
   'CORRECCION = ('+', '.join(str(k) for k in IDX_COR)+',)','']
for nom,com,uni in [('IEX_MIN','Iex a Vdif = -0.14 V','A'),
                    ('GAIN','dV(x)/dVdif en el centro',''),
                    ('VA','tensión del nodo a (cola)','V')]:
    c=LEY[nom]
    cte=c[IDX_CTE]; pot=[c[k] for k in IDX_POT]
    L+=['# %s.  En REF: %s'%(com, ('%.4g %s'%(10**cte,uni)) if nom!='VA' else '%.4g V'%cte)]
    if nom!='VA':
        L+=['#   %s = %s_0 * (Wd/%.3f)^%+.5f (Wl/%.3f)^%+.5f'%(nom,nom,REF[0],pot[0],REF[1],pot[1]),
            '#              * (Ll/%.3f)^%+.5f (L9/%.3f)^%+.5f * 10^correccion'%(REF[2],pot[2],REF[3],pot[3])]
    else:
        L+=['#   VA = VA_0 + VA_EXP . lg10(v/REF) + correccion   (sin logaritmo)']
    L+=['%s_0 = %.8g'%(nom,(10**cte) if nom!='VA' else cte),
        '%s_EXP = (%s)'%(nom,', '.join('%.8g'%x for x in pot)),
        '%s_COR = ('%nom]
    cc=[c[k] for k in IDX_COR]
    L+=['    '+', '.join('%.8g'%x for x in cc[i:i+4])+',' for i in range(0,len(cc),4)]
    L+=[')','']
L+=['# --- ley de viabilidad ----------------------------------------------------',
    '# lg10(Iex(+)/Iex(-)) = VIABILIDAD . (1, lgIa, lgG, lgIa^2, lgG^2, lgIa*lgG)',
    'VIABILIDAD = '+fmt(CV),'',
    '# --- desviación de entrada ------------------------------------------------',
    '# lg10(sigma_Vos [V]) = SIGMA_VOS . (1, lgWd, lgWl, lgLl, lgL9)',
    'SIGMA_VOS = '+fmt(CS),'',
    '# --- espejo de salida y su impedancia -------------------------------------',
    'WO, LO = 0.93, 1.86   # um, el espejo M5-M8 (fijo en esta celda)',
    '# lg10(ro [ohm]) = polinomio de grado 3 en u = lg10(Iex [A]), ESPEJO FIJO.',
    '# Medido con Wo/Lo fijos y la corriente controlada aparte (ro_fijo.npz).',
    'RO_SALIDA = '+fmt(CR),'',
    '# --- corriente del divisor de bias M10/M11 --------------------------------',
    '# lg10(I_ref [A]) = I_REF . base EXPONENTES de (lgWn, lgLn, lgWp, lgLp)',
    'I_REF = '+fmt(CI),'',
    '# Caja PROPIA del divisor, distinta de la de la etapa diferencial.',
    'CAJA_BIAS = (' + ', '.join('(%.2f, %.2f)'%c for c in CAJA_BIAS) + ')','',
    '# --- capacidad de entrada -------------------------------------------------',
    '# lg10(C_in [F]) = C_IN . (1, lgWd, lgWl, lgLl, lgL9)',
    'C_IN = '+fmt(CC),'',
    '# --- esquinas: factor sobre (Iex, ganancia) respecto de typical/27C -------',
    'ESQUINAS = {']
for (c,t),(fi,fg) in ESQ.items():
    L.append('    (%-9s %4d): (%.4f, %.4f),'%('"%s",'%c,t,fi,fg))
L+=['}','']
open('coeffs.py','w').write('\n'.join(L)+'\n')
print('coeffs.py: %d lineas'%len(L))
for k,val in ERR.items(): print('   %-10s %.2f%%'%(k,val))
print('   %-10s %.1f%% (factor unico por condicion)'%('esquinas',ERRE))
