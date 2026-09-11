"""Resolucion por capas: viabilidad -> objetivos -> grados de libertad sobrantes.

El sistema NO es "spec -> parametros" sino un sistema de restricciones
parcialmente fijadas: cualquiera de las cuatro dimensiones puede venir dada, y
se resuelve solo lo libre. Tres regimenes, como en la neurona:

  sub-determinado    hay familia de soluciones -> se elige con `tradeoff`
  determinado        solucion unica
  sobre-determinado  puede no haber solucion -> se libera lo fijado (warning)
                     o se reporta la contradiccion (error)

El orden importa y no es arbitrario:

  1. VIABILIDAD. Antes de tocar ninguna geometria se comprueba si el pedido
     existe. Los tres objetivos viven en una superficie; una terna inventada
     casi nunca cae en ella. Aproximar en silencio es el fallo que hay que
     evitar -- costo dos hipotesis falsas descubrirlo durante la
     caracterizacion.

  2. OBJETIVOS. Busqueda en las variables libres. Si las fijadas impiden llegar,
     se liberan: LOS OBJETIVOS MANDAN SOBRE LAS DIMENSIONES FIJADAS (politica
     del equipo, lif_design/spec.py).

  3. LO QUE SOBRA. Dos objetivos contra cuatro variables dejan dos libres. Se
     gastan segun `tradeoff` entre area y desapareamiento, que a especificacion
     identica valen un factor ~4 en sigma_Vos.

ORDEN DE LIBERACION cuando hay que tocar algo fijado, por coste de cambio. Sale
de las leyes medidas, no de intuicion:

  1. L_tail   la cola. No interviene en la ganancia (exponente 0.03) ni en el
          desapareamiento (0.03), y no es un par apareado. Cambiarla no
          arrastra nada.
  2. W_load   ancho de las cargas. Mueve la ganancia pero NO el desapareamiento
          (exponente 0.03).
  3. L_load   largo de las cargas. Mueve la ganancia Y domina el desapareamiento
          (exponente -1.07): tocarla se paga en sigma_Vos.
  4. W_in   el par de entrada. Mueve la ganancia, el desapareamiento, y es el par
          apareado con mas peso en el layout. Lo ultimo que se toca.

Sin numpy: la busqueda son unos pocos miles de evaluaciones de ~105 productos.
"""
from __future__ import annotations

import random
from math import log10

from . import coeffs as C
from . import laws as L
from .spec import EncoderDesign, EncoderSpec, Severity

__all__ = ["design", "nominal", "NOMINAL_SPEC"]

_ORDEN = ("W_in", "W_load", "L_load", "L_tail")

# --- el punto nominal -------------------------------------------------------
#
# NO son cuatro numeros clavados. El nominal de la neurona si lo es, porque el
# suyo es una CELDA MEDIDA. El nuestro es el resultado de una busqueda, asi que
# lo que se guarda es EL CRITERIO, y las dimensiones se derivan resolviendolo.
# Si mañana cambian las leyes o la caja, el nominal se mueve solo al punto que
# vuelva a cumplir el criterio.
#
# CRITERIO: el punto mas COMODO DE CARACTERIZAR -- no el mas util ni el mas
# barato. En este proyecto eso significa lejos de los bordes de la caja, que es
# donde las leyes son de fiar. Medido:
#
#     distancia al borde     lgIa    lgIb
#     pegado  (<5 %)        0.79 %  0.74 %
#     centro  (>30 %)       0.44 %  0.50 %
#
# Buscando con el propio motor la peticion cuya solucion cae mas adentro sale
# esta, con los cuatro ejes al 43-53 % del borde:
# DEFAULT. Es el REF del desarrollo potencia x correccion, y encaja con la
# cadena: 80-286 nA caen dentro de la ventana de la celda v3 (5-1755 nA) y dan
# 205-734 kHz en la capa 1.
# AVISO: solo usa el 16 % de la ventana del LIF, asi que el ENCODER es el
# cuello de botella del rango dinamico de todo el sistema. Ampliarlo pide mas
# ganancia, y la ganancia empeora `source_ro` (ver la matriz de acoplo).
NOMINAL_SPEC = {"iex_min": 80.0, "gain": 0.40, "tradeoff": 0.5}

