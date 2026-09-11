import numpy as np, subprocess, itertools
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
# varias relaciones pmos/nmos, para ver si alguna sigue al proceso como hace falta
VAR=[(0.5,0.28,0.5,0.28),(0.5,0.28,1.0,0.28),(1.0,0.28,0.5,0.28),
     (0.5,1.00,0.5,0.28),(0.5,0.28,0.5,1.00),(0.5,2.00,0.5,0.28)]
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
out={}
for cor,T in itertools.product(COR,TMP):
    L=['* bloque de bias en esquina','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.options temp=%d tnom=27'%T,'VDD Vdd 0 3.3','VSS Vss 0 0']
    for i,(wn,ln,wp,lp) in enumerate(VAR):
        L+=['XM10_b%d n%d n%d Vss Vss nfet_03v3 L=%gu W=%gu %s'%(i,i,i,ln,wn,MO),
            'XM11_b%d n%d n%d Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(i,i,i,lp,wp,MO)]
    L+=['.control','op','print '+' '.join('v(n%d)'%i for i in range(len(VAR))),'.endc','.end']
    open('b.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','b.spice'],capture_output=True,text=True)
    v=[]
    for ln_ in r.stdout.splitlines():
        for i in range(len(VAR)):
            if ln_.strip().startswith('v(n%d)'%i): v.append(float(ln_.split('=')[1]))
    out['%s|%d'%(cor,T)]=v
NEED={'typical|-40':1.203,'typical|27':1.200,'typical|125':1.200,'ff|-40':1.072,'ff|27':1.065,
 'ff|125':1.055,'ss|-40':1.341,'ss|27':1.344,'ss|125':1.359,'fs|-40':1.115,'fs|27':1.108,
 'fs|125':1.100,'sf|-40':1.295,'sf|27':1.294,'sf|125':1.304}
K=list(NEED); need=np.array([NEED[k] for k in K])
V=np.array([out[k] for k in K])
print('Vbias que PIDE el diferencial vs el que DA el bloque de bias')
print()
print('%-15s %8s %s'%('condicion','pide',' '.join('var%d'%i for i in range(len(VAR)))))
for j,k in enumerate(K):
    print('%-15s %7.3f  %s'%(k,need[j],' '.join('%5.3f'%x for x in V[j])))
print()
print('%-8s %10s %12s %14s'%('variante','Wn/Ln,Wp/Lp','recorrido','tras ajustar offset y escala'))
for i,(wn,ln,wp,lp) in enumerate(VAR):
    x=V[:,i]
    A=np.column_stack([np.ones(len(x)),x]); c=np.linalg.lstsq(A,need,rcond=None)[0]
    r=need-A@c
    print('  var%d   %.1f/%.2f %.1f/%.2f  %6.0f mV   residuo rms %5.1f mV  peor %5.1f mV  (ganancia %.2f)'
      %(i,wn,ln,wp,lp,1000*(x.max()-x.min()),1000*r.std(),1000*np.abs(r).max(),c[1]))
print()
print('  recorrido que hace falta seguir: %.0f mV'%(1000*(need.max()-need.min())))
