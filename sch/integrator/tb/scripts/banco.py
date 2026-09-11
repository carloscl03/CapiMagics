"""Banco del integrador para el barrido sobre la banda de la cadena.

Tres cosas que el banco anterior (val3.py) no tenia:

  AMPERIMETROS.  Una fuente de 0 V en serie en cada camino (VAMF en la fuga,
  VAMI en la inyeccion). Sirven de instrumento Y de test: en equilibrio la
  carga que entra por M6 tiene que igualar a la que sale por M2.

  VENTANA ATADA AL PERIODO.  Con ventana fija en microsegundos, a 74 kHz el
  balance fallaba un 35 % -- la ventana cogia a veces uno y a veces dos spikes.
  No era el circuito, era la medida.

  ARRANQUE EN EL EQUILIBRIO PREDICHO.  `.ic` sale de la ley de composicion, que
  acierta a 7 mV. Asentar por fuerza bruta desde 2.0 V costaba 60+ periodos y
  hacia el barrido inviable; desde la prediccion bastan unos pocos.
"""
import itertools, subprocess, os
from ancho_f import ancho_ns
import numpy as np

_D = np.load('leyes.npz'); CF, CI = _D['cf'], _D['ci']

def _base(Z, g, nv):
    cols = [np.ones(len(Z))]
    for e in itertools.product(range(g + 1), repeat=nv):
        if 0 < sum(e) <= g:
            t = np.ones(len(Z))
            for j, k in enumerate(e):
                if k:
                    t = t * Z[:, j] ** k
            cols.append(t)
    return np.column_stack(cols)

def fuga(vm, W1, L1, W2, L2, Iref):
    Z = np.column_stack([np.full_like(vm, np.log10(W1)), np.full_like(vm, np.log10(L1)),
                         np.full_like(vm, np.log10(W2)), np.full_like(vm, np.log10(L2)), vm])
    return Iref * 10 ** (_base(Z, 3, 5) @ CF)

def iny(vm, W6, L6, Cf_):
    Z = np.column_stack([np.full_like(vm, np.log10(W6)), np.full_like(vm, np.log10(L6)),
                         np.full_like(vm, np.log10(Cf_)), vm])
    return 10 ** (_base(Z, 5, 4) @ CI)

def equilibrio(g, f_kHz):
    W1, L1, W2, L2, Iref, W6, L6, Cf_ = g
    vv = np.linspace(1.0, 2.45, 900)
    r = iny(vv, W6, L6, Cf_) - fuga(vv, W1, L1, W2, L2, Iref) / (f_kHz * 1e3 * Cf_ * 1e-15)
    j = np.where(np.diff(np.sign(r)))[0]
    return np.nan if not len(j) else np.interp(
        0, [r[j[0]], r[j[0] + 1]], [vv[j[0]], vv[j[0] + 1]])

def _sub(p, g, f_kHz, vic):
    W1, L1, W2, L2, Ir, W6, L6, Cf = g
    T = 1e6 / f_kHz * 1e-9
    n = ['IREF%s avdd nref%s %gn' % (p, p, Ir * 1e9),
         'XM3%s nref%s nref%s avss avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, L2, W2),
         'VAMF%s nf%s avss 0' % (p, p),
         'XM2%s nf%s nref%s vg%s avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L2, W2),
         'XM1%s vg%s vg%s vm%s avdd pfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L1, W1),
         'VAMI%s ni%s avdd 0' % (p, p),
         'XM6%s vm%s Vext%s ni%s avss nfet_03v3 L=%gu W=%gu nf=1' % (p, p, p, p, L6, W6),
         'C3%s vm%s avss %gf' % (p, p, Cf),
         # ancho REAL del spike a esa frecuencia (medido: 32-39 ns), no 32 fijos.
         'VSPK%s Vext%s 0 PULSE(0 3.3 %.8gs 2n 2n %.8gn %.8gs)'
         % (p, p, T, ancho_ns(f_kHz), T),
         '.ic v(vm%s)=%.4f' % (p, vic)]
    return n, ['v(vm%s)' % p, 'i(vamf%s)' % p, 'i(vami%s)' % p]

