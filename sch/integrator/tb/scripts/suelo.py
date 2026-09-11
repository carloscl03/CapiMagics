import numpy as np, subprocess
# fuga a corrientes bajas, con el espejo alargado (L2=1u) que ya sabemos que conviene
IR=[0.5,1,2,3,5,8,12,18,25,40]
L=['* suelo de corriente del integrador','.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
   '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
   'VDD avdd 0 3.3','VSS avss 0 0','VM vm 0 1.0']
vec=[]
for i,ir in enumerate(IR):
    p='q%d'%i
    L+=['I%s avdd %sref %gn'%(p,p,ir),
        'XM3_%s %sref %sref avss avss nfet_03v3 L=1.0u W=1u nf=1'%(p,p,p),
        'XM2_%s avss %sref %svg avss nfet_03v3 L=1.0u W=1u nf=1'%(p,p,p),
        'XM1_%s %svg %svg %ss avdd pfet_03v3 L=0.28u W=1u nf=1'%(p,p,p,p),
        'VAM%s vm %ss 0'%(p,p)]
    vec.append('i(vam%s)'%p)
L+=['.control','dc VM 0.05 3.3 0.025','wrdata sf.dat '+' '.join(vec),'.endc','.end']
open('sf.spice','w').write('\n'.join(L)+'\n')
subprocess.run(['ngspice','-b','sf.spice'],capture_output=True)
A=np.loadtxt('sf.dat'); v=A[:,0]; I=np.abs(A[:,1::2])
np.savez('suelo.npz',v=v,I=I,IR=np.array(IR))
J=np.load('iny_bar.npz'); ci=J['casos']; V0=J['V0']; dV=J['dV']
b=np.where((ci[:,0]==0.25)&(ci[:,1]==1.0)&(ci[:,2]==5111))[0][0]
frs=np.array([268,400,800,1500])
print('=== el integrador con el espejo ya alargado (L2=1u), W6=0.25/1.0, C=5111 fF ===')
print('%9s %10s %10s %11s %9s %9s'%('Iref [nA]','vm@268','vm@1500','mV/decada','rizado','RESOL'))
for k,ir in enumerate(IR):
    f_=lambda x: np.interp(x,v,I[:,k]); d_=lambda x: np.interp(x,V0,dV[b])
    vv=np.linspace(0.9,2.55,1200); out=[]
    for fr in frs:
        r=d_(vv)-f_(vv)/(fr*1e3*5111e-15)
        j=np.where(np.diff(np.sign(r)))[0]
        out.append(np.interp(0,[r[j[0]],r[j[0]+1]],[vv[j[0]],vv[j[0]+1]]) if len(j) else np.nan)
    out=np.array(out)
    if not np.isfinite(out).all(): print('%9.1f %10s'%(ir,'satura arriba')); continue
    s=1000*(out[-1]-out[0])/np.log10(frs[-1]/frs[0]); rz=1000*max(d_(x) for x in out)
    print('%9.1f %10.3f %10.3f %11.0f %8.0f %9.1f'%(ir,out[0],out[-1],s,rz,s/max(rz,1e-9)))
