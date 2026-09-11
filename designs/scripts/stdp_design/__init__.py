"""Motor de diseno de la sinapsis STDP (gf180mcuD).

    from stdp_design import StdpSpec, design
    d = design(StdpSpec(tau_us=5.5, f_min_kHz=12.8, f_max_kHz=4500))
    print(d.report())

Caracterizacion en `sch/stdp/results/stdp_knowledge_base.md` (10.741 puntos).
Sobre el netlist ARREGLADO: `designs/libs/snn_analog/stdp/stdp_propuesta.spice`.
"""
from .spec import Note, Severity, StdpDesign, StdpSpec
from .solver import design
from . import laws, coeffs

__all__ = ["StdpSpec", "StdpDesign", "Note", "Severity", "design",
           "laws", "coeffs"]
