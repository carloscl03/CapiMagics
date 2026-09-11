"""Banco instrumentado de la celda STDP del equipo (gf180).

La celda se reescribe insertando AMPERIMETROS (fuentes de 0 V) en los seis
puntos de la cadena causal del paper:

    Idep -> Vdep0 -> decae con Itd -> Vdep(tpre) -> I_stdp -> DVw -> Iout

Medir solo el resultado final no distingue cual eslabon falla. Es la leccion
del integrador: las tres leyes validaban bien por separado y el modelo
compuesto fallaba 43 mV; sin puntos intermedios no se habria encontrado.

Ademas lleva dentro los tests de validez:
    balance en CW    : (Qpot - Qdep) = CW * DVw
    balance en Cdep  : (Qdep_in - Qtd) = Cdep * DVdep
Si no cierran, hay una corriente por donde no miro.
"""
import re
import subprocess

import numpy as np

MIM = open('mimfull.spice').read()
CRUDA = open('stdp_sch.spice').read()

# --- instrumentacion: se reescribe el subcircuito con las fuentes de 0 V ----
def instrumenta(txt):
    L = txt.splitlines()
    out, extra = [], []
    dentro = False
    for l in L:
        s = l.strip()
        if s.lower().startswith('.subckt stdp '):
            dentro = True
        if not dentro:
            out.append(l)
            continue
        # 1. Idep: M16 alimenta n5
        if s.startswith('M16 '):
            out.append(s.replace('M16 n5 ', 'M16 n5a '))
            extra.append('VAM_dep n5a n5 0')
        # 1b. la rama que de verdad carga Cdep: M12, entre n5 y vdep.
        #     El amperimetro de M16 mide la Idep TOTAL y el diodo M9 se lleva
        #     ~40 % de ella -> por eso el balance de carga no cerraba.
        elif s.startswith('M12 '):
            out.append(s.replace(' vdep avss ', ' vdpx avss '))
            extra.append('VAM_c vdpx vdep 0')
        # 1c. ESPEJO de VAM_c: la rama que de verdad descarga Cpot es M8,
        #     no MCM_1. MCM_1 lleva la `Ipot` TOTAL y el diodo M7 se lleva el
        #     resto -- mismo reparto que M9/M12 en la depresion.
        elif s.startswith('M8 '):
            out.append(s.replace(' vpot avdd', ' vptx avdd'))
            extra.append('VAM_cp vpot vptx 0')
        # 2. Itd: el ultimo de la pila de cinco, a avss
        elif s.startswith('MCM_9 '):
            out.append(s.replace(' avss avss ', ' n9x avss '))
            extra.append('VAM_td n9x avss 0')
        # 3. I_stdp depresion: entre vw y M3
        elif s.startswith('M3 '):
            out.append(s.replace('M3 vw ', 'M3 vwd '))
            extra.append('VAM_sd vw vwd 0')
        # 4. I_stdp potenciacion: entre M2 y vw
        elif s.startswith('M2 '):
            out.append(s.replace('M2 vw ', 'M2 vwp '))
            extra.append('VAM_sp vwp vw 0')
        # 5. Ipot: MCM_1 a avss
        elif s.startswith('MCM_1 '):
            out.append(s.replace(' avss avss ', ' n4x avss '))
            extra.append('VAM_pot n4x avss 0')
        # 6. Itp: M17 alimenta vpot
        elif s.startswith('M17 '):
            out.append(s.replace('M17 vpot ', 'M17 vpx '))
            extra.append('VAM_tp vpx vpot 0')
        elif s.startswith('.ends'):
            out += extra
            out.append(s)
            dentro = False
        else:
            out.append(l)
    return '\n'.join(out)

CEL = instrumenta(CRUDA)


def con_vdep_forzado(txt):
    """Variante para el barrido B: anade un puerto `vdepf` y una fuente
    controlada que impone `vdep`. Asi la ley I_stdp(Vdep) se mide DIRECTA,
    sin depender de si la traza llega a ese valor: separa el eslabon 3 de
    los eslabones 1 y 2.
    """
    out, dentro = [], False
    for l in txt.splitlines():
        t = l.strip()
        if t.lower().startswith('.subckt stdp '):
            dentro = True
            out.append(l.replace(' vw iout', ' vw iout vdepf'))
            continue
        if dentro and t.startswith('.ends'):
            out.append('EFD vdep avss vdepf avss 1')
            dentro = False
        out.append(l)
    return chr(10).join(out)


CEL_F = con_vdep_forzado(CEL)

AMPS = ['vam_dep', 'vam_c', 'vam_cp', 'vam_td', 'vam_sd', 'vam_sp', 'vam_pot', 'vam_tp']
# `vw` es un PUERTO del subcircuito: a nivel superior se llama `vw`, no
# `x1.vw`. El resto son nodos internos. Confundirlos hace que el `.ic` se
# ignore en silencio ("IC on non-existent node").
NODOS_INT = ['vdep', 'vpot', 'n1', 'n2', 'n3', 'n4', 'n5']
NODOS_TOP = ['vw']
NODOS = NODOS_INT + NODOS_TOP


def cabecera(vb):
    return ['* banco stdp instrumentado',
            '.include /foss/pdks/gf180mcuD/libs.tech/ngspice/design.ngspice',
            '.lib /foss/pdks/gf180mcuD/libs.tech/ngspice/sm141064.ngspice typical',
            MIM, CEL, 'VDD avdd 0 3.3', 'VSS avss 0 0',
            'VBITD vb_itd 0 %.4f' % vb['itd'],
            'VBPOT vb_pot 0 %.4f' % vb['pot'],
            'VBIDEP vb_idep 0 %.4f' % vb['idep'],
            'VBITP vb_itp 0 %.4f' % vb['itp']]


def corre(lineas, control, salida='bk.dat'):
    open('bk.spice', 'w').write('\n'.join(lineas + control) + '\n')
    r = subprocess.run(['ngspice', '-b', 'bk.spice'], capture_output=True, text=True)
    try:
        return np.loadtxt(salida), r
    except Exception:
        return None, r


def vectores(pref='x1.'):
    v = ['v(%s%s)' % (pref, n) for n in NODOS]
    i = ['i(v%s.%s)' % (pref.rstrip('.'), a) if False else 'i(%s%s)' % (pref, a) for a in AMPS]
    return v, i


def vec_i(inst='x1'):
    """Corrientes de los amperimetros. En ngspice el nombre jerarquico de una
    fuente dentro de X1 es `v.x1.<nombre>`, y su corriente `i(v.x1.<nombre>)`."""
    return ['i(v.%s.%s)' % (inst, a) for a in AMPS]


def vec_v(inst='x1'):
    """Tensiones. Los internos llevan el prefijo de la instancia; los puertos no."""
    return (['v(%s.%s)' % (inst, n) for n in NODOS_INT]
            + ['v(%s)' % n for n in NODOS_TOP])
