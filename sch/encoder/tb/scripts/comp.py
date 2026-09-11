import numpy as np, subprocess, itertools
GE=np.load('esq_geos.npy')[:20]
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
VB=np.round(np.arange(0.90,2.01,0.05),3)
res={}
for cor,T in itertools.product(COR,TMP):
    L=['* compensacion por Vbias %s %dC'%(cor,T),
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.options temp=%d tnom=27'%T,
       'VDD Vdd 0 3.3','VSS Vss 0 0','VB Vb 0 1.2',
       'VIN Vin 0 1.58','VINN Vinn 0 1.72','VMEM Vmem 0 1.0']   # Vdif = -0.14 fijo
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(GE):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p]
    t='c_%s_%d'%(cor,T)
    L+=['.control','dc VB 0.90 2.00 0.05','wrdata %s.dat '%t+' '.join(vec),'.endc','.end']
    open(t+'.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',t+'.spice'],capture_output=True)
    A=np.loadtxt(t+'.dat')
    res['%s|%d'%(cor,T)]=np.abs(A[:,1::2]); res['vb']=A[:,0]
np.savez('comp.npz',geos=GE,**res)
vb=res['vb']; ref=res['typical|27']
j0=int(np.argmin(np.abs(vb-1.2)))
obj=ref[j0,:]                      # Iex nominal por geometria, a Vbias=1.2
print('objetivo: recuperar el Iex nominal de cada geometria ajustando SOLO Vbias')
print()
print('%-14s %14s %16s %14s'%('condicion','Vbias necesario','dispersion geom','error residual'))
for cor,T in itertools.product(COR,TMP):
    I=res['%s|%d'%(cor,T)]; need=[]
    for i in range(I.shape[1]):
        y=np.log(I[:,i]/obj[i])
        s=np.where(np.diff(np.sign(y)))[0]
        need.append(np.interp(0.0,y[s[0]:s[0]+2],vb[s[0]:s[0]+2]) if len(s) else np.nan)
    need=np.array(need); ok=np.isfinite(need)
    vfix=np.median(need[ok])
    jj=int(np.argmin(np.abs(vb-vfix)))
    resid=100*np.abs(I[jj,:]/obj-1)
    print('%-10s%4dC %10.3f V %13.0f mV %12.0f%% (peor %.0f%%)'
      %(cor,T,vfix,1000*np.std(need[ok]),np.median(resid),resid.max()))
