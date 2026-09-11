import numpy as np, subprocess
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
NOMI=dict(Wd=0.725,Wl=0.947,Ll=0.394,L9=1.811)
LD,W9,WO,LO=1.60,0.26,0.93,1.86
CAJA=dict(Wd=(0.26,1.80),Wl=(0.30,2.70),Ll=(0.28,0.62),L9=(0.80,3.78))
def net(p,g):
    return ['XM1_%s %sx %sp %sa 0 nfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,LD,g['Wd'],MO),
      'XM2_%s %sy %sn %sa 0 nfet_03v3 L=%gu W=%gu %s'%(p,p,p,p,LD,g['Wd'],MO),
      'XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,g['Ll'],g['Wl'],MO),
      'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,g['Ll'],g['Wl'],MO),
      'XM9_%s %sa Vb 0 0 nfet_03v3 L=%gu W=%gu %s'%(p,p,g['L9'],W9,MO),
      'XM5_%s %so %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,LO,WO,MO),
      'VO%s %so 0 1.0'%(p,p)]
res={}
for var in ('Wd','Wl','Ll','L9'):
    lo,hi=CAJA[var]; vals=np.logspace(np.log10(lo),np.log10(hi),13)
    L=['* rodaja','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VB Vb 0 1.2']
    vec=[]
    for i,v in enumerate(vals):
        g=dict(NOMI); g[var]=v; p='%s%d'%(var.lower(),i)
        L+=['VP%s %sp 0 1.62'%(p,p),'VN%s %sn 0 1.76'%(p,p)]+net(p,g)
        vec.append('i(vo%s)'%p)
    L+=['.control','op','print '+' '.join(vec),'.endc','.end']
    open('rod.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','rod.spice'],capture_output=True,text=True)
    d={}
    for t in r.stdout.splitlines():
        t=t.strip()
        if '=' in t and t.split('=')[0].strip().startswith('i(vo'):
            try: d[t.split('=')[0].strip()]=abs(float(t.split('=')[1]))
            except: pass
    I=np.array([d.get('i(vo%s%d)'%(var.lower(),i),np.nan) for i in range(len(vals))])
    m=np.isfinite(I)&(I>0)
    if m.sum()<5:
        print('  %s: fallo (%d validos)'%(var,m.sum())); continue
    lx,ly=np.log10(vals[m]),np.log10(I[m])
    fila=[np.abs(np.polyval(np.polyfit(lx,ly,gr),lx)-ly).max() for gr in (1,2,3)]
    res[var]=(ly.max()-ly.min(),fila,m.sum())
print()
print('=== rodajas 1-D REALES: tres variables en el nominal, mueves una ===')
print('  13 puntos, todo el ancho de la caja. Error MAXIMO del ajuste, en decadas.')
print('  %-5s %6s %10s %10s %10s %10s'%('','pts','recorre','recta','parabola','cubica'))
for v,(rec,f,k) in res.items():
    print('  %-5s %6d %8.2f dec %9.4f %10.4f %10.4f'%(v,k,rec,*f))
