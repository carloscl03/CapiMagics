"""Caracterizacion completa de la celda STDP, con el metodo del encoder y el
integrador, y sobre el netlist ARREGLADO (n3 = n4).

El paper da la estructura, que es lo que abarata esto frente al encoder:

    tau = C * eta * VT / I

o sea que los 4 transistores de bias y sus 4 tensiones entran SOLO a traves de
las 4 corrientes -- colapso verificado al -1.7 % en el decaimiento. De corriente
a geometria ya tenemos la ley `I_ref` del encoder, asi que no se remide.

    7 grados de libertad:  Idep Itd Ipot Itp | Cdep Cpot CW

Las leyes, cada una medida AISLADA de las anteriores (forzando el nodo
intermedio donde hace falta), porque el integrador enseño que tres leyes buenas
por separado componen 43 mV de error si no se separan:

    L1  Vdep0(Idep, Dtp, Cdep)     satura: la limita Vpost-Vth, no la carga
    L2  pendiente(Itd, Cdep)       lineal, = Itd/Cdep
    L3  DVw(Vdep, CW)              exponencial (e-plegado 76 mV) + suelo
    L1p L2p L3p                    el juego espejo de la potenciacion

CONTROL: los dos spikes presentes con Dt >> tau. NO quitar el post -- eso quita
la traza Y la inyeccion de carga del propio post (+4.30 mV), que son dos cosas.
"""
import os
import re
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, '/tmp/stdp')
os.chdir('/tmp/stdp')
import stdp_banco as B

PID = os.getpid()
VW0 = 1.65
CU = 54.5e-15
NOM = dict(itd=0.60, pot=1.30, idep=2.32, itp=2.60)
PUERTOS = ('avdd avss nvpre nvpost vpre vpost vb_itd vb_idep vb_itp vb_pot '
           'vw iout')
DTP0 = 33e-9
T0 = 200e-9
T_INI = time.time()


# --- transformaciones del netlist, en orden -------------------------------
def corto_n3n4(txt):
    """EL ARREGLO, hecho como lo haria el equipo: RENOMBRAR el nodo, no meter
    una fuente de 0 V entre los dos.

    `n3` y `n4` son el mismo nodo. Asi M7 queda diodo-conectado (el camino de
    continua que le falta) y M8 cuelga del mismo nodo que la fuente, igual que
    M12 en el lado de depresion.

    Con `VN34 n3 n4 0` -- que fue mi primer intento -- la fuente de 0 V queda en
    bucle con el M7 diodo-conectado y el punto de operacion NO CONVERGE:
    `singular matrix`, `gmin stepping failed`, `source stepping failed`. El
    solver se rinde en vw = 0.25 V y ahi el `.ic` ya no manda. Renombrar no
    tiene ese problema, y ademas es el arreglo de verdad.
    """
    out, dentro = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp '):
            dentro = True
        elif dentro and t.startswith('.ends'):
            dentro = False
        elif dentro:
            l = re.sub(r'(?<![\w.])n3(?![\w.])', 'n4', l)
        out.append(l)
    return '\n'.join(out)


def caps(txt, ndep=None, ncw=None, npot=None):
    """Reescribe las cuentas de unitcap. Es lo unico dimensional que se toca:
    en gLayout son arrays, no obligan a rehacer transistores."""
    plan = {'x1': (ndep, 'vdep avss'), 'x2': (ncw, 'vw avss'),
            'x3': (npot, 'avdd vpot')}
    out, visto = [], set()
    for l in txt.splitlines():
        m = re.match(r'\s*(x[123])\[\d+\]\s', l)
        if m and plan[m.group(1)][0] is not None:
            g = m.group(1)
            if g not in visto:
                visto.add(g)
                n, nodos = plan[g]
                for k in range(n):
                    out.append('%s[%d] %s unitcap' % (g, k, nodos))
            continue
        out.append(l)
    return '\n'.join(out)


def forzado(txt, nodo):
    """Impone un nodo interno desde un puerto nuevo. Aisla el eslabon 3 de los
    eslabones 1 y 2: la ley DVw(Vdep) deja de heredar el error de la traza."""
    out, dentro = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp '):
            dentro = True
            out.append(l.replace(' vw iout', ' vw iout %sf' % nodo))
            continue
        if dentro and t.startswith('.ends'):
            out.append('EF%s %s avss %sf avss 1' % (nodo, nodo, nodo))
            dentro = False
        out.append(l)
    return '\n'.join(out)



