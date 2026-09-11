"""Ejemplos de uso del motor del encoder.

    python -m encoder_design.example
"""
from . import EncoderSpec, design, laws


def _sep(t):
    print("\n" + "=" * 66)
    print(t)
    print("=" * 66)


def main():
    _sep("1. Sin objetivos: el punto nominal")
    print(design(EncoderSpec()).report())

    _sep("2. Con objetivos. SE PIDE CON DOS, no con tres")
    d = design(EncoderSpec(iex_min=100, gain=0.35))
    print(d.report())

    _sep("3. El tercer objetivo se da para COMPROBARLO, no para pedirlo")
    d = design(EncoderSpec(iex_min=60, gain=0.35, iex_max=180))
    print("ok =", d.ok)
    for n in d.errors:
        print(n)
    print("\n  ...y el mismo pedido con el valor que el circuito permite:")
    d = design(EncoderSpec(iex_min=60, gain=0.35, iex_max=207))
    print("  ok =", d.ok)

    _sep("4. Los grados de libertad que sobran: area contra apareamiento")
    print("%10s %12s %12s %10s %8s" %
          ("tradeoff", "area", "sigma_Vos", "iex_min", "gain"))
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        p = design(EncoderSpec(iex_min=100, gain=0.35, tradeoff=t)).predicted
        print("%10.2f %9.3f um2 %9.1f mV %7.1f nA %8.4f" %
              (t, p["area [um2]"], p["sigma_Vos [mV]"],
               p["iex_min [nA]"], p["gain"]))
    print("\n  Un factor 4 en desviacion a especificacion identica.")
    print("  La palanca es Ll (el par de CARGA), no el par de entrada:")
    print("  el reflejo de 'agrandar la entrada' da 1.7x; esto da 3-4x.")

    _sep("5. Esquinas: el diseño no cambia, lo que hace el chip si")
    d = design(EncoderSpec(iex_min=100, gain=0.35))
    ie = d.predicted["iex_min [nA]"]
    print("%-10s %6s %14s" % ("esquina", "T", "Iex(-) resultante"))
    for cor, t in laws.CONDICIONES:
        fi, _ = laws.corner_factors(cor, t)
        print("%-10s %5dC %12.1f nA  (x%.2f)" % (cor, t, ie * fi, fi))
    print("\n  Factor 5 entre extremos. NO es un problema de este paquete:")
    print("  se arregla en la polarizacion (seccion 7 del knowledge base).")

    _sep("6. Fijar dimensiones a mano")
    d = design(EncoderSpec(iex_min=100, gain=0.35, Ll=0.30))
    print("  Ll fijado a 0.30:", {k: d.params[k] for k in ("Wd", "Wl", "Ll", "L9")})
    print("  ->", d.predicted["iex_min [nA]"], "nA, sigma",
          d.predicted["sigma_Vos [mV]"], "mV")
    d = design(EncoderSpec(iex_min=100, gain=0.35, Wd=5.0))
    print("\n  Fuera de la caja medida:")
    for n in d.warnings:
        print("   ", n)


if __name__ == "__main__":
    main()
