import json, numpy as np, subprocess
R=json.load(open('pareto2.json')); W=[r[0] for r in R]; geos=[r[1] for r in R]
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
def cuerpo(salida=True):
    L=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(geos):
        p='g%d'%i
        L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
            'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
            'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,MO)]
        if salida: L+=['XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),'VI_%s %so Vmem 0'%(p,p)]
    return L
CAB=['.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
     'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
     'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
LIB='.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical'
# --- nominal: comprobar que la especificacion sigue en pie ---
L=['* nominal']+CAB[:1]+[LIB]+CAB[1:]+cuerpo(True)
L+=['.control','dc VDIF -0.6 0.6 0.02','wrdata p2nom.dat '+' '.join('i(vi_g%d) v(g%dx)'%(i,i) for i in range(len(geos))),'.endc','.end']
open('p2nom.spice','w').write('\n'.join(L)+'\n'); subprocess.run(['ngspice','-b','p2nom.spice'],capture_output=True)
# --- montecarlo ---
N=300
L=['* mc']+CAB[:1]+['.param sw_stat_global=0 sw_stat_mismatch=1',LIB]+CAB[1:]+cuerpo(False)
L+=['.control','set appendwrite','let c=0','dowhile c < %d'%N,'  reset','  dc VDIF -0.12 0.12 0.008']
L+=['  let d%d = v(g%dx)-v(g%dy)'%(i,i,i) for i in range(len(geos))]
L+=['  wrdata p2mc.dat '+' '.join('d%d'%i for i in range(len(geos))),'  let c = c + 1','end','.endc','.end']
open('p2mc.spice','w').write('\n'.join(L)+'\n'); subprocess.run(['rm','-f','p2mc.dat'])
subprocess.run(['ngspice','-b','p2mc.spice'],capture_output=True)
A=np.loadtxt('p2nom.dat'); vd=A[:,0]
qa,qb,k0=[int(np.argmin(np.abs(vd-t))) for t in (-0.14,0.14,0)]
B=np.loadtxt('p2mc.dat'); P=31; B=B[:(len(B)//P)*P].reshape(-1,P,2*len(geos))
vm=B[0,:,0]; pred=[9.7,10.4,23.4,25.9,27.0]
print('%d corridas MC'%B.shape[0]); print()
print('%5s %7s %11s %11s %9s %28s'%('w','area','sigma pred','sigma MEDIDA','error','especificacion en ngspice'))
for i,q in enumerate(geos):
    ie=np.abs(A[:,1+2*(2*i)]); vx=A[:,1+2*(2*i+1)]
    G=float(np.abs(np.gradient(vx)/np.gradient(vd))[k0])
    off=[]
    for k in range(B.shape[0]):
        y=B[k,:,2*i+1]; j=np.where(np.diff(np.sign(y)))[0]
        if len(j):
            a,b=j[0],j[0]+2
            yy,xx=(y[a:b],vm[a:b]) if y[a+1]>y[a] else (y[a:b][::-1],vm[a:b][::-1])
            off.append(np.interp(0.0,yy,xx))
    s=np.std(off); ar=q[0]*q[1]+2*q[2]*q[3]+q[4]*q[5]
    print('%5.2f %6.2f %9.1f mV %9.1f mV %8.0f%%   %.1f/%.1f nA G=%.3f'
      %(W[i],ar,pred[i],1000*s,100*(1000*s/pred[i]-1),ie[qa]*1e9,ie[qb]*1e9,G))
