"""Contrato de entrada y salida del diseño del encoder.

Mismo criterio que el de la neurona: entrada determinista, salida estructurada,
y se informa con honestidad de lo que no se puede.

Politica de prioridades (la del equipo, en lif_design/spec.py):
  1. OBJETIVOS de diseño  -- mandan
  2. DIMENSIONES fijadas  -- se ajustan si estorban, con WARNING
  3. Si la contradiccion no se puede resolver -> ERROR con la cadena causal

Lo propio del encoder frente a la neurona:

  * Los objetivos NO son independientes. `iex_min`, `iex_max` y `gain` viven en
    una superficie: fijados dos, el tercero esta determinado. Se pide con
    (iex_min, gain) y `iex_max` se deduce. Si se dan los tres, se COMPRUEBA la
    terna y se avisa; nunca se aproxima en silencio.

  * Sobran grados de libertad. Dos objetivos contra cuatro variables dejan dos
    libres, que valen un factor 3 en desapareamiento a especificacion identica.
    De ahi el `tradeoff`.

  * La esquina es contexto de primera clase: Iex deriva un factor 5 entre
    chips, y eso no es un detalle que se pueda dejar implicito.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO = "info"        # una decision que se tomo por el usuario
    WARNING = "warning"  # se cambio algo que el usuario habia fijado
    ERROR = "error"      # contradiccion irresoluble


@dataclass
class Note:
    """Algo que el sistema decidio, cambio o no pudo hacer."""
    severity: Severity
    subject: str
    message: str
    chain: str = ""

    def __str__(self) -> str:
        s = f"[{self.severity.value.upper()}] {self.subject}: {self.message}"
        if self.chain:
            s += f"\n    cadena: {self.chain}"
        return s


@dataclass
class EncoderSpec:
    """Lo que el diseñador pide.

    Todo es opcional. None significa "decide tu", no un default fijo.

    Objetivos (prioridad 1):
        iex_min     corriente entregada al LIF en el extremo bajo [nA]
        gain        ganancia dV(x)/dVdif en el centro
        iex_max     extremo alto [nA]. NO es libre: si se da, se comprueba
                    contra la ley de viabilidad y se avisa si no existe.

    Objetivo secundario (prioridad 1.5, gasta los grados de libertad que sobran):
        tradeoff    0.0 = minima desviacion de entrada
                    1.0 = minima area
                    Vale un factor ~3 en sigma_Vos a especificacion identica.

    Dimensiones fijadas (prioridad 2, se ajustan con warning si estorban):
        Wd, Wl, Ll, L9   [um]

    Contexto:
        corner      typical | ff | ss | fs | sf
        temp        -40 | 27 | 125  [C]
                    Se resuelve SIEMPRE en typical/27C y se reporta la deriva:
                    la esquina no cambia el diseño, cambia lo que hara el chip.
        c_in_max    capacidad maxima que la etapa ANTERIOR puede mover [fF].
                    Dual del `c_in_max` de la neurona: nuestro `C_in` es el
                    `c_load` de quien nos alimente. Se comprueba, no se
                    resuelve.
        va_min      margen de saturacion exigido a M9 [V]. En las 15
                    condiciones medidas V(a) nunca bajo de 350 mV, asi que esta
                    cota practicamente nunca puede morder.
        tolerance   desviacion aceptable al resolver [fraccion]
    """
    # objetivos
    iex_min: float | None = None
    gain: float | None = None
    iex_max: float | None = None

    # objetivo secundario
    tradeoff: float = 0.5

    # dimensiones fijadas
    Wd: float | None = None
    Wl: float | None = None
    Ll: float | None = None
    L9: float | None = None

    # contexto
    corner: str = "typical"
    temp: float = 27.0
    c_in_max: float | None = None
    va_min: float = 0.15
    tolerance: float = 0.05

    def fixed_dims(self) -> dict[str, float]:
        """Las dimensiones que el usuario fijo explicitamente."""
        return {n: v for n, v in (("Wd", self.Wd), ("Wl", self.Wl),
                                  ("Ll", self.Ll), ("L9", self.L9))
                if v is not None}

    def has_objectives(self) -> bool:
        return any(x is not None for x in
                   (self.iex_min, self.gain, self.iex_max))


@dataclass
class EncoderDesign:
    """Lo que el sistema devuelve.

    NUNCA lanza excepcion: siempre trae params con la mejor solucion
    alcanzable. Un agente que consume esto necesita datos estructurados sobre
    el conflicto, no un stack trace.
    """
    params: dict[str, float] = field(default_factory=dict)
    predicted: dict[str, object] = field(default_factory=dict)
    requirements: dict[str, object] = field(default_factory=dict)
    notes: list[Note] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(n.severity is Severity.ERROR for n in self.notes)

    @property
    def errors(self) -> list[Note]:
        return [n for n in self.notes if n.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Note]:
        return [n for n in self.notes if n.severity is Severity.WARNING]

    def add(self, severity: Severity, subject: str, message: str,
            chain: str = "") -> None:
        self.notes.append(Note(severity, subject, message, chain))

    def report(self) -> str:
        """Resumen legible. Para humano; una IA usa los campos."""
        lines = ["=" * 62,
                 "DISEÑO " + ("OK" if self.ok else "CON ERRORES"),
                 "=" * 62, "", "Parametros:"]
        for k, v in self.params.items():
            lines.append(f"  {k:10s} = {v:8.3f} um")
        if self.predicted:
            lines += ["", "Comportamiento predicho:"]
            for k, v in self.predicted.items():
                lines.append(f"  {k:20s} = {v}")
        if self.requirements:
            lines += ["", "Requisitos sobre el entorno:"]
            for k, v in self.requirements.items():
                lines.append(f"  {k:20s} : {v}")
        if self.notes:
            lines += ["", "Notas:"]
            lines += [f"  {n}" for n in self.notes]
        return "\n".join(lines)
