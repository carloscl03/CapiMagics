"""Sistema de diseño por capas para la neurona LIF (GF180MCU).

Herramienta PARA que la use una IA, no una IA: la entrada es determinista y la
salida son datos estructurados, incluido el detalle de por que algo no se puede.

Uso:
    from design import NeuronSpec, design

    # "haz una neurona y ya" -> punto nominal medido
    d = design(NeuronSpec())

    # con objetivos
    d = design(NeuronSpec(iex_range=(20, 200), freq_range=(200, 1500)))

    # con dimensiones ya calculadas por el diseñador
    d = design(NeuronSpec(W_reset=1.0, freq_range=(500, 500)))

    print(d.report())
    if not d.ok:
        for e in d.errors:
            print(e.chain)

Solo stdlib: math, dataclasses, enum. Sin numpy -- son ~15 pow() por diseño.
"""
from .laws import (
    c_load_max, Cm_min, freq, freq_at_iex_ref, gain, iex_window,
    min_source_impedance, swing, vth, vth_max_at,
)
from .solver import NOMINAL, design
from .spec import NeuronDesign, NeuronSpec, Note, Severity

__all__ = [
    "NeuronSpec", "NeuronDesign", "Note", "Severity", "design", "NOMINAL",
    "freq", "freq_at_iex_ref", "gain", "vth", "swing", "Cm_min",
    "iex_window", "c_load_max", "min_source_impedance", "vth_max_at",
]
