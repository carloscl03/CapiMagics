# encoder_design

Motor de diseño del **encoder** de CapiMagics (GF180MCU): la VCCS diferencial
que convierte la entrada complementaria en la corriente `Iex` que alimenta la
membrana de cada LIF. Es la etapa que fija las condiciones de contorno de
`NeuronSpec`.

Mismo criterio que `lif_design`: entrada determinista, salida estructurada,
solo stdlib.

```python
from encoder_design import EncoderSpec, design

d = design(EncoderSpec(iex_min=100, gain=0.35))
print(d.report())
```

## Se pide con DOS objetivos, no con tres

`iex_min`, `iex_max` y `gain` **no son independientes**. La imagen del espacio
de diseño en ese espacio de tres es una *superficie* de espesor 0.022 décadas,
no un volumen: fijados dos, el tercero está determinado.

Por eso se pide con `(iex_min, gain)` y `iex_max` se deduce. Se puede dar el
tercero, pero para **comprobarlo**:

```python
design(EncoderSpec(iex_min=60, gain=0.35, iex_max=180))
# [ERROR] iex_max: pediste 180.0 nA pero con iex_min=60.0 nA y gain=0.350
#         el circuito exige 207.4 nA (-13 %)
```

Aproximar en silencio era el fallo que había que evitar: descubrirlo durante la
caracterización costó dos hipótesis falsas.

## Espacio de diseño

Cuatro variables. `Ld = 1.60 um` y `W9 = 0.26 um` van fijos: se eligieron
midiendo que fijarlos no pierde nada de la región que el LIF usa (100 % de
cobertura) y ahorran área.

| | rango [um] |
|---|---|
| `Wd` ancho del par de entrada | 0.26 – 1.80 |
| `Wl` ancho de las cargas | 0.30 – 2.70 |
| `Ll` largo de las cargas | 0.28 – 0.62 |
| `L9` largo de la cola | 0.80 – 3.78 |

Dos objetivos contra cuatro variables dejan **dos grados de libertad libres**,
que valen un factor 4 en desapareamiento a especificación idéntica. Se gastan
con `tradeoff` (0 = mínima `sigma_Vos`, 1 = mínima área):

```
tradeoff       area    sigma_Vos    iex_min     gain
    0.00   5.126 um2     10.0 mV   100.0 nA   0.3512
    0.50   2.026 um2     20.1 mV   100.1 nA   0.3504
    1.00   1.083 um2     39.6 mV   100.3 nA   0.3493
```

**La palanca del apareamiento es `Ll`, el par de CARGA, no el par de entrada.**
Medido por Monte Carlo con los modelos del PDK: el reflejo habitual de
"agrandar el par de entrada" da 1.7x de mejora; guiarse por la ley medida da
3-4x por la misma área.

## Dimensiones fijadas: los objetivos mandan

Cualquiera de las cuatro puede venir dada. Si estorba para alcanzar el objetivo,
**se libera** — la política del equipo pone los objetivos (prioridad 1) por
encima de las dimensiones fijadas (prioridad 2). Cada liberación se reporta con
su cadena causal:

```python
design(EncoderSpec(iex_min=400, gain=0.30, L9=3.7))
# [WARNING] L9: cambiada de 3.700 a 0.950 um para alcanzar lo pedido
#   cadena: con L9=3.700 fija el mejor alcanzable era 85.3 % de desviacion;
#           liberandola baja a 0.1 %. Se eligio L9 primero porque no interviene
#           ni en la ganancia ni en el desapareamiento
```

El orden de liberación sale de las leyes medidas, no de intuición:

| | por qué |
|---|---|
| 1. `L9` | no interviene ni en la ganancia (exp. 0.03) ni en el desapareamiento (0.03), y no es un par apareado |
| 2. `Wl` | mueve la ganancia pero **no** el desapareamiento (exp. 0.03) |
| 3. `Ll` | mueve la ganancia **y domina** el desapareamiento (exp. −1.07) |
| 4. `Wd` | par apareado de entrada: ganancia, desapareamiento y layout |

Se libera solo lo necesario y se para al alcanzar la tolerancia. Con las cuatro
fijadas y un objetivo incompatible, libera `L9` y `Wl`, llega, y deja `Wd` y `Ll`
como el usuario las puso.

Si no se alcanza ni liberándolo todo, `ERROR` con lo más cercano:

```
[ERROR] objetivos: no alcanzable con las cuatro dimensiones libres:
        iex_min 1721.6 nA de 5000.0 pedidos (-65.6 %);
        gain 0.5676 de 0.3500 pedidos (+62.2 %)
```

## El punto nominal se deriva, no se clava

`design(EncoderSpec())` sin objetivos devuelve el punto **más cómodo de
caracterizar**, que en este proyecto significa lo más lejos posible de los
bordes de la caja — es donde las leyes son de fiar:

