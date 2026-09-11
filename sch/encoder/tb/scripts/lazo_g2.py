import numpy as np, subprocess, itertools
D=np.load('siete.npz'); G=D['geos']; R=D['res']
ok=(R[:,3]>0.15)&np.isfinite(R).all(1)&(R[:,0]>0)
X=np.log10(G[ok]); LO,HI=X.min(0),X.max(0)
def mk(g):
    E=[e for e in itertools.product(range(g+1),repeat=4) if sum(e)<=g]
    B=lambda Z: np.column_stack([np.prod(Z**np.array(e),axis=1) for e in E])
    co={k:np.linalg.lstsq(B(X),y,rcond=None)[0] for k,y in
        [('a',np.log10(R[ok,0])),('b',np.log10(R[ok,1])),('g',np.log10(R[ok,2])),('v',R[ok,3])]}
    return B,co,len(E)
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
def sim(geos,tag):
    L=['* '+tag,'.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
       'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
       'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
    vec=[]
    for i,(wd,wl,ll,l9) in enumerate(geos):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=1.60u W=%gu %s'%(p,p,p,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=0.26u %s'%(p,p,l9,MO),
            'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
            'VI_%s %so Vmem 0'%(p,p)]
        vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
    L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata %s.dat '%tag+' '.join(vec),'.endc','.end']
    open(tag+'.spice','w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice','-b',tag+'.spice'],capture_output=True)
    A=np.loadtxt(tag+'.dat'); vd=A[:,0]
    qa,qb,k0=[int(np.argmin(np.abs(vd-x))) for x in (-0.14,0.14,0)]
    return np.array([[np.abs(A[:,1+2*(3*i)])[qa],np.abs(A[:,1+2*(3*i)])[qb],
      float(np.abs(np.gradient(A[:,1+2*(3*i+1)])/np.gradient(vd))[k0]),A[:,1+2*(3*i+2)][k0]] for i in range(len(geos))])
rng=np.random.default_rng(404)
NG=10**rng.uniform(LO,HI,(25,4))
ped=sim(NG,'p2g'); okp=(ped[:,3]>0.15)&(ped[:,0]>0); ped=ped[okp]
print('%d pedidos alcanzables'%okp.sum())
for grado in (2,3):
    B,co,nt=mk(grado)
    POOL=rng.uniform(LO,HI,(150000,4)); BP=B(POOL)
    PA,PB,PG,PV=[BP@co[k] for k in ('a','b','g','v')]
    sol=[]
    for Ia,Ib,g_,_ in ped:
        c=(PA-np.log10(Ia))**2+(PB-np.log10(Ib))**2+(PG-np.log10(g_))**2+100*np.maximum(0,0.15-PV)**2
        x=POOL[np.argmin(c)].copy(); cb=c.min()
        for paso in (0.05,0.015,0.005,0.0015):
            for _ in range(25):
                Q=np.clip(x+rng.normal(0,paso,(1200,4)),LO,HI); BQ=B(Q)
                cc=((BQ@co['a']-np.log10(Ia))**2+(BQ@co['b']-np.log10(Ib))**2
                    +(BQ@co['g']-np.log10(g_))**2+100*np.maximum(0,0.15-BQ@co['v'])**2)
                j=int(np.argmin(cc))
                if cc[j]<cb: cb,x=cc[j],Q[j].copy()
        sol.append(x)
    got=sim(10**np.array(sol),'s2g%d'%grado)
    e=np.column_stack([100*(got[:,0]/ped[:,0]-1),100*(got[:,1]/ped[:,1]-1),100*(got[:,2]/ped[:,2]-1)])
    d=np.abs(e).max(1)
    print()
    print('=== LAZO CERRADO con grado %d (%d terminos) ==='%(grado,nt))
    for n_,j in [('Iex(-)',0),('Iex(+)',1),('ganancia',2)]:
        print('  %-9s |error| %5.2f%%  peor %6.2f%%'%(n_,np.abs(e[:,j]).mean(),np.abs(e[:,j]).max()))
    for t in (2,5,10): print('  dentro de +-%2d%%: %2d/%d'%(t,(d<t).sum(),len(d)))
