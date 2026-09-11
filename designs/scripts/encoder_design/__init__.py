"""Sistema de diseño por capas para el encoder de CapiMagics (GF180MCU).

El encoder es la VCCS diferencial que convierte la entrada complementaria en la
corriente Iex que alimenta la membrana de cada LIF. Es la etapa que fija las
condiciones de contorno de `NeuronSpec`.

Herramienta PARA que la use una IA, no una IA: entrada determinista, salida
estructurada, incluido el detalle de por que algo no se puede.

Uso:
    from encoder_design import EncoderSpec, design

    # "haz un encoder y ya" -> punto nominal
    d = design(EncoderSpec())

    # con objetivos: SE PIDE CON DOS, no con tres
    d = design(EncoderSpec(iex_min=100, gain=0.35))

    # el tercero se puede dar, pero para COMPROBARLO
    d = design(EncoderSpec(iex_min=60, gain=0.35, iex_max=180))
    #   -> ERROR: con esos dos el circuito exige 207 nA, no 180

    # gastar los grados de libertad que sobran
    d = design(EncoderSpec(iex_min=100, gain=0.35, tradeoff=0.0))  # apareamiento
    d = design(EncoderSpec(iex_min=100, gain=0.35, tradeoff=1.0))  # area

    print(d.report())
    if not d.ok:
        for e in d.errors:
            print(e.chain)

Lo que hay que saber antes de usarlo:

  * SE PIDE CON DOS OBJETIVOS. `iex_min`, `iex_max` y `gain` no son
    independientes: viven en una superficie. Dar los tres es pedir algo que
    casi nunca existe.

  * EL DISEÑO SE RESUELVE EN typical/27C. La esquina no cambia la geometria,
    cambia lo que hara el chip: Iex deriva un factor 5 entre chips y eso se
    reporta en `requirements`, no se corrige.

  * ESO ULTIMO ES UN PROBLEMA DE CIRCUITO, NO DE ESTE PAQUETE. Se arregla en la
    polarizacion. Ver seccion 7 del knowledge base.

Precision (medida fuera de muestra, y el lazo cerrado verificado en ngspice):

    Iex(-)      0.65 %        viabilidad   1.26 %
    ganancia    0.26 %        sigma_Vos    5.6 %
    V(a)        0.12 %        esquinas      15 % (sobre una deriva de 5x)

    lazo cerrado: 22/25 pedidos dentro del +-2 %, 25/25 dentro del +-5 %

Solo stdlib: math, random, dataclasses, enum. Sin numpy a proposito, igual que
lif_design.
"""
from .coeffs import CAJA, CAJA_BIAS, LD, LO, REF, VBIAS_NOMINAL, W_tail, WO
from .laws import (
    area, c_in, corner_factors, en_caja, en_caja_bias, forma_corta,
    gain, i_ref,
    iex_max, iex_min, iex_para_ro, sigma_vos, source_ro, v_a,
    CONDICIONES, VA_MIN,
)
from .solver import NOMINAL_SPEC, design, nominal
from .spec import EncoderDesign, EncoderSpec, Note, Severity

__all__ = [
    "EncoderSpec", "EncoderDesign", "Note", "Severity", "design",
    "nominal", "NOMINAL_SPEC",
    "iex_min", "iex_max", "gain", "v_a", "sigma_vos", "area", "en_caja",
    "source_ro", "iex_para_ro", "c_in", "i_ref", "en_caja_bias",
    "corner_factors", "forma_corta", "CONDICIONES",
    "VA_MIN",
    "CAJA", "CAJA_BIAS", "REF", "LD", "W_tail", "WO", "LO", "VBIAS_NOMINAL",
]