def mide(casos, nset=6, nmed=8, tag='b', vic=None):
    """casos = [(geometria, f_kHz)]. TODOS deben compartir frecuencia."""
    f = casos[0][1]
    assert all(c[1] == f for c in casos), 'un lote, una frecuencia'
    T = 1e6 / f * 1e-9
    tfin = T * (1 + nset + nmed); vent = T * nmed
    tag = '%d_%s' % (os.getpid(), tag)   # PID: dos procesos no pueden pisarse
    sp, dat = 'bk_%s.spice' % tag, 'bk_%s.dat' % tag
    L = ['* banco integrador',
         '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
         '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
         'VDD avdd 0 3.3', 'VSS avss 0 0']
    vec = []
    for i, (g, _) in enumerate(casos):
        # arranque: el vm ya medido si lo hay, si no la ley de composicion
        v0 = vic[i] if vic is not None else equilibrio(g, f)
        if not np.isfinite(v0):
            v0 = 2.0
        vic_i = v0
        a, b = _sub('c%d' % i, g, f, vic_i)
        L += a; vec += b
    L += ['.control', 'tran 2n %.8g %.8g uic' % (tfin, tfin - vent),
          'wrdata %s %s' % (dat, ' '.join(vec)), '.endc', '.end']
    open(sp, 'w').write('\n'.join(L) + '\n')
    subprocess.run(['ngspice', '-b', sp], capture_output=True)
    A = np.loadtxt(dat); t = A[:, 0]
    out = []
    for i in range(len(casos)):
        vm = A[:, 1 + 6 * i]; ifg = A[:, 3 + 6 * i]; iny_ = A[:, 5 + 6 * i]
        # integral CON SIGNO. Con |i| el camino de inyeccion se infla: la
        # puerta de M6 mete desplazamiento en los dos sentidos por los
        # flancos de 2 ns, y el valor absoluto los suma en vez de dejarlos
        # cancelarse. Medido: 1.4-13.7 % de carga bidireccional en la
        # inyeccion y 0.0 % en la fuga, lo que producia un sesgo POSITIVO
        # del balance en 129 puntos de 129, sin una sola excepcion.
        qf = abs(np.trapezoid(ifg, t)); qi = abs(np.trapezoid(iny_, t))
        mit = t[0] + (t[-1] - t[0]) / 2
        a1 = t < mit
        out.append(dict(vm=vm.mean(), riz=1000 * (vm.max() - vm.min()),
                        deriva=1000 * (vm[~a1].mean() - vm[a1].mean()),
                        bal=100 * (qi / qf - 1) if qf > 0 else np.nan,
                        ifuga=1e9 * qf / (t[-1] - t[0]),
                        pred=equilibrio(casos[i][0], f)))
    os.remove(dat)
    return out

if __name__ == '__main__':
    MED = [('ORIGINAL', (1.0,0.28,1.0,0.28,50e-9,1.0,0.28,5111), {268:2.208, 1500:2.343}),
           ('mejorado 25n',(1.0,0.28,1.0,1.00,25e-9,0.25,1.0,5111), {268:1.794, 1500:2.004}),
           ('mejorado 12n',(1.0,0.28,1.0,1.00,12e-9,0.25,1.0,5111), {268:1.904, 1500:2.055})]
    print('=== validacion del banco contra transitorios ya medidos ===')
    print('  %-13s %7s %9s %9s %9s %8s %8s' %
          ('diseño','f[kHz]','banco','val3.py','ley','deriva','balance'))
    err = []
    for f in (268, 1500):
        lote = [(g, f) for _, g, _ in MED]
        rs = mide(lote, tag='v%d' % f)
        for (nom, g, med), r in zip(MED, rs):
            e = 1000 * (r['vm'] - med[f]); err.append(abs(e))
            print('  %-13s %7d %8.3fV %8.3fV %8.3fV %6.1fmV %7.2f%%' %
                  (nom, f, r['vm'], med[f], r['pred'], r['deriva'], r['bal']))
    print()
    print('  banco vs val3.py: medio %.1f mV, peor %.1f mV' % (np.mean(err), np.max(err)))
