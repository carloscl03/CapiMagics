import numpy as np, subprocess, itertools
GE=np.load('esq_geos.npy')[:20]
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=["typical","ff","ss","fs","sf"]; TMP=[-40,27,125]
out={}
for cor,T in itertools.product(COR,TMP):
    L=['* encoder polarizado por referencia con resistencia',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical',
       '.options temp=%d tnom=27'%T,'VDD Vdd 0 3.3','VSS Vss 0 0',
       'VIN Vin 0 1.58','VINN Vinn 0 1.72','VMEM Vmem 0 1.0',
       '* --- referencia con resistencia ---',
       'XMP1 n1 n2 Vdd Vdd pfet_03v3 L=2u W=1u '+MO,
       'XMP2 n2 n2 Vdd Vdd pfet_03v3 L=2u W=1u '+MO,
       'XMN1 n1 n1 Vss Vss nfet_03v3 L=1u W=0.5u '+MO,
       'XMN2 n2 n1 ns  Vss nfet_03v3 L=1u W=4u '+MO,
       'XR1 ns Vss Vss ppolyf_u_3k r_width=0.8u r_length=200u',
       'RSU Vdd n1 200MEG',
       '* --- divisor de diodos, para comparar ---',
       'XM10 nd nd Vss Vss nfet_03v3 L=0.28u W=0.5u '+MO,
       'XM11 nd nd Vdd Vdd pfet_03v3 L=0.28u W=0.5u '+MO,
       'VFIJO Vfijo 0 1.2']
    vec=[]
    for i,(wd,ld,wl,ll,w9,l9) in enumerate(GE):
        # M9 como espejo de XMN1 (misma L=1u, W escalada) para el caso 'referencia'
        for tag,nodo,W9,L9 in [('r','n1',0.5,1.0),('a','nd',w9,l9),('f','Vfijo',w9,l9)]:
            p='%s%d'%(tag,i)
            L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,MO),
                'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
                'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,MO),
                'XM9_%s %sa %s Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,nodo,L9,W9,MO),
                'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=1.86u W=0.93u %s'%(p,p,p,MO),
                'VI_%s %so Vmem 0'%(p,p)]
            vec.append('i(vi_%s)'%p)
    L+=['.control','op','print '+' '.join(vec+['v(n1)','v(nd)']),'.endc','.end']
    open('bm2.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','bm2.spice'],capture_output=True,text=True)
    d={}
    for ln in r.stdout.splitlines():
        t=ln.strip()
        if '=' in t and (t.startswith('i(vi_') or t.startswith('v(n')):
            try: d[t.split('=')[0].strip()]=float(t.split('=')[1])
            except: pass
    out["%s|%d"%(cor,T)]=d
CT=["%s|%d"%(c,t) for c,t in itertools.product(COR,TMP)]
ref=out["typical|27"]
print('deriva de Iex respecto a typical (1.00x = sin deriva), 27 C')
print()
print('%-13s %8s %8s %14s %14s %14s'%('condicion','V(n1)','V(nd)','Vbias FIJO','divisor M10/M11','REFERENCIA R'))
for cor in CT:
    d=out[cor]
    def dev(tag):
        v=[d['i(vi_%s%d)'%(tag,i)]/ref['i(vi_%s%d)'%(tag,i)] for i in range(len(GE)) if 'i(vi_%s%d)'%(tag,i) in d]
        return np.median(v) if v else float('nan')
    print('%-13s %7.3f %8.3f %11.2fx %13.2fx %13.2fx'%(cor,d.get('v(n1)',0),d.get('v(nd)',0),dev('f'),dev('a'),dev('r')))
print()
for nom,tag in [('Vbias fijo','f'),('divisor M10/M11','a'),('referencia con R','r')]:
    v=[]
    for cor in CT:
        d=out[cor]
        v.append(np.median([d['i(vi_%s%d)'%(tag,i)]/ref['i(vi_%s%d)'%(tag,i)] for i in range(len(GE)) if 'i(vi_%s%d)'%(tag,i) in d]))
    v=np.array(v); print('  %-18s deriva total %.2fx   (ff->ss %.2fx)'%(nom,v.max()/v.min(),v[1]/v[2]))