# `n3` desaparece con el arreglo (renombrado a `n4`), asi que la lista de
# vectores NO puede ser la de `stdp_banco`: wrdata fallaria con "no such
# vector x1.n3" y devolveria menos columnas de las que el lector espera.
NODOS_INT = ['vdep', 'vpot', 'n1', 'n2', 'n4', 'n5']
NODOS = NODOS_INT + ['vw']


def vec_v():
    return (['v(x1.%s)' % n for n in NODOS_INT] + ['v(vw)'])


def vec_i():
    return ['i(v.x1.%s)' % a for a in B.AMPS]


BASE = corto_n3n4(B.CEL)


# --- motor ------------------------------------------------------------------
def corre(cuerpo, ctl, cel, extra='', paso='0.2n'):
    sp, dat = 'cs_%d.spice' % PID, 'cs_%d.dat' % PID
    cab = ['* caracterizacion stdp',
           '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
           '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
           # varios nodos internos solo tocan puertas -> matriz singular.
           # 1e12 ohm sobre 272 fF son 272 s: invisible en 500 ns.
           '.option rshunt=1e12',
           B.MIM, cel, 'X1 %s%s stdp' % (PUERTOS, extra),
           'VDD avdd 0 3.3', 'VSS avss 0 0',
           # `iout` FLOTANTE (drenador de M5 y nada mas) da matriz
           # singular. Se ata a una carga realista: la entrada del
           # integrador de la neurona siguiente.
           'VIO iout 0 0.9']
    txt = '\n'.join(cab + cuerpo + ctl).replace('SALIDA', dat) + '\n'
    # GUARDA. Los nodos de spike son `vpre`/`vpost`, no `pre`/`post`. Escribir
    # `pulso('pre', ..)` deja el nodo SIN EXCITAR: no hay spike, la medida sale
    # plana, y ngspice solo dice `singular matrix: check node vpre`. Costo hoy
    # cuatro hipotesis equivocadas antes de mirar el netlist generado.
    for nd in ('vpre', 'vpost', 'nvpre', 'nvpost'):
        if not re.search(r'^V\w+ ' + nd + ' ', txt, re.M):
            raise AssertionError('nodo sin excitar: ' + nd)
    open(sp, 'w').write(txt)
    r = subprocess.run(['/foss/tools/bin/ngspice', '-b', sp],
                       capture_output=True, text=True)
    try:
        A = np.loadtxt(dat)
    except Exception:
        return None
    nv = len(NODOS)
    return dict(t=A[:, 0],
                V={n: A[:, 1 + 2 * k] for k, n in enumerate(NODOS)},
                I={a: A[:, 1 + 2 * (nv + k)] for k, a in enumerate(B.AMPS)})


def bias(**kw):
    v = dict(NOM); v.update(kw)
    return ['VBITD vb_itd 0 %.4f' % v['itd'], 'VBPOT vb_pot 0 %.4f' % v['pot'],
            'VBIDEP vb_idep 0 %.4f' % v['idep'], 'VBITP vb_itp 0 %.4f' % v['itp']]


def pulso(nom, ninv, t, w):
    return ['V%s %s 0 PULSE(0 3.3 %.6g 1n 1n %.6g 1)' % (nom.upper(), nom, t, w),
            'VN%s %s 0 PULSE(3.3 0 %.6g 1n 1n %.6g 1)' % (nom.upper(), ninv, t, w)]


def quieto(nom, ninv):
    return ['V%s %s 0 0' % (nom.upper(), nom), 'VN%s %s 0 3.3' % (nom.upper(), ninv)]


def tran(tf, paso='0.2n', forzado=None):
    """`.ic` SOLO sobre nodos que no estan impuestos por una fuente. Si se
    mete `v(x1.vdep)=0` cuando `vdep` lo impone la EFvdep, ngspice descarta la
    linea ENTERA -- incluida la parte de `vw` -- y solo avisa. El peso arranca
    entonces en su punto de operacion flotante (0.249 V) y la medida se recorta
    contra el cero."""
    ic = '.ic v(vw)=%.4f' % VW0
    if forzado != 'vdep':
        ic += ' v(x1.vdep)=0'
    return [ic, '.control', 'tran %s %.6g' % (paso, tf),
            'wrdata SALIDA %s' % ' '.join(vec_v() + vec_i()),
            '.endc', '.end']


