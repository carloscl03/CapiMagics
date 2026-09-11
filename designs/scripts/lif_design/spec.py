"""Contrato de entrada y salida del sistema de diseño.

Entrada determinista: esto es una herramienta PARA que la use una IA, no una
IA. Quien llama expresa la intencion; aqui solo se resuelve con precision y se
informa con honestidad de lo que no se puede.

Politica de prioridades (decidida por el equipo):
  1. OBJETIVOS de diseño  -- mandan
  2. DIMENSIONES fijadas  -- se ajustan si estorban, con WARNING
  3. Si la contradiccion no se puede resolver -> ERROR con la cadena causal
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
    subject: str          # que parametro / objetivo
    message: str          # que paso
    chain: str = ""       # la cadena causal, cuando aplica

    def __str__(self) -> str:
        s = f"[{self.severity.value.upper()}] {self.subject}: {self.message}"
        if self.chain:
            s += f"\n    cadena: {self.chain}"
        return s


def _as_range(v):
    """Normaliza a (lo, hi): un escalar x se vuelve (x, x); None sigue None.

    Todo lo interno trabaja con pares, asi que las capas de resolucion no
    tienen que distinguir si el usuario pidio un punto o un rango.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return (float(v), float(v))
    lo, hi = v
    return (float(lo), float(hi))


@dataclass
class NeuronSpec:
    """Lo que el diseñador pide.

    Todo es opcional. None significa "decide tu", no un default fijo -- la
    distincion importa porque es lo que da libertad a las capas de resolucion.

    Objetivos (prioridad 1):
        iex_range   corriente que entregara la etapa previa [nA]
        freq_range  frecuencia deseada a la salida [kHz]

        Ambos aceptan un par (lo, hi) para pedir un rango, o un solo
        numero para pedir ese valor exacto: freq_range=500 equivale a
        freq_range=(500, 500).
        vth         umbral de disparo [V]
        c_load      carga capacitiva que colgara la etapa siguiente [fF]

    Dimensiones fijadas (prioridad 2, se ajustan con warning si estorban):
        W_reset, L_reset, Cm, W_buf

    Contexto:
        source_ro   impedancia de salida de la fuente de corriente [ohm].
                    Si se da, el sistema calcula el error esperado.
        c_in_max    capacidad maxima que la etapa previa puede manejar [fF].
                    Dual de c_load: nuestro c_load es el C_in de la celda
                    siguiente, y nuestro C_in es el c_load de la anterior.
                    Se comprueba, no se resuelve: C_in solo va de 1.1 a 4.0 fF
                    en todo el envolvente, asi que la cota practicamente nunca
                    puede morder. Si algun dia lo hace, sube a objetivo y
                    compite con la frecuencia por W_reset.
        freq_tolerance  desviacion aceptable al resolver [fraccion]
    """
    # objetivos
    iex_range: tuple[float, float] | float | None = None
    freq_range: tuple[float, float] | float | None = None
    vth: float | None = None
    c_load: float | None = None

    # dimensiones fijadas
    W_reset: float | None = None
    L_reset: float | None = None
    Cm: float | None = None
    W_buf: float | None = None

    # contexto
    source_ro: float | None = None
    c_in_max: float | None = None
    freq_tolerance: float = 0.05

    def __post_init__(self) -> None:
        self.iex_range = _as_range(self.iex_range)
        self.freq_range = _as_range(self.freq_range)

    def fixed_dims(self) -> dict[str, float]:
        """Las dimensiones que el usuario fijo explicitamente."""
        return {
            n: v for n, v in (
                ("W_reset", self.W_reset), ("L_reset", self.L_reset),
                ("Cm", self.Cm), ("W_buf", self.W_buf),
            ) if v is not None
        }

    def has_objectives(self) -> bool:
        return any(x is not None for x in
                   (self.iex_range, self.freq_range, self.vth, self.c_load))


@dataclass
class NeuronDesign:
    """Lo que el sistema devuelve.

    NUNCA lanza excepcion: siempre trae params con la mejor solucion
    alcanzable. Un agente que consume esto necesita datos estructurados sobre
    el conflicto, no un stack trace.
    """
    params: dict[str, float]              # W_reset, L_reset, Cm, W_buf
    predicted: dict[str, object] = field(default_factory=dict)
    requirements: dict[str, object] = field(default_factory=dict)
    notes: list[Note] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """False si hubo alguna contradiccion irresoluble."""
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
        """Resumen legible. Para consumo por humano; una IA usa los campos."""
        lines = ["=" * 62,
                 "DISEÑO " + ("OK" if self.ok else "CON ERRORES"),
                 "=" * 62, "", "Parametros:"]
        for k, v in self.params.items():
            unit = "fF" if k == "Cm" else "um"
            lines.append(f"  {k:10s} = {v:8.3f} {unit}")
        if self.predicted:
            lines += ["", "Comportamiento predicho:"]
            for k, v in self.predicted.items():
                lines.append(f"  {k:18s} = {v}")
        if self.requirements:
            lines += ["", "Requisitos sobre el entorno:"]
            for k, v in self.requirements.items():
                lines.append(f"  {k:18s} : {v}")
        if self.notes:
            lines += ["", "Notas:"]
            lines += [f"  {n}" for n in self.notes]
        return "\n".join(lines)
