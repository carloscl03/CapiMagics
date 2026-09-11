# `stdp_design` — motor de la sinapsis STDP

```python
from stdp_design import StdpSpec, design
d = design(StdpSpec(tau_us=5.5, f_min_kHz=12.8, f_max_kHz=4500))
print(d.report())
```

Cuarto motor de la cadena, espejo de `encoder_design`, `integrator_design` y
`lif_design`: misma política (objetivos > dimensiones), mismos `Note`/`Severity`,
nunca lanza excepción.

Medido sobre **`designs/libs/snn_analog/stdp/stdp_propuesta.spice`**, no sobre el
netlist original — sin unir `n3` y `n4` la potenciación no conduce. La
caracterización completa (10.741 puntos) está en
`sch/stdp/results/stdp_knowledge_base.md`.

## Lo que este bloque tiene de distinto

**El equilibrio no es un objetivo, es una restricción.** En STDP aditivo la
deriva media del peso con pre y post no correlacionados va como
`r²·(A₊τ₊ − A₋τ₋)`. Si no es cero, los pesos se van al raíl y da igual lo bien
dimensionado que esté el resto. El motor *deriva* `W4` de esa condición en vez
de dejarla como preferencia.

**Hay un término no hebbiano y no se puede eliminar del todo.** La inyección de
carga hace derivar el peso con actividad presináptica sola. En potenciación se
anula eligiendo `W1 = 0.357 µm`; en depresión los dos términos son negativos y
no cruza cero — el mejor caso son 1.73 mV de peor caso sobre esquinas y
temperatura, contra 5.51 de la geometría original.

**`L1` es discreta y `L4` es constante.** No es simplificación: dejando fuera
una `L` entera el error de predicción es del 43-47 % (hasta 140 % en el peor
caso). Estos transistores cruzan la transición canal corto/largo y ninguna
forma de bajo orden la atraviesa. `L4` va al mínimo del proceso porque el óptimo
está ahí y gana en los tres ejes a la vez.

**El peso es volátil.** 79 ms de retención (`vw` tiene 550 fF y 144 GΩ). No es
un parámetro: es una propiedad que el sistema tiene que saber.

## Validación

| | |
|---|---|
| núcleo depresión | LOO por geometría **3.05 %**, peor 4.51 % |
| núcleo potenciación | LOO **3.5-5.2 %** en `W`; en `L` no se interpola |
| suelo | 0.03 % (depresión), ~4 % (potenciación) |
| decaimiento | −1.7 %, físico y sin coeficientes |
| **lazo cerrado** | **−4.0 % / +5.1 %** sobre 6 pedidos, moviendo `asimetría`, `W1` y `nCW` |

El error del motor **iguala** al de las leyes: el solver no amplifica. Esa es la
señal de que está sano, y es lo que en el integrador falló (2.98 % de ley contra
4 fallos de 25 en el lazo).

## Acoplo

`d.requirements` trae lo que hay que pasar a los vecinos en vez de suponerlo:
la carga capacitiva sobre los inversores de la neurona (5.32 fF con 4 sinapsis,
contra ~300 fF que mueve), lo que las salidas suman a `Cm` (2.02 fF sobre 280),
`R_out` (763 MΩ → 0.36 % de variación sobre la excursión de membrana) y la
retención del peso.

## Regenerar

```
python sch/stdp/tb/scripts/gen_coeffs_stdp.py
```
reconstruye `coeffs.py` desde los `.npz` de `sch/stdp/results/`.