# Verificado en ngspice (2026-09-01) con las leyes de esta version:
#   dimensiones  W_in 0.725  W_load 0.947  L_load 0.394  L_tail 1.811
#   predicho     80.0 / 286.5 nA   G=0.400   V(a)=582 mV
#   ngspice      79.6 / 285.4 nA   G=0.401   V(a)=583 mV  (-0.5 %, -0.4 %, +0.1 %)
#
# El criterio se verifica solo: de los tres diseños de referencia, el que peor
# valida (`lento`, -2.7 %) es el que tiene L_load = 0.280, pegado al borde.
#
# Para comparar, la celda original del equipo (W_in=0.5 L_in=10 W_load=2 L_load=0.28
# Wb=0.5 Lb=0.28) da 40.0/56.0 nA, G=0.075 y V(a)=41 mV: ganancia 4x menor,
# excursion de 1.4x en vez de 3x, y M9 en triodo.
_NOMINAL_CACHE: dict[str, float] | None = None


def nominal() -> dict[str, float]:
    """Las dimensiones del punto nominal, derivadas de `NOMINAL_SPEC`.

    Se resuelven una vez y se cachean. No es una constante a proposito: si las
    leyes cambian, esto sigue devolviendo el punto que cumple el criterio.
    """
    global _NOMINAL_CACHE
    if _NOMINAL_CACHE is None:
        from .spec import EncoderSpec
        s = EncoderSpec(**NOMINAL_SPEC)
        v, _ = _resolver(s, list(_ORDEN), {},
                         NOMINAL_SPEC["iex_min"], NOMINAL_SPEC["gain"])
        _NOMINAL_CACHE = {n: round(v[n], 3) for n in _ORDEN}
    return dict(_NOMINAL_CACHE)


def _coste(g, iex_obj, gain_obj, va_min, tradeoff):
    """Error de especificacion + penalizacion + objetivo secundario."""
    try:
        ie = L.iex_min(*g)
        gn = L.gain(*g)
        va = L.v_a(*g)
    except (ValueError, OverflowError):
        return float("inf")
    if ie <= 0 or gn <= 0:
        return float("inf")

    e = 0.0
    if iex_obj is not None:
        e += (log10(ie / iex_obj)) ** 2
    if gain_obj is not None:
        e += (log10(gn / gain_obj)) ** 2
    e *= 300.0                                   # la especificacion manda

    if va < va_min:                              # M9 fuera de saturacion
        e += 100.0 * (va_min - va) ** 2

    # lo que sobra: area contra desapareamiento
    a = log10(L.area(*g))
    s = log10(L.sigma_vos(*g))
    e += tradeoff * a + (1.0 - tradeoff) * s
    return e


def _resolver(spec, libres, fijas, iex_obj, gain_obj, semilla=0):
    """Busqueda global gruesa + refinado local. Determinista."""
    rng = random.Random(semilla)
    rangos = {n: C.CAJA[_ORDEN.index(n)] for n in _ORDEN}

    def arma(vals):
        g = dict(fijas)
        g.update(vals)
        return tuple(g[n] for n in _ORDEN)

    def muestrea():
        return {n: 10.0 ** rng.uniform(log10(rangos[n][0]), log10(rangos[n][1]))
                for n in libres}

    mejor, cb = None, float("inf")
    for _ in range(4000):
        v = muestrea()
        c = _coste(arma(v), iex_obj, gain_obj, spec.va_min, spec.tradeoff)
        if c < cb:
            cb, mejor = c, v
    if mejor is None:
        return {n: 10.0 ** ((log10(rangos[n][0]) + log10(rangos[n][1])) / 2)
                for n in libres}, float("inf")

    for paso in (0.08, 0.03, 0.01, 0.003, 0.001):
        for _ in range(400):
            v = {}
            for n in libres:
                lo, hi = rangos[n]
                x = log10(mejor[n]) + rng.gauss(0.0, paso)
                v[n] = 10.0 ** min(max(x, log10(lo)), log10(hi))
            c = _coste(arma(v), iex_obj, gain_obj, spec.va_min, spec.tradeoff)
            if c < cb:
                cb, mejor = c, v
    return mejor, cb


# Orden de liberacion por coste de cambio (ver docstring del modulo).
_COSTE = ("L_tail", "W_load", "L_load", "W_in")

_PORQUE = {
    "L_tail": "no interviene ni en la ganancia ni en el desapareamiento",
    "W_load": "mueve la ganancia pero no el desapareamiento",
    "L_load": "mueve la ganancia y domina el desapareamiento: se paga en sigma_Vos",
    "W_in": "es el par apareado de entrada, lo mas caro de tocar",
}