def arranco_bien(d):
    """El banco SE NIEGA a medir un punto que no arranco donde debia. Un aviso
    del simulador se pierde entre el ruido; una fila que falta, no."""
    return d is not None and abs(float(d['V']['vw'][0]) - VW0) < 2e-3


def q(i, t, a, b):
    m = (t >= a) & (t <= b)
    return float(np.trapezoid(i[m], t[m]))


def reloj():
    return '[%5.1f min]' % ((time.time() - T_INI) / 60.0)


# --- L1 / L1p : amplitud de la traza ---------------------------------------
def L1(lado):
    dep = lado == 'dep'
    VB = ([2.10, 2.18, 2.25, 2.32, 2.38, 2.44, 2.48, 2.52] if dep else
          [1.45, 1.38, 1.30, 1.22, 1.15, 1.08, 1.00, 0.92])
    DTP = [20e-9, 33e-9, 50e-9, 100e-9, 200e-9]
    NC = [1, 2, 4, 8]
    # `amp_q` es la rama que carga el condensador; `amp_i` la del
    # regimen permanente. NO son la misma: leer la corriente del
    # amperimetro del interruptor da 5 fA, porque antes del spike
    # esa rama no lleva nada.
    nodo, amp_q, amp_i, clave = (
        ('vdep', 'vam_c', 'vam_dep', 'idep') if dep
        else ('vpot', 'vam_cp', 'vam_pot', 'pot'))
    filas = []
    print('\n=== L1%s: amplitud de la traza  (%s) ===' % ('' if dep else 'p', nodo),
          flush=True)
    print('  %6s %8s %5s %11s %10s %10s %8s'
          % ('vb', 'Dtp[ns]', 'nC', 'I[nA]', 'Q/C[V]', 'V0[V]', 'bal[%]'), flush=True)
    for nc in NC:
        cel = caps(BASE, ndep=nc) if dep else caps(BASE, npot=nc)
        C = nc * CU
        for vb in VB:
            for dtp in DTP:
                cuerpo = bias(**{clave: vb})
                cuerpo += (pulso('vpost', 'nvpost', T0, dtp) + quieto('vpre', 'nvpre')
                           if dep else
                           pulso('vpre', 'nvpre', T0, dtp) + quieto('vpost', 'nvpost'))
                d = corre(cuerpo, tran(T0 + dtp + 300e-9), cel)
                if not arranco_bien(d):
                    print('  %6.2f %8.1f %5d   RECHAZADO' % (vb, dtp * 1e9, nc),
                          flush=True)
                    continue
                t, v = d['t'], d['V'][nodo]
                qq = q(d['I'][amp_q], t, T0 - 5e-9, T0 + dtp + 20e-9)
                ii = float(np.median(np.abs(d['I'][amp_i][t < T0 - 10e-9])))
                v0 = float(v.max() - v[0]) if dep else float(v[0] - v.min())
                pred = abs(qq) / C
                bal = 100 * (pred - v0) / v0 if v0 > 1e-4 else float('nan')
                filas.append((vb, dtp, nc, ii, qq, pred, v0))
                print('  %6.2f %8.1f %5d %11.2f %10.4f %10.4f %8.1f'
                      % (vb, dtp * 1e9, nc, ii * 1e9, pred, v0, bal), flush=True)
                np.savez('L1_%s.npz' % lado, filas=np.array(filas, float))
    print('%s L1%s: %d puntos' % (reloj(), '' if dep else 'p', len(filas)), flush=True)


