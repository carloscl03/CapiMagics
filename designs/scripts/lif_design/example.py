#!/usr/bin/env python3
"""Ejemplos de uso del sistema de diseño. Ejecutable directamente:

    python sch/lif/design/example.py

Para verificar por simulacion hace falta ngspice y el contenedor:

    docker exec capimagics_x bash -lc \\
      "python3.10 /foss/repo/sch/lif/design/example.py --verify"

Para usarlo desde otro script en cualquier ruta, instalar el paquete:

    cd sch/lif && pip install -e .

y luego basta con  `from design import NeuronSpec, design`.
"""
import sys
from pathlib import Path

# permite ejecutar este archivo sin haber instalado el paquete; si ya esta
# instalado con pip install -e, esta linea no cambia nada
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from design import NeuronSpec, design, verify  # noqa: E402

TB_DIR = Path(__file__).resolve().parent.parent / "tb"


def ejemplo_1_default():
    """Sin objetivos: devuelve el punto nominal, el unico simulado."""
    print("\n1. 'haz una neurona y ya'")
    d = design(NeuronSpec())
    print(f"   {d.params}")
    print(f"   f a 100 nA: {d.predicted['f a 100 nA [kHz]']} kHz")


def ejemplo_2_rangos():
    """Lo habitual: rango de entrada -> rango de salida."""
    print("\n2. rango de corriente -> rango de frecuencia")
    d = design(NeuronSpec(iex_range=(20, 200), freq_range=(300, 1200)))
    print(f"   {d.params}")
    print(f"   k = {d.predicted['k [kHz/nA]']} kHz/nA")
    print(f"   f = {d.predicted['f en el rango [kHz]']} kHz")
    print(f"   requisito: {d.requirements['impedancia de fuente']}")


def ejemplo_3_hibrido():
    """El diseñador ya calculo W; que se respete y se resuelva el resto."""
    print("\n3. hibrido: W fija, el resto libre")
    d = design(NeuronSpec(W_reset=1.0, freq_range=(500, 500)))
    print(f"   {d.params}")
    for n in d.notes:
        print(f"   {n}")


def ejemplo_4_conflicto():
    """Objetivo incompatible con las dimensiones fijadas."""
    print("\n4. conflicto resoluble (los objetivos mandan)")
    d = design(NeuronSpec(W_reset=1.0, L_reset=41, freq_range=(2000, 2000)))
    print(f"   {d.params}   ok={d.ok}")
    for n in d.warnings:
        print(f"   [{n.subject}] {n.message}")


def ejemplo_5_imposible():
    """Contradiccion sin salida: se explica la cadena causal."""
    print("\n5. imposible fisico (f baja + Vth alto estan acoplados)")
    d = design(NeuronSpec(freq_range=(200, 200), vth=2.5))
    print(f"   ok={d.ok}")
    for n in d.errors:
        print(f"   {n.message}")
        print(f"   cadena: {n.chain}")


def ejemplo_6_verify():
    """Cierra el lazo: netlist -> ngspice -> medida -> comparacion."""
    print("\n6. verificacion por simulacion")
    d = design(NeuronSpec(freq_range=(800, 800)))
    print(f"   diseño: {d.params}")
    r = verify(d, iex_na=100.0, workdir=TB_DIR)
    print(f"   {r.status}")
    for k in r.predicted:
        m = r.measured.get(k)
        if m:
            print(f"     {k:8s} pred {r.predicted[k]:8.2f}  med {m:8.2f}"
                  f"  {r.errors_pct.get(k, 0):+6.1f}%")


if __name__ == "__main__":
    ejemplo_1_default()
    ejemplo_2_rangos()
    ejemplo_3_hibrido()
    ejemplo_4_conflicto()
    ejemplo_5_imposible()
    if "--verify" in sys.argv:
        ejemplo_6_verify()
    else:
        print("\n(usa --verify para el ejemplo 6, que necesita ngspice)")
