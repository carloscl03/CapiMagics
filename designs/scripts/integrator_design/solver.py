"""El motor: de una banda de frecuencias a las dimensiones del integrador.

Busqueda sobre la rejilla de geometrias medidas, con refinamiento local. El
espacio es pequeño (7 variables, y la fuga y la inyeccion casi no interactuan)
asi que no hace falta nada mas sofisticado.

Politica al liberar dimensiones fijadas, por orden de coste deducido de las
leyes -- el mismo criterio que en el encoder:

    W1   apenas interviene (quitarlo entero cuesta 0.07 puntos de error)
    W2   solo mueve el nivel de la fuga
    Iref desplaza la ventana en frecuencia sin cambiar su anchura
    L2   moldea la pendiente de la fuga con vm
    C    manda en el rizado y se paga en area
    W6   la palanca de resolucion medida (0.25 da 4.93 contra 2.24 de 1.0)
    L6   manda en el TECHO, o sea en la anchura de banda
"""
from __future__ import annotations

import itertools
from math import log10

from . import coeffs as C
from . import laws as L
from .spec import IntegratorDesign, IntegratorSpec, Severity

__all__ = ["design", "nominal", "NOMINAL_SPEC"]

# Rejilla de busqueda: los valores MEDIDOS, no una malla inventada.
_W1 = (0.5, 1.0, 2.0, 4.0)
_W2 = (0.5, 1.0, 2.0, 4.0)
_L2 = (0.28, 0.5, 1.0, 2.0, 4.0, 10.0)
_IR = (5e-9, 12e-9, 25e-9, 50e-9, 100e-9)
_W6 = (0.26, 0.5, 1.0, 2.0)   # 0.26 y no 0.25: el barrido de la inyeccion llega a 0.2555
_L6 = (0.28, 0.5, 1.0, 2.0)
_C = (2000.0, 5111.0, 12000.0)

# El nominal se DERIVA, no se clava: si cambian las leyes, se mueve con ellas.
# DEFAULT derivado de la CADENA. Antes decia 150-2400 kHz, puesto a ojo.
# Lo que de verdad le llega: la capa 2 alimentada por 4 sinapsis de 252 nA
# recorre 12.8-2586 kHz con la celda v3. El suelo es donde la neurona empieza a
# disparar (5 nA) y el techo los 1009 nA que suman las cuatro sinapsis.
NOMINAL_SPEC = {"f_min": 12.8, "f_max": 2586.0, "tradeoff": 0.5}

_ORDEN = ("W1", "W2", "Iref", "L2", "C", "W6", "L6")


def _area(g):
    """Area [um2] aproximada. El condensador domina: ~1 fF por um2 en MIM."""
    W1, W2, L2, Iref, W6, L6, Cf = g
    return W1 * C.L1_FIJO + 2 * W2 * L2 + W6 * L6 + Cf


def _evalua(g, f_lo, f_hi):
    """(resolucion, sensibilidad, rizado peor, f de saturacion) o None."""
    W1, W2, L2, Iref, W6, L6, Cf = g
    r = L.resolucion(W1, W2, L2, Iref, W6, L6, Cf, f_lo, f_hi)
    if r is None:
        return None
    s = L.sensibilidad(W1, W2, L2, Iref, W6, L6, Cf, f_lo, f_hi)
    v = L.vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_lo)
    rz = 1000.0 * L.rizado(v, W1, W2, L2, Iref, Cf, f_lo)
    return r, s, rz, L.f_satura(W1, W2, L2, Iref, W6, L6, Cf)


_EJES = ((0, _W1), (1, _W2), (2, _L2), (3, _IR), (4, _W6), (5, _L6), (6, _C))
MAX_BORDES = 2


def _bordes(g):
    """Cuantos ejes de la geometria estan en un extremo de la rejilla."""
    n = 0
    for k, vals in _EJES:
        if g[k] <= min(vals) * 1.001 or g[k] >= max(vals) * 0.999:
            n += 1
    return n


