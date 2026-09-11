import numpy as np, subprocess, itertools
GE=np.load('esq_geos.npy')[:20]
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=['typical','ff','ss','fs','sf']; TMP=[27]
IDEAL={'typical':1.200,'ff':1.065,'ss':1.344,'fs':1.108,'sf':1.294}
out={}
for cor,T in itertools.product(COR,TMP):
    L=['* autopolarizado real vs Vbias fijo vs Vbias ideal',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.options temp=%d tnom=27'%T,'VDD Vdd 0 3.3','VSS Vss 0 0',
       'VIN Vin 0 1.58','VINN Vinn 0 1.72','VMEM Vmem 0 1.0',
       'VFIJO Vfijo 0 1.2','VIDEAL Videal 0 %.3f'%IDEAL[cor],
       '* el divisor real M10/M11 que fija net1',
       'XM10 net1 net1 Vss Vss nfet_03v3 L=0.28u W=0.5u '+MO,
       'XM11 net1 net1 Vdd Vdd pfet_03v3 L=0.28u W=0.5u '+MO]
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(GE):
        for tag,nodo in [('a','net1'),('f','Vfijo'),('d','Videal')]:
            p='%s%d'%(tag,i)
            L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
                'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
                'XM9_%s %sa %s Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,nodo,l9,w9,MO),
                'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
                'VI_%s %so Vmem 0'%(p,p)]
            vec.append('i(vi_%s)'%p)
    L+=['.control','op','print '+' '.join(vec+['v(net1)']),'.endc','.end']
    open('au.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','au.spice'],capture_output=True,text=True)
    d={}
    for ln in r.stdout.splitlines():
        t=ln.strip()
        if '=' in t and (t.startswith('i(vi_') or t.startswith('v(net1)')):
            k=t.split('=')[0].strip(); d[k]=float(t.split('=')[1])
    out[cor]=d
ref=out['typical']
print('%-9s %8s %14s %14s %14s'%('esquina','net1','Vbias FIJO','autopolarizado','Vbias IDEAL'))
for cor in COR:
    d=out[cor]
    def dev(tag):
        v=[d['i(vi_%s%d)'%(tag,i)]/ref['i(vi_%s%d)'%(tag,i)] for i in range(len(GE)) if 'i(vi_%s%d)'%(tag,i) in d]
        return np.median(v)
    print('%-9s %7.3f V %11.2fx %13.2fx %13.2fx'%(cor,d['v(net1)'],dev('f'),dev('a'),dev('d')))
print()
print('(cada columna es el factor de Iex respecto a la esquina typical; 1.00x = sin deriva)')
