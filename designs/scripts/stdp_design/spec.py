"""Contrato de entrada y salida del diseno de la sinapsis STDP.

Mismo criterio que `encoder_design`, `integrator_design` y `lif_design`:
entrada determinista, salida estructurada, y se informa con honestidad de lo
que no se puede.

Politica de prioridades (la del equipo):
  1. OBJETIVOS de diseno  -- mandan
  2. DIMENSIONES fijadas  -- se ajustan si estorban, con WARNING
  3. Si la contradiccion no se puede resolver -> ERROR con la cadena causal

Lo propio de esta celda frente a las otras tres:

  * EL EQUILIBRIO NO ES OPCIONAL. En STDP aditivo la deriva media del peso va
    como `r^2*(A+ tau+ - A- tau-)` con pre y post no correlacionados. Si eso
    no es cero, los pesos se van al rail y da igual lo bien dimensionado que
    este el resto. Por eso el motor lo impone como restriccion, no como
    objetivo blando.

  * HAY UN TERMINO NO HEBBIANO. La inyeccion de carga hace derivar el peso con
    actividad presinaptica SOLA. En la potenciacion se anula eligiendo
    `W_trrd_pot = 0.357`; en la depresion no cruza cero y hay que vivir con 1.7 mV de
    peor caso. Se reporta siempre, porque no se puede eliminar del todo.

  * `L_trrd_pot` ES DISCRETA. No es una simplificacion: dejando fuera una `L` entera el
    error de prediccion es del 43-47 %. El motor elige de `L_TRRD_POT_DISC`.

  * LA VENTANA SE ACOPLA CON LA NEURONA. `tau` tiene que solapar con los
    intervalos entre spikes que el LIF produce. Pedir una ventana que no los
    cubre no es un error de esta celda, es un error de sistema -- y se avisa.

  * EL PESO ES VOLATIL. 79 ms de retencion. No es un parametro de diseno, es
    una propiedad que el sistema tiene que saber.
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
class StdpSpec:
    """Lo que se le pide a la sinapsis.

    OBJETIVOS
      tau_us          anchura de la ventana STDP [us]. Es lo unico obligatorio.
      dvw_evento_mV   cuanto peso cambia por evento, cerca de `dt -> 0`. Si no
                      se da, se maximiza dentro de la caja.
      asimetria       `A+/A-`. Por defecto 1.0, que con `tau+ = tau-` es la
                      condicion de equilibrio. El STDP biologico es asimetrico
                      a proposito (Bi & Poo: tau+ 17 ms, tau- 34 ms), asi que
                      se deja abierto -- pero el motor AVISA si el producto
                      `A*tau` no se compensa.

    ACOPLO CON LA NEURONA  (para comprobar, no para elegir)
      f_min_kHz, f_max_kHz   lo que la neurona produce. El motor comprueba que
                      la ventana los cubre. Con la celda v3 del equipo son
                      12.8 y 4500.
      n_sinapsis_pre, n_sinapsis_post   cuantas comparten cada linea de spike,
                      para reportar la carga que ve la neurona. En el 4x2, 2 y 4.

    DIMENSIONES (cualquiera puede venir dada; se libera si estorba)
      W_trrd_dep, W_trrd_pot, L_trrd_pot      lectura de las trazas. `L4` va FIJA a 0.28 (ver laws).
      nCdep, nCW      capacidades, en unidades de unitcap
      itd, itp        corrientes de decaimiento [A]

    CONTEXTO
      area_max        [um2] si se da, se penalizan las capacidades
    """
    tau_us: float | None = None
    dvw_evento_mV: float | None = None
    asimetria: float = 1.0

    f_min_kHz: float | None = None
    f_max_kHz: float | None = None
    n_sinapsis_pre: int = 2
    n_sinapsis_post: int = 4

    W_trrd_dep: float | None = None
    W_trrd_pot: float | None = None
    L_trrd_pot: float | None = None
    nCdep: int | None = None
    nCW: int | None = None
    itd: float | None = None
    itp: float | None = None

    area_max: float | None = None

    @property
    def fixed_dims(self) -> dict[str, float]:
        d = {}
        for k in ("W_trrd_dep", "W_trrd_pot", "L_trrd_pot", "nCdep", "nCW", "itd", "itp"):
            v = getattr(self, k)
            if v is not None:
                d[k] = v
        return d

    @property
    def has_objectives(self) -> bool:
        return self.tau_us is not None


@dataclass
class StdpDesign:
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
                 "DISENO " + ("OK" if self.ok else "CON ERRORES"),
                 "=" * 62, "", "Parametros:"]
        for k, v in self.params.items():
            u = ("um" if k.startswith(("W", "L")) else
                 "uds" if k.startswith("n") else
                 "nA" if k.startswith("i") else "")
            lines.append(f"  {k:10s} = {v:9.4g} {u}")
        if self.predicted:
            lines += ["", "Comportamiento predicho:"]
            for k, v in self.predicted.items():
                lines.append(f"  {k:28s} = {v}")
        if self.requirements:
            lines += ["", "Requisitos sobre el entorno:"]
            for k, v in self.requirements.items():
                lines.append(f"  {k:28s} : {v}")
        if self.notes:
            lines += ["", "Notas:"]
            lines += [f"  {n}" for n in self.notes]
        return "\n".join(lines)