def _merito(g, f_lo, f_hi, tradeoff, area_max, t_max=None):
    """Lo que se maximiza. `tradeoff` reparte entre resolucion y holgura.

    Con un FRENO EN LOS BORDES (`MAX_BORDES`), el mismo que hizo falta en el
    encoder. Sin el, el motor elegia a la vez `Iref` minimo, `C` maximo y `L6`
    maximo en los ocho pedidos de prueba. Eso es malo por dos motivos
    independientes:

      * las leyes son peores en los bordes de su caja, y el lazo cerrado lo
        pagaba: 100 mV de sesgo en vm y -13 % en rizado
      * esas geometrias tienen `tau = C*vm/I_fuga` de milisegundos (12000 fF
        con 5 nA da 4.6 ms), asi que validarlas por transitorio es inviable:
        el asentamiento pide mil veces mas tiempo que el periodo

    BARATO A PROPOSITO. `f_satura` cuesta 50 bisecciones y cada una resuelve el
    equilibrio con 40 mas: 2000 evaluaciones por geometria, y la rejilla tiene
    11520. Aqui la holgura se mide por el MARGEN AL TECHO en f_max, que sale de
    un solo equilibrio; la frecuencia de saturacion se calcula despues, solo
    para la ganadora.
    """
    if _bordes(g) > MAX_BORDES:
        return None      # ver MAX_BORDES: el solver se iba a las esquinas
    W1, W2, L2, Iref, W6, L6, Cf = g
    v_hi = L.vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_hi)
    if v_hi is None:
        return None                        # satura dentro de la banda pedida
    v_lo = L.vm_equilibrio(W1, W2, L2, Iref, W6, L6, Cf, f_lo)
    if v_lo is None or v_hi <= v_lo:
        return None
    sens = 1000.0 * (v_hi - v_lo) / log10(f_hi / f_lo)
    rz = 1000.0 * L.rizado(v_lo, W1, W2, L2, Iref, Cf, f_lo)
    if rz <= 0:
        return None
    r = sens / rz
    tau = L.t_respuesta(v_lo, W1, W2, L2, Iref, Cf)
    if t_max and tau > t_max:
        return None
    margen = L.techo(W6, L6) - v_hi        # V de holgura antes de saturar
    m = tradeoff * log10(max(r, 1e-6)) + (1.0 - tradeoff) * 2.0 * margen
    if area_max and _area(g) > area_max:
        m -= 3.0 * log10(_area(g) / area_max)
    return m


def _busca(f_lo, f_hi, tradeoff, fijas, area_max, t_max=None, w1_todos=False):
    """Rejilla sobre lo no fijado.

    `W1` se deja fuera de la pasada gruesa y se refina al final: la competencia
    de familias midio que quitarlo entero cuesta 0.07 puntos de error (9.59 %
    contra 9.66 %). Barrerlo en la rejilla cuadruplica el coste para nada.
    """
    ejes = []
    for nm, vals in (("W1", _W1 if w1_todos else (1.0,)), ("W2", _W2),
                     ("L2", _L2), ("Iref", _IR),
                     ("W6", _W6), ("L6", _L6), ("C", _C)):
        ejes.append((fijas[nm],) if nm in fijas else vals)
    mejor, gbest = None, None
    for W1, W2, L2, Iref, W6, L6, Cf in itertools.product(*ejes):
        g = (W1, W2, L2, Iref, W6, L6, Cf)
        m = _merito(g, f_lo, f_hi, tradeoff, area_max, t_max)
        if m is not None and (mejor is None or m > mejor):
            mejor, gbest = m, g
    return gbest, mejor