# --- L2 / L2p : pendiente del decaimiento ----------------------------------
def L2(lado):
    dep = lado == 'dep'
    VB = ([0.50, 0.55, 0.60, 0.66, 0.72] if dep else
          [2.70, 2.64, 2.58, 2.52, 2.46])
    NC = [1, 2, 4]
    nodo, amp, clave = ('vdep', 'vam_td', 'itd') if dep else ('vpot', 'vam_tp', 'itp')
    filas = []
    print('\n=== L2%s: pendiente del decaimiento  (%s) ==='
          % ('' if dep else 'p', nodo), flush=True)
    print('  %6s %5s %11s %14s %14s %8s'
          % ('vb', 'nC', 'I[nA]', 'medida[V/s]', 'I/C[V/s]', 'err[%]'), flush=True)
    for nc in NC:
        cel = caps(BASE, ndep=nc) if dep else caps(BASE, npot=nc)
        C = nc * CU
        for vb in VB:
            cuerpo = bias(**{clave: vb})
            cuerpo += (pulso('vpost', 'nvpost', T0, DTP0) + quieto('vpre', 'nvpre')
                       if dep else
                       pulso('vpre', 'nvpre', T0, DTP0) + quieto('vpost', 'nvpost'))
            d = corre(cuerpo, tran(4.2e-6, paso='1n'), cel)
            if not arranco_bien(d):
                print('  %6.2f %5d   RECHAZADO' % (vb, nc), flush=True)
                continue
            t, v = d['t'], d['V'][nodo]
            m = (t > 1.0e-6) & (t < 4.0e-6)
            pend = float(np.polyfit(t[m], v[m], 1)[0])
            ii = float(np.median(np.abs(d['I'][amp][m])))
            esp = -ii / C if dep else ii / C
            err = 100 * (pend - esp) / abs(esp) if abs(esp) > 1 else float('nan')
            filas.append((vb, nc, ii, pend, esp))
            print('  %6.2f %5d %11.4f %14.4g %14.4g %8.1f'
                  % (vb, nc, ii * 1e9, pend, esp, err), flush=True)
            np.savez('L2_%s.npz' % lado, filas=np.array(filas, float))
    print('%s L2%s: %d puntos' % (reloj(), '' if dep else 'p', len(filas)), flush=True)


# --- L3 / L3p : el nucleo, con el nodo FORZADO -----------------------------
def L3(lado):
    dep = lado == 'dep'
    VV = (np.arange(0.0, 1.45, 0.10) if dep else np.arange(3.3, 1.85, -0.10))
    NCW = [5, 10, 20, 40]
    nodo = 'vdep' if dep else 'vpot'
    filas = []
    print('\n=== L3%s: nucleo DVw(%s)  [%s FORZADO] ==='
          % ('' if dep else 'p', nodo, nodo), flush=True)
    print('  %8s %5s %12s %12s %12s'
          % (nodo, 'nCW', 'Ipico[nA]', 'DVw[mV]', 'senal[mV]'), flush=True)
    for ncw in NCW:
        cel = forzado(caps(BASE, ncw=ncw), nodo)
        suelo = None
        for vv in VV:
            cuerpo = bias() + ['VF%s %sf 0 %.4f' % (nodo, nodo, vv)]
            cuerpo += (pulso('vpre', 'nvpre', T0, DTP0) + quieto('vpost', 'nvpost')
                       if dep else
                       pulso('vpost', 'nvpost', T0, DTP0) + quieto('vpre', 'nvpre'))
            d = corre(cuerpo, tran(T0 + DTP0 + 300e-9, forzado=nodo), cel,
                      extra=' %sf' % nodo)
            if not arranco_bien(d):
                print('  %8.2f %5d   RECHAZADO  vw(0) = %s'
                      % (vv, ncw, 'sin datos' if d is None
                         else '%.4f' % d['V']['vw'][0]), flush=True)
                continue
            amp = 'vam_sd' if dep else 'vam_sp'
            t = d['t']
            ip = float(np.abs(d['I'][amp][(t > T0) & (t < T0 + DTP0)]).max())
            dvw = float(d['V']['vw'][-1] - 1.65)
            if suelo is None:
                suelo = dvw          # el primer punto es el de traza nula
            filas.append((vv, ncw, ip, dvw, dvw - suelo))
            print('  %8.2f %5d %12.4f %12.4f %12.4f'
                  % (vv, ncw, ip * 1e9, dvw * 1e3, (dvw - suelo) * 1e3), flush=True)
            np.savez('L3_%s.npz' % lado, filas=np.array(filas, float))
    print('%s L3%s: %d puntos' % (reloj(), '' if dep else 'p', len(filas)), flush=True)


if __name__ == '__main__':
    print('caracterizacion STDP sobre netlist ARREGLADO (n3 = n4)', flush=True)
    for f, a in ((L3, 'dep'), (L3, 'pot'), (L1, 'dep'), (L1, 'pot'),
                 (L2, 'dep'), (L2, 'pot')):
        try:
            f(a)
        except Exception as e:
            print('!! %s(%s) reventó: %r' % (f.__name__, a, e), flush=True)
    print('\n%s LISTO' % reloj(), flush=True)