def _error(g, iex_obj, gain_obj):
    """Peor desviacion relativa respecto de los objetivos dados."""
    e = 0.0
    if iex_obj is not None:
        e = max(e, abs(L.iex_min(*g) / iex_obj - 1.0))
    if gain_obj is not None:
        e = max(e, abs(L.gain(*g) / gain_obj - 1.0))
    return e


def _resolver_liberando(spec, d, fijas, iex_obj, gain_obj):
    """Resuelve; si lo fijado impide llegar, lo libera por orden de coste.

    Los objetivos mandan sobre las dimensiones fijadas (prioridad 1 sobre 2).
    Cada liberacion se reporta con su WARNING y su cadena causal: que se cambio,
    a que, y que pasaba si no.
    """
    def resuelve(fj):
        libres = [n for n in _ORDEN if n not in fj]
        if not libres:
            return tuple(fj[n] for n in _ORDEN)
        v, _ = _resolver(spec, libres, fj, iex_obj, gain_obj)
        return tuple({**fj, **v}[n] for n in _ORDEN)

    g = resuelve(fijas)
    e = _error(g, iex_obj, gain_obj)
    if e <= spec.tolerance or not fijas:
        if e > spec.tolerance:
            _no_alcanza(d, g, spec, iex_obj, gain_obj, fijas)
        return g, fijas

    # lo fijado estorba: liberar por orden de coste hasta llegar
    for n in _COSTE:
        if n not in fijas:
            continue
        antes, e_antes = fijas[n], e
        libre = dict(fijas)
        del libre[n]
        g2 = resuelve(libre)
        e2 = _error(g2, iex_obj, gain_obj)
        if e2 < e_antes - 1e-9:
            nuevo = g2[_ORDEN.index(n)]
            d.add(Severity.WARNING, n,
                  f"cambiada de {antes:.3f} a {nuevo:.3f} um para alcanzar "
                  f"lo pedido",
                  f"con {n}={antes:.3f} fija el mejor alcanzable era "
                  f"{e_antes * 100:.1f} % de desviacion; liberandola baja a "
                  f"{e2 * 100:.1f} %. Se eligio {n} primero porque "
                  f"{_PORQUE[n]}")
            fijas, g, e = libre, g2, e2
            if e <= spec.tolerance:
                return g, fijas
    if e > spec.tolerance:
        _no_alcanza(d, g, spec, iex_obj, gain_obj, fijas)
    return g, fijas


def _no_alcanza(d, g, spec, iex_obj, gain_obj, fijas):
    """El objetivo no se alcanza ni liberandolo todo."""
    partes = []
    if iex_obj is not None:
        v = L.iex_min(*g)
        partes.append(f"iex_min {v:.1f} nA de {iex_obj:.1f} pedidos "
                      f"({(v / iex_obj - 1) * 100:+.1f} %)")
    if gain_obj is not None:
        v = L.gain(*g)
        partes.append(f"gain {v:.4f} de {gain_obj:.4f} pedidos "
                      f"({(v / gain_obj - 1) * 100:+.1f} %)")
    aun = (f" aun con {', '.join(sorted(fijas))} fijada(s)" if fijas
           else " con las cuatro dimensiones libres")
    d.add(Severity.ERROR, "objetivos",
          f"no alcanzable{aun}: " + "; ".join(partes),
          "lo mas cercano dentro de la caja medida. El pedido puede rozar el "
          "borde de la caja, o los dos objetivos pueden competir entre si")


