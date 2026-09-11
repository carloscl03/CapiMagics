"""Contrato de entrada y salida del diseño del integrador.

Mismo criterio que `encoder_design` y `lif_design`: entrada determinista,
salida estructurada, y se informa con honestidad de lo que no se puede.

Politica de prioridades (la del equipo):
  1. OBJETIVOS de diseño  -- mandan
  2. DIMENSIONES fijadas  -- se ajustan si estorban, con WARNING
  3. Si la contradiccion no se puede resolver -> ERROR con la cadena causal

Lo propio del integrador frente a los otros dos:

  * LA BANDA ES UN CONTRATO BIDIRECCIONAL. No se pide una corriente, se pide un
    rango de frecuencias a leer. Y ese rango tiene que caber en lo que la
    cadena produce: `EncoderSpec` -> Iex -> `NeuronSpec` -> 74-4500 kHz. Pedir
    fuera de ahi es un error de sistema, no del integrador.

  * LA SATURACION SE REPORTA HACIA ARRIBA. Cada geometria deja de leer a cierta
    frecuencia, porque `vm` se pega al techo (1.92-2.73 V segun `L6`). Eso es
    un dato del contrato, no algo que se descubra en silicio.

  * `Iref` ES ENTRADA, NO CONSTANTE. Desplaza la ventana en frecuencia sin
    cambiar su anchura -- el analogo exacto del `Vbias` del encoder, y hereda
    su problema: deriva con esquina y temperatura.

  * EL SPIKE ES INTERFAZ. Ancho, amplitud y flancos los fija la neurona, no el
    integrador. Estuvieron clavados como constantes en el banco durante toda la
    caracterizacion sin haberse medido; ahora `laws.ancho_ns(f)` los declara.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


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
class IntegratorSpec:
    """Lo que se le pide al integrador.

    OBJETIVOS
      f_min, f_max   la banda a leer, en kHz. Es lo unico obligatorio.
      resolucion_min   si se da, se exige; si no, se maximiza.
      t_respuesta_max  [us] cuanto puede tardar la lectura en asentarse cuando
                       la neurona cambia de frecuencia. `tau = C*vm/I_fuga`.
                       COMPITE con la resolucion: bajar el rizado pide poca
                       corriente y mucha capacidad, que es justo lo que hace
                       lenta la respuesta. Sin este limite el motor elige
                       tau de milisegundos.

    PERILLA
      tradeoff  0 = toda la holgura (banda ancha, margen al techo)
                1 = toda la resolucion (poco rizado, banda justa)
                Los dos compiten: `L6` largo mejora el rizado pero BAJA el
                techo, o sea que estrechas la banda para ganar precision
                dentro de ella.

    DIMENSIONES (cualquiera puede venir dada; se libera si estorba)
      W1, W2, L2, Iref   la fuga.  `L1` va fijo en 0.28 um (ver laws.fuga)
      W6, L6, C          la inyeccion y la memoria

    CONTEXTO
      area_max   [um2] si se da, se penaliza el condensador
    """
    f_min: float | None = None
    f_max: float | None = None
    resolucion_min: float | None = None
    t_respuesta_max: float | None = None      # us
    tradeoff: float = 0.5

    W1: float | None = None
    W2: float | None = None
    L2: float | None = None
    Iref: float | None = None
    W6: float | None = None
    L6: float | None = None
    C: float | None = None

    area_max: float | None = None

    @property
    def fixed_dims(self) -> dict[str, float]:
        d = {}
        for k in ("W1", "W2", "L2", "Iref", "W6", "L6", "C"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        return d

    @property
    def has_objectives(self) -> bool:
        return self.f_min is not None and self.f_max is not None


@dataclass
class IntegratorDesign:
    """Lo que el sistema devuelve.

    NUNCA lanza excepcion: siempre trae `params` con la mejor solucion
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
            u = "nA" if k == "Iref" else ("fF" if k == "C" else "um")
            lines.append(f"  {k:10s} = {v:9.3f} {u}")
        if self.predicted:
            lines += ["", "Comportamiento predicho:"]
            for k, v in self.predicted.items():
                lines.append(f"  {k:24s} = {v}")
        if self.requirements:
            lines += ["", "Requisitos sobre el entorno:"]
            for k, v in self.requirements.items():
                lines.append(f"  {k:24s} : {v}")
        if self.notes:
            lines += ["", "Notas:"]
            lines += [f"  {n}" for n in self.notes]
        return "\n".join(lines)