def design(spec: IntegratorSpec) -> IntegratorDesign:
    """De una banda a las dimensiones. Nunca lanza excepcion."""
    d = IntegratorDesign()

    if not spec.has_objectives:
        d.add(Severity.INFO, "objetivos",
              "sin banda: se devuelve el punto nominal",
              chain=f"derivado de NOMINAL_SPEC={NOMINAL_SPEC}, no clavado a "
                    f"mano: si cambian las leyes, el nominal se mueve con ellas")
        return design(IntegratorSpec(**NOMINAL_SPEC))

    f_lo, f_hi = float(spec.f_min), float(spec.f_max)
    if f_hi <= f_lo:
        d.add(Severity.ERROR, "banda", f"f_max ({f_hi:.0f}) <= f_min ({f_lo:.0f})")
        return d

    # la banda tiene que caber en lo que la CADENA produce
    b0, b1 = C.BANDA_CADENA
    if f_lo < b0 or f_hi > b1:
        d.add(Severity.WARNING, "banda",
              f"pediste {f_lo:.0f}-{f_hi:.0f} kHz pero la cadena solo produce "
              f"{b0:.0f}-{b1:.0f}",
              chain="el suelo lo pone el pedido mas bajo que EncoderSpec "
                    "resuelve (15 nA) y el techo el reset del LIF (F_MAX), no "
                    "el integrador. Fuera de ahi no hay nada que leer")

    fijas = dict(spec.fixed_dims)
    if "Iref" in fijas and fijas["Iref"] > 1e-6:
        fijas["Iref"] *= 1e-9              # lo dieron en nA

    g, m = _busca(f_lo, f_hi, spec.tradeoff, fijas, spec.area_max, spec.t_respuesta_max)

    # refinar W1 alrededor de la ganadora
    if g is not None and "W1" not in fijas:
        mej, gb = m, g
        for w1 in _W1:
            gg = (w1,) + g[1:]
            mm = _merito(gg, f_lo, f_hi, spec.tradeoff, spec.area_max, spec.t_respuesta_max)
            if mm is not None and mm > mej:
                mej, gb = mm, gg
        g, m = gb, mej

    # si no hay solucion, liberar por orden de coste
    liberadas = []
    while g is None and fijas:
        for nm in _ORDEN:
            if nm in fijas:
                del fijas[nm]; liberadas.append(nm); break
        g, m = _busca(f_lo, f_hi, spec.tradeoff, fijas, spec.area_max, spec.t_respuesta_max)
    if liberadas:
        d.add(Severity.WARNING, "dimensiones",
              "liberadas " + ", ".join(liberadas) + " para alcanzar la banda",
              chain="politica del equipo: los objetivos mandan sobre las "
                    "dimensiones fijadas. Se libera por orden de coste deducido "
                    "de las leyes, y se para al encontrar solucion")

    if g is None:
        d.add(Severity.ERROR, "banda",
              f"no hay geometria que cubra {f_lo:.0f}-{f_hi:.0f} kHz sin saturar",
              chain="el techo de la inyeccion (1.92-2.73 V segun L6) limita la "
                    "frecuencia maxima legible. Banda mas estrecha, o L6 mas "
                    "corto a costa de mas rizado")
        return d

    W1, W2, L2, Iref, W6, L6, Cf = g
    r, s, rz, fsat = _evalua(g, f_lo, f_hi)
    d.params = {"W1": W1, "W2": W2, "L2": L2, "Iref": Iref*1e9,
                "W6": W6, "L6": L6, "C": Cf}

    v_lo = L.vm_equilibrio(*g, f_lo)
    v_hi = L.vm_equilibrio(*g, f_hi)
    d.predicted = {
        "vm [V]": f"{v_lo:.3f} a {v_hi:.3f}",
        "sensibilidad [mV/dec]": round(s, 1),
        "rizado peor [mV]": round(rz, 2),
        "RESOLUCION": round(r, 2),
        "techo [V]": round(L.techo(W6, L6), 3),
        "satura en [kHz]": round(fsat, 0),
        "area [um2]": round(_area(g), 0),
        "t_respuesta [us]": round(L.t_respuesta(v_lo, W1, W2, L2, Iref, Cf), 0),
        "L1 [um]": C.L1_FIJO,
    }
    ci = L.c_in(W6, L6)
    ro = L.r_out(v_lo, W1, W2, L2, Iref)
    d.predicted["C_in [fF]"] = round(ci, 3)
    d.predicted["R_out [GOhm]"] = round(ro/1e9, 2)
    d.requirements = {
        "C_in para NeuronSpec": f"{ci:.3f} fF -- la neurona mueve ~300 fF, "
                                f"asi que no es restriccion, pero pasalo como "
                                f"c_load a NeuronSpec en vez de suponerlo",
        "BUFER de salida": f"R_out = {ro/1e9:.2f} GOhm: vm NO puede mover nada. "
                           f"Hace falta un bufer, y su consumo (comparable a los "
                           f"{Iref*1e9:.0f} nA de Iref) puede comerse el ahorro",
        "ancho del spike [ns]": f"{L.ancho_ns(f_lo):.0f} a {L.ancho_ns(f_hi):.0f} "
                                f"-- lo fija la NEURONA, no este bloque",
        "Iref": f"{Iref*1e9:.0f} nA; desplaza la ventana en frecuencia sin "
                f"cambiar su anchura (analogo del Vbias del encoder)",
        "holgura al techo": (f"{log10(fsat/f_hi):.2f} decadas sobre f_max"
                             if fsat > f_hi else "ninguna"),
    }

    if not L.en_caja_fuga(W1, W2, L2, Iref):
        d.add(Severity.WARNING, "caja", "la fuga queda fuera de donde se midio")
    if not L.en_caja_iny(W6, L6, Cf):
        d.add(Severity.WARNING, "caja", "la inyeccion queda fuera de donde se midio")

    if spec.resolucion_min and r < spec.resolucion_min:
        d.add(Severity.ERROR, "resolucion",
              f"la mejor geometria da {r:.2f} y pediste {spec.resolucion_min:.2f}",
              chain="resolucion = sensibilidad / rizado peor. Subir C o bajar "
                    "Iref reducen el rizado; L6 largo tambien, pero BAJA el "
                    "techo y estrecha la banda")

    if 0 < fsat < 1.3 * f_hi:
        d.add(Severity.INFO, "saturacion",
              f"satura en {fsat:.0f} kHz, solo un {100*(fsat/f_hi-1):.0f} % "
              f"por encima de f_max",
              chain="por encima del techo vm se queda clavado y deja de leer. "
                    "Es un dato del contrato hacia arriba, no algo que deba "
                    "descubrirse en silicio")

    d.add(Severity.INFO, "spike",
          "las leyes suponen el spike del LIF: 32-39 ns segun frecuencia, "
          "amplitud al riel",
          chain="es INTERFAZ, no parametro de este bloque. Si la neurona "
                "cambia su pulso, la ley de inyeccion hay que remedirla")
    return d


_NOM = {}


def nominal() -> dict[str, float]:
    """El punto nominal, DERIVADO con el propio motor y cacheado."""
    if not _NOM:
        _NOM.update(design(IntegratorSpec(**NOMINAL_SPEC)).params)
    return dict(_NOM)
