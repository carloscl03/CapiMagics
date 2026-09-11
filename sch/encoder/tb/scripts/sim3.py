import json
sal=json.load(open('spec_test3.json'))
mo="nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u' pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0"
WO,LO=0.93,1.86
L=['* validacion EncoderSpec v2 (modelo cubico, tolerancia estrecha)',
   '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD Vdd 0 3.3','VSS Vss 0 0','VDIF Vdif 0 0','VB Vb 0 1.2',
   'BP Vin 0 V = 1.65 + 0.5*V(Vdif)','BN Vinn 0 V = 1.65 - 0.5*V(Vdif)','VMEM Vmem 0 1.0']
vec=[]
for i,r in enumerate(sal):
    wd,ld,wl,ll,w9,l9=r[3:9]; p='v%d'%i
    L+=['XM3_%s %sx %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,mo),
        'XM4_%s %sy %sy Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,ll,wl,mo),
        'XM1_%s %sx Vin  %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,mo),
        'XM2_%s %sy Vinn %sa Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,p,ld,wd,mo),
        'XM9_%s %sa Vb Vss Vss nfet_03v3 L=%gu W=%gu %s'%(p,p,l9,w9,mo),
        'XM8_%s %so %sx Vdd Vdd pfet_03v3 L=%gu W=%gu %s'%(p,p,p,LO,WO,mo),
        'VI_%s %so Vmem 0'%(p,p)]
    vec+=['i(vi_%s)'%p,'v(%sx)'%p,'v(%sa)'%p]
L+=['.control','dc VDIF -0.4 0.4 0.01','wrdata spec3.dat '+' '.join(vec),'.endc','.end']
open('spec3.spice','w').write('\n'.join(L)+'\n')
