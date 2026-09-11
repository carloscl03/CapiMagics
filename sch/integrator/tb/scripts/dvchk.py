"""La ley de inyeccion, medida DIRECTAMENTE en las geometrias del motor.

El sesgo de vm es casi constante (-40 mV) y no correlaciona con nada. Como
dV ~ (techo-vm)^3.46, la pendiente logaritmica es ~7 por voltio: un 30 % de
error en dV da 40 mV en vm. Con la fuga seria 40x menos (acierta al 1.2 %).

Se mide dV de un spike aislado, con vm forzado por .ic, igual que se midio
iny3.npz -- pero en las geometrias que el solver elige.
"""
import json, subprocess, sys
import numpy as np
sys.path.insert(0, "/tmp/integ/pkg")
import banco

sol = json.load(open('pedidos.json'))

def dv_medido(W1, W2, L2, Iref, W6, L6, Cf, v0, an=33.0):
    L = ['*', '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0', 'IREF avdd nref %gn' % (Iref*1e9),
         'XM3 nref nref avss avss nfet_03v3 L=%gu W=%gu nf=1' % (L2, W2),
         'XM2 avss nref vg avss nfet_03v3 L=%gu W=%gu nf=1' % (L2, W2),
         'XM1 vg vg vm avdd pfet_03v3 L=%gu W=%gu nf=1' % (0.28, W1),
         'XM6 vm Vext avdd avss nfet_03v3 L=%gu W=%gu nf=1' % (L6, W6),
         'C3 vm avss %gf' % Cf,
         'VSPK Vext 0 PULSE(0 3.3 1u 2n 2n %gn 100u)' % an,
         '.ic v(vm)=%.5f' % v0, '.control', 'tran 0.2n 1.6u uic',
         'wrdata dv.dat v(vm)', '.endc', '.end']
    open('dv.spice', 'w').write('\n'.join(L)+'\n')
    subprocess.run(['ngspice', '-b', 'dv.spice'], capture_output=True)
    A = np.loadtxt('dv.dat'); t = A[:, 0]; vm = A[:, 1]
    a = vm[t < 0.99e-6][-1]
    b = vm[(t > 1.3e-6) & (t < 1.5e-6)].mean()
    return 1000*(b - a)

print('=== la ley de inyeccion en las geometrias del motor ===')
print('  %-11s %6s %6s %8s %9s %11s %11s %9s' %
      ('banda', 'W6', 'L6', 'C', 'vm', 'ley [mV]', 'medido [mV]', 'error'))
sys.stdout.flush()
er = []
vistos = set()
for s in sol:
    k = (s['W6'], s['L6'], s['C'], s['W1'], s['W2'], s['L2'])
    if k in vistos: continue
    vistos.add(k)
    for v0 in (s['vm_lo'], s['vm_hi']):
        ley = 1000*banco.iny(np.array([v0]), s['W6'], s['L6'], s['C'])[0]
        import integrator_design as I
        ley2 = 1000*I.inyeccion(v0, s['W6'], s['L6'], s['C'])
        med = dv_medido(s['W1'], s['W2'], s['L2'], s['Iref']*1e-9,
                        s['W6'], s['L6'], s['C'], v0)
        e = 100*(ley2/med - 1); er.append(e)
        print('  %-11s %6.2f %6.2f %8.0f %8.3fV %10.3f %10.3f %+8.1f%%'
              % ('%d-%d' % (s['f_lo'], s['f_hi']), s['W6'], s['L6'], s['C'],
                 v0, ley2, med, e))
        sys.stdout.flush()
print()
print('  error de la ley de inyeccion aqui: medio %+.1f%%, mediana %+.1f%%'
      % (np.mean(er), np.median(er)))
print('  (su LOO por geometria daba 4.03%%, peor geometria 11.4%%)')
