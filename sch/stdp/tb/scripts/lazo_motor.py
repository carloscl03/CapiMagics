"""Igual que lazo2 pero aplicando TAMBIEN las capacidades al netlist.

`construye()` solo tocaba W y L. Con nCW distinto el motor predecia una cosa y
se simulaba otra: +46.5 % y -99.5 % de "error" que no era del motor sino del
banco. Es justo lo que el lazo cerrado existe para cazar.
"""
import re, sys
sys.path.insert(0, '/tmp/stdp'); sys.path.insert(0, '/tmp/motor')
import carac_stdp as K
import lazo_motor as LM
from stdp_design import StdpSpec, design

def construye(p):
    cel = LM.construye(p)
    cel = K.caps(cel, ndep=int(p['nCdep']), ncw=int(p['nCW']))
    return cel

print('  %6s %6s %5s %8s %11s %11s %8s %8s'
      % ('asim','W1 ped','nCW','W4 sale','A- ley','A- medido','err[%]','A+ err'))
for asim, w1, ncw in [(1.0,None,10), (0.7,None,10), (1.0,0.55,10),
                      (1.0,None,5), (1.0,None,20), (1.0,None,40)]:
    d = design(StdpSpec(tau_us=5.5, asimetria=asim, W1=w1, nCW=ncw,
                        f_min_kHz=12.8, f_max_kHz=4500))
    if not d.ok:
        print('  %6.2f %6s %5d   %s' % (asim, w1 or '-', ncw,
              d.errors[0].message[:46])); continue
    p = d.params
    cel = construye(p)
    am = LM.mide(cel, 0.767, 'vdep', p['itd_nA'])
    ap = LM.mide(cel, 1.213, 'vpot', p['itp_nA'])
    lm = d.predicted['A- por evento [mV]']*1e-3
    lp = d.predicted['A+ por evento [mV]']*1e-3
    if am is None or ap is None:
        print('  %6.2f %6s %5d   RECHAZADO' % (asim, w1 or '-', ncw)); continue
    print('  %6.2f %6s %5d %8.3f %11.2f %11.2f %8.1f %8.1f'
          % (asim, ('%.2f'%w1) if w1 else '-', ncw, p['W4'],
             lm*1e3, am*1e3, 100*(am-lm)/abs(lm), 100*(ap-lp)/abs(lp)))