def design(spec: EncoderSpec | None = None) -> EncoderDesign:
    """Resuelve un EncoderSpec. Nunca lanza excepcion."""
    spec = spec or EncoderSpec()
    d = EncoderDesign()

    # --- 0. cordura de la entrada -----------------------------------------
    tradeoff = min(max(spec.tradeoff, 0.0), 1.0)
    if tradeoff != spec.tradeoff:
        d.add(Severity.WARNING, "tradeoff",
              f"{spec.tradeoff} fuera de [0, 1]; se usa {tradeoff}")
    spec.tradeoff = tradeoff

    fijas = {}
    for n, v in spec.fixed_dims().items():
        lo, hi = C.CAJA[_ORDEN.index(n)]
        if not lo <= v <= hi:
            nv = min(max(v, lo), hi)
            d.add(Severity.WARNING, n,
                  f"{v:.3f} um fuera de la caja medida [{lo}, {hi}]; "
                  f"se recorta a {nv:.3f}",
                  "fuera de la caja las leyes no estan validadas")
            v = nv
        fijas[n] = v

    iex_obj, gain_obj = spec.iex_min, spec.gain

    # --- 1. viabilidad: el pedido existe? ---------------------------------
    if spec.iex_max is not None:
        if iex_obj is None or gain_obj is None:
            d.add(Severity.INFO, "iex_max",
                  "solo se comprueba si se dan tambien iex_min y gain; "
                  "se ignora")
        else:
            exige = L.iex_max(iex_obj, gain_obj)
            desv = spec.iex_max / exige - 1.0
            if abs(desv) > max(spec.tolerance, 0.05):
                d.add(Severity.ERROR, "iex_max",
                      f"pediste {spec.iex_max:.1f} nA pero con iex_min="
                      f"{iex_obj:.1f} nA y gain={gain_obj:.3f} el circuito "
                      f"exige {exige:.1f} nA ({desv * 100:+.0f} %)",
                      "los tres objetivos no son independientes: viven en una "
                      "superficie de espesor 0.022 decadas. Fija dos y el "
                      "tercero queda determinado.")
            else:
                d.add(Severity.INFO, "iex_max",
                      f"{spec.iex_max:.1f} nA es compatible "
                      f"({desv * 100:+.1f} % de lo que exige la ley)")

    if not spec.has_objectives():
        d.add(Severity.INFO, "objetivos",
              "sin objetivos: se devuelve el punto nominal, que es el mas "
              "comodo de caracterizar (el mas interior de la caja)",
              "derivado de NOMINAL_SPEC=%s, no clavado a mano: si cambian las "
              "leyes, el nominal se mueve con ellas" % NOMINAL_SPEC)

    # --- 2. objetivos, liberando lo fijado si estorba ---------------------
    if not spec.has_objectives():
        nom = nominal()
        v = {n: nom[n] for n in _ORDEN if n not in fijas}
        g = tuple({**fijas, **v}[n] for n in _ORDEN)
        if not v:
            d.add(Severity.INFO, "dimensiones",
                  "las cuatro fijadas: no queda nada que resolver")
    else:
        g, fijas = _resolver_liberando(spec, d, dict(fijas), iex_obj, gain_obj)

    d.params = {n: round(x, 3) for n, x in zip(_ORDEN, g)}
    d.params["L_in"] = C.LD
    d.params["W_tail"] = C.W_tail

    # --- 3. que sale de aqui ----------------------------------------------
    ie, gn, va = L.iex_min(*g), L.gain(*g), L.v_a(*g)
    ix = L.iex_max(ie, gn)
    fi, fg = L.corner_factors(spec.corner, spec.temp)

    d.predicted = {
        "iex_min [nA]": round(ie, 1),
        "iex_max [nA]": round(ix, 1),
        "gain": round(gn, 4),
        "V(a) [mV]": round(va * 1000, 0),
        "sigma_Vos [mV]": round(L.sigma_vos(*g) * 1000, 1),
        "area [um2]": round(L.area(*g), 3),
        "C_in [fF]": round(L.c_in(*g), 2),
        "source_ro [ohm]": "%.2e a %.2e" % (L.source_ro(ix), L.source_ro(ie)),
    }

    if va < spec.va_min:
        d.add(Severity.ERROR, "V(a)",
              f"{va * 1000:.0f} mV, por debajo del margen de "
              f"{spec.va_min * 1000:.0f} mV: M9 no queda saturado")

    # --- 4. lo que el entorno tiene que cumplir ---------------------------
    req = {
        "Vbias [V]": f"{C.VBIAS_NOMINAL} nominal; la esquina exige otro valor",
        "deriva por esquina": (
            f"{spec.corner}/{spec.temp:.0f}C -> Iex x{fi:.2f}, ganancia x{fg:.2f}"
        ),
    }
    todos_i = [f for f, _ in C.ESQUINAS.values()]
    req["envolvente de proceso"] = (
        f"Iex entre x{min(todos_i):.2f} y x{max(todos_i):.2f} sobre las 15 "
        f"condiciones (factor {max(todos_i) / min(todos_i):.1f})"
    )

    ci = L.c_in(*g)
    if spec.c_in_max is not None and ci > spec.c_in_max:
        d.add(Severity.WARNING, "C_in",
              f"{ci:.2f} fF supera los {spec.c_in_max:.2f} fF que la etapa "
              f"anterior puede mover",
              "C_in va casi solo con W_in (exponente 0.93): bajarlo exige "
              "reducir el par de entrada, lo que se paga en apareamiento")

    # la interfaz con el LIF: source_ro es lo que NeuronSpec pide como contexto
    err_max = 1.9e9 / (L.source_ro(ix) * ix)
    err_min = 1.9e9 / (L.source_ro(ie) * ie)
    req["source_ro para NeuronSpec"] = (
        f"{L.source_ro(ix):.2e} ohm en el extremo alto -> pasalo tal cual a "
        f"NeuronSpec(source_ro=...)"
    )
    if err_max > 0.011:      # margen para no avisar justo en el cruce
        d.add(Severity.WARNING, "source_ro",
              f"a {ix:.0f} nA el espejo de salida da {L.source_ro(ix):.2e} ohm "
              f"y el LIF vera {err_max * 100:.1f} % de error, no 1 %",
              f"el espejo no llega al 1 % en NINGUN punto, y va a peor a "
              f"corriente baja: {err_min * 100:.1f} % en {ie:.0f} nA contra "
              f"{err_max * 100:.1f} % en {ix:.0f}. Se arregla en el espejo "
              f"(alargar Lo, cascodear), no en la etapa diferencial; cuanto "
              f"ayuda cada cosa no esta medido")
    d.requirements = req

    if spec.corner != "typical" or abs(spec.temp - 27) > 1:
        d.add(Severity.INFO, "esquina",
              f"el diseño se resuelve en typical/27C; en {spec.corner}/"
              f"{spec.temp:.0f}C dara {ie * fi:.1f}-{ix * fi:.1f} nA "
              f"con ganancia {gn * fg:.3f}")

    d.add(Severity.INFO, "polarizacion",
          "el divisor M10/M11 no puede generar el Vbias que exige cada "
          "esquina: cubre el 16 % del eje de velocidad y el 133 % del de "
          "sesgo p/n",
          "hace falta ajuste por chip, una referencia compensada en "
          "temperatura, o hacer el sistema ratiometrico con el LIF")

    d.add(Severity.INFO, "consumo del bias",
          "el divisor 0.5/0.28 : 0.5/0.28 consume %.1f uA, mas que la neurona "
          "(14.6) y que esta etapa (2.93) juntas"
          % L.i_ref(0.5, 0.28, 0.5, 0.28),
          "con Ln=10, Lp=20 baja a %.2f uA (74x menos) Y duplica el "
          "seguimiento de esquina (99 mV contra 44). Gana en las dos cosas"
          % L.i_ref(0.5, 10.0, 0.5, 20.0))

    # --- salidas: cuantas y con que polaridad ---------------------------
    n = spec.n_salidas
    if not (1 <= n <= 4):
        d.add(Severity.ERROR, "n_salidas",
              "%d fuera de rango: la celda tiene CUATRO copias de espejo" % n,
              "1 a 4. Con 2 puedes hacer ON+OFF o dos copias del mismo signo")
        n = max(1, min(4, n))
    # Reparto EQUILIBRADO por defecto: con 2 salidas lo natural en codificacion
    # neuromorfica es un par ON/OFF, no dos copias del mismo signo. Con
    # `solo_positivas=True` se llenan primero las ON.
    if spec.solo_positivas:
        pos, neg = min(n, 2), max(0, n - 2)
    else:
        pos = (n + 1) // 2
        neg = n - pos
    if spec.solo_positivas and n > 2:
        d.add(Severity.WARNING, "n_salidas",
              "solo hay DOS salidas positivas (Iex_1, Iex_2); se piden %d" % n,
              "las otras dos (Iex_3, Iex_4) bajan con Vdif")
        pos, neg = 2, n - 2
    d.predicted["salidas"] = "%d (%d ON, %d OFF)" % (n, pos, neg)
    d.requirements["salidas"] = (
        "Iex_1 e Iex_2 SUBEN con Vdif (canal ON), Iex_3 e Iex_4 BAJAN (OFF). "
        "Medido: 40.8 nA a Vdif=-0.14 y 57.0 a +0.14, y al reves para las OFF. "
        "Cada salida cuesta 48.5 nA (0.1 pct de los 47.81 uA que tira el "
        "bloque con CERO conectadas): la decision es de area y de topologia, "
        "no de consumo")
    if neg and not spec.solo_positivas:
        d.add(Severity.INFO, "polaridad",
              "%d salida(s) van al canal OFF: su neurona dispara MENOS cuando "
              "Vdif sube" % neg,
              "es lo que permite codificar ON/OFF, pero si no se queria, pon "
              "`solo_positivas=True` y n_salidas<=2")

    return d
