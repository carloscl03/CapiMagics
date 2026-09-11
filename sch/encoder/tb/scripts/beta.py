import numpy as np, subprocess, itertools
MO="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
COR=['typical','ff','ss','fs','sf']; TMP=[-40,27,125]
RL=200.0   # longitud de la resistencia en um
K=8        # relacion de anchuras del par nmos
res={}
for cor,T in itertools.product(COR,TMP):
    L=['* referencia autopolarizada con resistencia (beta-multiplier subumbral)',
       '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice '+cor,
       '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice res_typical',
       '.options temp=%d tnom=27'%T,'VDD Vdd 0 3.3','VSS Vss 0 0',
       '* espejo pmos: MP2 en diodo fija la puerta comun',
       'XMP1 n1 n2 Vdd Vdd pfet_03v3 L=2u W=1u '+MO,
       'XMP2 n2 n2 Vdd Vdd pfet_03v3 L=2u W=1u '+MO,
       '* par nmos: MN1 en diodo, MN2 %d veces mas ancho con resistencia en fuente'%K,
       'XMN1 n1 n1 Vss Vss nfet_03v3 L=1u W=0.5u '+MO,
       'XMN2 n2 n1 ns  Vss nfet_03v3 L=1u W=%gu %s'%(0.5*K,MO),
       'XR1 ns Vss Vss ppolyf_u_3k r_width=0.8u r_length=%gu'%RL,
       '* arranque: inyeccion debil para sacar al lazo del estado de corriente nula',
       'RSU Vdd n1 200MEG',
       '* medidor de la corriente de la rama',
       'VAM Vdd nsup 0',
       '.control','op','print v(n1) v(n2) v(ns) i(vam) @xmn1[id]','.endc','.end']
    open('bm.spice','w').write('\n'.join(L)+'\n')
    r=subprocess.run(['ngspice','-b','bm.spice'],capture_output=True,text=True)
    d={}
    for ln in r.stdout.splitlines():
        t=ln.strip()
        if '=' in t and t.split('=')[0].strip() in ('v(n1)','v(n2)','v(ns)','@xmn1[id]'):
            try: d[t.split('=')[0].strip()]=float(t.split('=')[1])
            except: pass
    res['%s|%d'%(cor,T)]=d
    if not d: print(cor,T,'sin datos:',[l for l in r.stdout.splitlines() if 'rror' in l or 'ingular' in l][:2])
print('%-9s %5s %10s %12s'%('esquina','T','V(n1)','I rama'))
for cor,T in itertools.product(COR,TMP):
    d=res['%s|%d'%(cor,T)]
    if d: print('%-9s %4dC %9.3f V %9.1f nA'%(cor,T,d.get('v(n1)',float('nan')),-1e9*d.get('@xmn1[id]',float('nan'))))
np.save('beta_res.npy',res,allow_pickle=True)
