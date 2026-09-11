"""integrator_design -- el motor de diseño del integrador de CapiMagics.

El integrador es el LECTOR DE LA TASA DE DISPARO: frecuencia de spikes -> tension.
Tercer motor de la cadena, hermano de `encoder_design` y `lif_design`.

    encoder  (tension -> corriente)
       -> LIF  (corriente -> frecuencia)
          -> INTEGRADOR  (frecuencia -> tension)

Uso:

    import integrator_design as I
    d = I.design(I.IntegratorSpec(f_min=150, f_max=2400))
    print(d.report())

Lo que lo distingue de los otros dos:
  * se pide una BANDA, no un valor, y la banda es un contrato con la cadena
  * la SATURACION se reporta hacia arriba (cada geometria deja de leer)
  * el rizado tiene ley SIN COEFICIENTES: I_fuga/(f*C)
  * `vm` no se ajusta, se RESUELVE componiendo fuga e inyeccion
"""
from .coeffs import BANDA_CADENA, CAJA_FUGA, CAJA_INY, IREF_RANGO, L_LEAKPASS_FIJO, VM_RANGO
from .laws import (
    ancho_ns, c_in, en_caja_fuga, en_caja_iny, f_satura, fuga, inyeccion,
    r_out,
    resolucion, rizado, sensibilidad, t_respuesta, techo, vm_equilibrio,
)
from .solver import NOMINAL_SPEC, design, nominal
from .spec import IntegratorDesign, IntegratorSpec, Note, Severity

__all__ = [
    "IntegratorSpec", "IntegratorDesign", "Note", "Severity",
    "design", "nominal", "NOMINAL_SPEC",
    "techo", "fuga", "inyeccion", "vm_equilibrio", "rizado",
    "sensibilidad", "resolucion", "f_satura", "ancho_ns", "t_respuesta",
    "c_in", "r_out",
    "en_caja_fuga", "en_caja_iny",
    "BANDA_CADENA", "CAJA_FUGA", "CAJA_INY", "IREF_RANGO", "L_LEAKPASS_FIJO", "VM_RANGO",
]