| distancia al borde | `lgIa` | `lgIb` |
|---|---|---|
| pegado (<5 %) | 0.79 % | 0.74 % |
| centro (>30 %) | 0.44 % | 0.50 % |

Lo que se guarda es **el criterio**, no el resultado:

```python
NOMINAL_SPEC = {"iex_min": 80.0, "gain": 0.40, "tradeoff": 0.5}
nominal()    # -> {'Wd': 0.725, 'Wl': 0.947, 'Ll': 0.394, 'L9': 1.811}
```

El nominal de la neurona sí son cuatro números clavados, porque el suyo es una
celda medida. El nuestro sale de una búsqueda, así que se deriva: si cambian las
leyes o la caja, el nominal se mueve solo al punto que vuelva a cumplir el
criterio.

Verificado en ngspice: predicho 80.0/286.5 nA G=0.400, medido 79.6/285.4
G=0.401 (−0.5 %, −0.4 %, +0.1 %). Y el criterio se verifica solo: de los tres
diseños de referencia el que peor valida (−2.7 %) es justo el que tiene
`Ll = 0.280`, pegado al borde.

## Precisión

Validación externa de las leyes (fuera de muestra):

| | |
|---|---|
| `Iex(-)` | 0.65 % |
| ganancia | 0.26 % |
| `V(a)` | 0.12 % |
| viabilidad | 1.26 % |
| `sigma_Vos` | 5.6 % |
| `source_ro` | 0.09 % (medio), 0.33 % (peor) |
| `C_in` | 0.73 % |
| `I_ref` (divisor de bias) | 3.15 %; 2.14 % por geometría externa |
| esquinas | 15 % (sobre una deriva de 5x) |

Lazo cerrado del motor, 36 diseños simulados en ngspice (pedido contra
resultado, ambos medidos):

```
iex_min    |error| 1.42 %   peor 3.24 %
ganancia   |error| 0.51 %   peor 2.85 %
24/36 dentro del +-2 %      36/36 dentro del +-5 %
```

El 1.4 % es peor que el 0.65 % de las leyes porque el solver busca los extremos
de la caja, donde la ley tiene menos apoyo. Esa es la cifra que vale para uso
real.

## La cadena, por los dos lados

`NeuronSpec` reporta su `C_in` y acepta `source_ro` y `c_in_max`. El encoder da
las dos magnitudes duales, así que los motores componen:

```python
de = design(EncoderSpec(iex_min=100, gain=0.35))
lo, hi = de.predicted["iex_min [nA]"], de.predicted["iex_max [nA]"]
dn = N.design(N.NeuronSpec(iex_range=(lo, hi), source_ro=source_ro(hi)))
```

```
lo que alimente al encoder debe mover     2.35 fF   (C_in del encoder)
el encoder debe mover                     2.03 fF   (C_in del LIF)
el LIF puede mover hasta                132.00 fF
```

`C_in` depende casi solo de `Wd` (exponente 0.934); el desvío de 1.0 y el
término de `L9` son efecto Miller. Si la cota `c_in_max` llega a morder, el
compromiso real no es capacidad contra área sino **capacidad contra desviación
de entrada**: bajar `C_in` exige reducir `Wd`, que es lo que se paga en
`sigma_Vos` (va con `Wd^-0.44`).

## Lo que este paquete NO resuelve

`Iex` deriva un **factor 5 entre chips** por dispersión de proceso. El diseño se
resuelve siempre en `typical/27C` y la deriva se reporta en `requirements`; no
se corrige, porque no se puede corregir con geometría.

Es un problema de circuito, no de modelado. El divisor de diodos M10/M11 que
genera `Vbias` cubre el 16 % del eje de velocidad del proceso y el 133 % del de
sesgo p/n: mide la magnitud equivocada. Las tres salidas, medidas:

1. **Ajuste de `Vbias` por chip** — residuo 3-13 %. Es lo que funciona hoy.
2. **Referencia con resistencia** — resuelve el proceso (1.12x) pero se lleva
   la temperatura por delante (5.67x). Necesita compensación térmica.
3. **Sistema ratiométrico** — que el umbral del LIF salga de la misma
   referencia. No cuesta pines ni área. Es la vía más prometedora, sin probar.

## Procedencia

Todo en `sch/encoder/results/encoder_knowledge_base.md`. Los coeficientes de
`coeffs.py` los genera `sch/encoder/tb/scripts/gen_coeffs.py` desde los
barridos; no editar a mano.

## Ficheros

| | |
|---|---|
| `spec.py` | `EncoderSpec` / `EncoderDesign` / `Note` / `Severity` |
| `laws.py` | las leyes, con su error medido en el docstring |
| `coeffs.py` | los 146 números. Generado |
| `solver.py` | viabilidad → objetivos → grados de libertad sobrantes |
| `example.py` | `python -m encoder_design.example` |

Sin `check.py` todavía: falta decidir contra qué verifica.
