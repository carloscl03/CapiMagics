# LIF Neuron — Design Knowledge Base

Empirical characterization of the LIF neuron (GF180MCU, 7T) mapping **design
parameters to behaviour**. Every number here comes from ngspice transient
simulation with multi-cycle period averaging.

Cell under test: [`../neurona_input_current.sch`](../neurona_input_current.sch).
Current input — the cell receives `Iex` directly, so it carries no input mirror.

Reference point: `W_reset = 1.25 µm`, `L_reset = 50 µm`, `Cm = 150 fF`, inverters at
PDK minimum (`W/L = 0.22/0.28 µm`).

> **Simulation settings are not a detail.** Use `.tran 1n` and a transient long
> enough for ≥5 cycles. Coarse settings produced two separate false results
> during this work — see [Methodology](#6-methodology-two-costly-artifacts).

---

## 1. The design laws

Six laws describe the cell. All were fitted on `.tran 1n` data and validated
against points outside the fitting grid.

### Frequency

```math
f[\text{kHz}] = 24837 \cdot W_{M5}^{-1.076} \cdot L_{M5}^{-0.940} \cdot \frac{I_{ex}}{100\,\text{nA}}
```

RMS 2.03% over 69 points. **`Cm` does not appear** — adding it to the fit makes
it worse. Verified across 8 series: `f` varies less than 4% while `Cm` triples.

| Cm (W=1.75, L=41) | 280 f | 388 f | 561 f | 864 f |
|---|---|---|---|---|
| f [kHz] | 414.2 | 411.6 | 410.3 | 411.5 |

The relation to current is **proportional, with no intercept** (see
[§4](#4-corrections-to-earlier-conclusions)).

### Modulation gain

```math
k[\text{kHz/nA}] = 280.22 \cdot W_{M5}^{-1.0447} \cdot L_{M5}^{-0.9923}
```

RMS 2.18%, worst case 4.9%, over 9 configurations. This is the slope a designer
actually needs: an input current *range* maps to an output frequency *range*.

Known bias: `k` has curvature — the slope falls as current rises (13.33 → 10.47
kHz/nA within one series). At the low end the real gain is **~11.6% higher**
than this law (measured 16.41 vs 14.51 at 5–10 nA for W=0.5, L=41).

### Threshold

```math
V_{th}[\text{V}] = 1.2792 + \frac{-16.83\,W_{M5} + 0.4884\,L_{M5} + 1.766\,W_{M5}L_{M5}}{C_m}
```

RMS 1.32%. **Orthogonal to `Iex`**: varies under 1.2% while current changes 16×.
The cross term is required — dropping the linear terms drops R² to 0.806.

### Membrane swing

```math
\text{swing}[\text{V}] = 4.114 \cdot W_{M5}^{0.951} \cdot L_{M5}^{1.065} \cdot C_m^{-1.006}
```

RMS 1.68%. The exponents land on (+1, +1, −1), so this is `W·L/Cm` — coupled
charge over capacitance. Physics, not curve fitting.

### Minimum capacitance

```math
C_{m,min}[\text{fF}] = 8.94 \cdot W_{M5}^{1.038} \cdot L_{M5}^{0.700}
```

Below this the membrane swings outside the rails and the cell misbehaves.
Conservative by 10–25%: measured boundaries sit at 0.75–0.93× the predicted
value across four configurations.

### Output stage

```math
C_{load,max}[\text{fF}] \approx 600 \cdot W_{M7M8}[\mu\text{m}] \qquad
I_{drive}[\mu\text{A}] \approx 85 \cdot W_{M7M8}
```

Criterion: fall time ≤ 5 ns. **Load does not feed back into the loop** —
frequency shifts under 0.7% with `C_load` from 0 to 1600 fF.

The inverter is balanced: pull-up (M7) matches pull-down (M8) at equal W, so
the spike is symmetric. Drive is independent of everything else — re-measured at
`L_reset = 25 µm` it gives 84.97 vs 85.07 µA/µm, under 1% apart.

### Input capacitance

```math
C_{in}[\text{fF}] = 0.945 + 0.865 \cdot W_{M5}[\mu\text{m}]
```

Measured as `C_total − Cm`, where `C_total = Iex / (dV/dt)` on the integration
ramp — the current source charging the node *is* the measurement. LOO 0.67%
RMS, external validation 0.56% RMS on a disjoint grid.

**Affine, not a power law**, for the same reason as `Vth`: there is a physical
constant term. The 0.945 is the M1/M2 gate pair, which hangs off the node even
at minimum M5; the `0.865·W` is M5's drain junction. A pure power law is forced
through the origin and misses by −21% at `W = 0.22`. Only `W` enters — four
pairs of `L` measured, under 1.5% apart.

**Do not use it to correct `f`.** The frequency law was fitted on full-circuit
simulations that already contain this `C_in`; adding it again double-counts.
Its uses are the interface contract (this is the `c_load` the previous stage
must drive) and as the baseline against which layout interconnect parasitics
are measured once the GDS is extracted.

`C_in` is the dual of `c_load`: our `c_load` is the next cell's `C_in`, and our
`C_in` is the previous cell's `c_load`. In the design system it is a *predicted
output*, never an objective — a `cin_max` in the spec is checked, not solved,
because 1.1–4.0 fF over the whole envelope is too narrow a band for the
constraint to ever bind.

---

## 2. Structure of the design space

Three properties that are not obvious from the schematic.

### `Cm` is not a frequency knob

It sets **threshold and swing**, nothing else. This breaks what would otherwise
be a circular dependency and makes the whole design problem solvable by direct
substitution — no iteration.

### Frequency and threshold are physically coupled

```
f low  →  W·L large  →  Cm_min large  →  Cm large  →  Vth low
```

So a slow neuron cannot have a high threshold. Measured ceiling:

| f target | max Vth |
|---|---|
| 200 kHz | 1.81 V |
| 500 kHz | 1.91 V |
| 1000 kHz | 2.04 V |
| 3000 kHz | 2.53 V |

Validated by simulation at three frequencies: predicted vs measured `Vth` at the
boundary agrees to −0.5% … −2.9%.

### One degree of freedom

For a given frequency there are ~200 valid `(W, L)` pairs — the iso-frequency
curve. Since the exponents are close (−1.076 vs −0.940), `W·L` is roughly
constant along it. That freedom is what a design system spends on a secondary
criterion: area, validity margin, or maximum achievable `Vth`.

### Coupling matrix

| Knob | frequency | threshold | notes |
|---|---|---|---|
| `Iex` | primary, linear | **<1.2%** | the only clean knob |
| `W_reset` | strong, `∝W^-1.08` | strong, via `W·L` | first order on both |
| `L_reset` | strong, `∝L^-0.94` | moderate | |
| `Cm` | **none** | primary | sets swing too |
| `W_buf` | none | none | fan-out only |

---

## 3. Operating limits

Measured, not assumed. Values marked ✅ have a directly measured boundary.

| Parameter | Limit | What happens outside |
|---|---|---|
| `f` | **≤ ~4500 kHz** ✅ | reset does not complete; period floor ~215 ns |
| `W_reset` | **≤ 3.5 µm** ✅ | at 4.0 µm `Vm_min` = −0.058 V; depends on `Cm` |
| `W_reset` | ≥ 0.22 µm | PDK minimum |
| `L_reset` | **≤ 50 µm** ✅ | L=60 does not converge |
| `L_reset` | ≥ 20 µm ✅ | below 25 µm the frequency error rises to 5–7% |
| `Cm` | ≥ `Cm_min(W,L)` ✅ | membrane leaves the rails |
| `Cm` | ≥ 50 fF | the `Vth` law diverges (at 25 fF it predicts 5.83 V > VDD) |
| `Iex` | **no floor** ✅ | verified down to 5 nA with constant gain and swing |

The frequency ceiling is a **period** limit, not a current one: three
configurations died at 350, 500 and 600 nA but all around 4400–4600 kHz.

Two checks any design flow must perform:

1. `Vth < VDD` — the `.../Cm` form has no ceiling, but physics does.
2. `Cm > Cm_min(W,L)` — the constraint that couples W, L and Cm, and the one
   most often violated when asking for a low threshold.

### Source impedance — the strictest requirement

The current source feeding the cell needs a very high output impedance. A finite
`ro` injects parasitic current proportional to the drop across it, and the
membrane node swings ~1.9 V below VDD:

```math
r_o \geq \frac{1.9\,\text{V}}{\text{tol} \cdot I_{ex}} \qquad\Rightarrow\qquad r_o[\text{G}\Omega] \geq \frac{190}{I_{ex}[\text{nA}]} \;\text{ for } 1\%
```

Measured at 100 nA (W=1.0, L=41, Cm=200 fF):

| `ro` | frequency | deviation |
|---|---|---|
| ∞ (ideal) | 758.2 kHz | — |
| 1 GΩ | 775.2 | +2.2% |
| 100 MΩ | 930.5 | +22.7% |
| 30 MΩ | 1325.9 | +74.9% |
| 10 MΩ | 2404.6 | +217% |
| 3 MΩ | — | **stops oscillating** |

**A simple mirror (1–10 MΩ) is not enough** — a cascode or a long-channel device
is required. Low currents are the demanding case: at 25 nA even 1 GΩ gives 9.2%
error.

---

## 4. Corrections to earlier conclusions

Findings reported during this work and later proved wrong. Kept because the
reasoning matters more than the conclusions.

| Earlier claim | Reality |
|---|---|
| "`Cm` raises frequency up to +79%" | flat in `Cm` (<4%); the effect was a timestep artifact |
| "Jitter of 30–55% limits the design" | numerical, not physical; vanishes at 1 ns |
| "`Iex` has a floor from M5 leakage" | no floor; verified to 5 nA. Short-window artifact |
| "`f` saturates above W=2.5 µm" | it does not saturate — the circuit breaks (membrane leaves the rail) |
| "`f = k·Iex + f₀` with f₀ = 14–144 kHz" | **f₀ = 0**. The intercept was an artifact of fitting far from the origin |

The `f₀` case is instructive. Fitting straight lines over 25–400 nA produced
intercepts of 14–144 kHz. Measuring directly at 5 and 10 nA gives
**f₀ = +0.57 kHz** — zero. Extrapolating the intercept-bearing line downward
fails badly:

| Iex | line with f₀ | proportional | measured |
|---|---|---|---|
| 5 nA | 129.2 (+56%) | 79.8 (−3.4%) | 82.6 |
| 10 nA | 204.7 (+24%) | 159.6 (−3.1%) | 164.6 |

An intercept fitted far from the origin absorbs curvature from the high end.

---

## 5. Validation

### External validation — 18 points no law had seen

Grid deliberately disjoint from the fitting grid: `W ∈ {0.75, 1.4, 2.1}` ×
`L ∈ {33, 50}`, where the fit used `W ∈ {0.5, 1.0, 1.75, 2.5}` × `L ∈ {25, 41}`.
`L = 50 µm` also sits outside the fitted range, testing extrapolation.

| Law | mean error | RMS | max |
|---|---|---|---|
| `f` | −0.00% | 1.23% | 2.59% |
| `Vth` | −0.63% | 0.90% | 1.61% |
| `swing` | −0.58% | 1.11% | 1.88% |
| `C_in` | +0.40% | 0.56% | 0.98% |

`C_in` used the same grids plus two points at `W = 0.3` and `W = 0.22`, below
the fitting grid's lower edge of 0.5 — a 2.3× extrapolation. The affine law
held there (−0.06%, +0.98%) while a power law fitted on the same points
collapsed (−14%, −21%). Note that this 0.56% measures the law on the surface
`Cm = 2·Cm_min(W,L)`, where both grids live; off that surface it deviates up to
15%. The number that bounds the deliverable is 0.15% of frequency — see
section 8.

Extrapolation-only subset (L=50): −1.08%, −1.04%, +0.11%. **The laws do not
break outside their fitting range**, and the LOO estimate of 3.1% turned out
conservative.

The `Iex` law from the previous voltage-input topology was re-measured at 1 ns
and holds to **0.07% RMS**:
`Iex[nA] = 169.1·(2.571 − Vin)²`. It now describes a block that lives *outside*
the cell, kept here as a reference for whoever designs the input stage.

### Design-loop validation

Three designs generated by the design system, then simulated. Two use
geometries that appear in no characterization grid:

| design | W | L | Cm | f predicted | f measured | error |
|---|---|---|---|---|---|---|
| nominal | 1.25 | 50.0 | 150 | 494.1 | 500.9 | −1.4% |
| fast | 0.602 | 35.42 | 76.9 | 1499.5 | 1491.6 | +0.5% |
| slow | 2.835 | 40.42 | 421.6 | 250.0 | 252.5 | −1.0% |

Worst error across all three quantities: **2.5%**.

### Refitting with the full dataset changes nothing

Refitting on all 69 clean points (13 W levels, 8 L levels) gives
`f = 23872·W^-1.0729·L^-0.9285`, improving RMS from 2.07% to 2.03% — 0.04
points. The published coefficients stand.

> **Methodological warning.** A 1-D slice at fixed `W = 1.0` gave an `L`
> exponent of −0.871 against the law's −0.940, which looked like a 7.3% error.
> The global fit over 69 points gives −0.9285. An exponent measured on a slice
> is not comparable to one from a multivariate fit — the slice absorbs
> correlations between variables.

---

## 6. Methodology: two costly artifacts

Both looked physical. Both were instrumental.

### Transient timestep

`.tran 20n` **overestimates frequency by +41% on average and up to +193%**: the
integrator skips cycles and counts them as spikes. It also produces apparent
jitter of up to 55% that does not exist.

Verified by re-simulating five configurations at 20/5/1 ns — all jitter
disappears at 1 ns:

| W | L | Cm | @20 ns | @5 ns | @1 ns |
|---|---|---|---|---|---|
| 2.5 | 25 | 884 | 54.5% | 2.7% | **0.0%** |
| 1.75 | 25 | 612 | 47.1% | 2.2% | **0.0%** |
| 0.5 | 41 | 106 | 9.3% | 5.1% | **0.5%** |

The bias is systematic and upward, so a high R² offers no protection: fits on
coarse data reached R² = 0.93–0.99 while describing an artifact.

### Transient length

With `tstop = 30 µs`, a neuron at 15 kHz (67 µs period) completes **no full
cycle**, and a cycle-count criterion flags it as non-oscillating. This produced
the phantom current floor. The frequency was scaling perfectly linearly the
whole time (30/40/50 nA → 89.9/119.6/149.3 kHz, k = 3.00 constant).

**Rule for future sweeps:** step ≤ 1 ns, transient sized for ≥5 cycles at the
*expected* frequency, and jitter recorded as a CSV column with a `NOCONV` flag
above 2%.

### Parallelism does not help

`bench_par.sh` measured that ngspice already uses 7.3 of 8 cores with a single
process. Two processes in parallel push each simulation from ~100 s to >660 s
through cache contention. **Run sweeps serially.**

---

## 7. Reference data

| File | Contents |
|---|---|
| `sweep_3d_fine.csv` | 32 pts, W×L×Cm at 1 ns — the main fitting set |
| `verify_laws.csv` | 18 pts outside the fitting grid — external validation |
| `sweep_extremes.csv` | 36 pts at the edges — operating boundaries |
| `sweep_gain_isrc.csv` | 45 pts — modulation gain `k(W,L)` |
| `sweep_zsource.csv` | 28 pts — source impedance sensitivity |
| `sweep_drive_load_isrc.csv` | 24 pts — output load capability |
| `validate_feasibility.csv` | 17 pts — the (f, Vth) feasibility map |
| `sweep_iexwindow.csv`, `sweep_iexmin.csv` | current window |
| `sweep_3d_wlcm.csv` | 32 pts at 20 ns — **biased**, kept as evidence |

Scripts that produced them: [`../tb/scripts/`](../tb/scripts/).
Design system that consumes them: [`../design/`](../design/).

---

## 8. Not characterized

- **Power consumption.** Not a design variable for now.
- **Process corners and temperature.** Everything here is typical at 27 °C.
  Marked as future work.
- **Inverter sizing (M1–M4).** Fixed at PDK minimum; mapping them would add
  another degree of freedom.
- **Resistive output load.** The STDP synapse presents MOS gates (capacitive
  only), so this was not needed — but it would matter for a different load.

### Open lead: `C_in` also depends on the swing

`C_in = 0.945 + 0.865·W` has structured residuals. At fixed geometry, sweeping
`Cm` moves `C_in` — but the exponent is `+0.098` at `W = 0.5` and `−0.023` at
`W = 2.5`. **Opposite signs**, so no separable `C_in = a(1+bW)·Cm^c` exists.

Sorting every point by membrane swing instead of by geometry collapses them
onto one curve. With `g = C_in − 0.865·W`:

| swing [V] | 0.141 | 0.242 | 0.425 | 0.463 | 0.486 | 0.587 | 0.720 | 0.797 | 0.976 | 1.282 |
|---|---|---|---|---|---|---|---|---|---|---|
| `g` | 1.188 | **0.818** | 1.018 | 1.030 | 0.968 | 1.010 | 0.977 | 0.957 | 0.918 | 0.878 |
| `W` | 0.5 | 2.5 | 0.5 | 0.22 | 2.5 | 0.22 | 0.35 | 0.35 | 2.5 | 0.5 |

Nine of ten points, from four `W` values spanning 11×, lie on a single
monotone curve — more swing, less `C_in`. It predicted two fresh points to
0.1% and 0.2%. The mechanism fits: `g` is the M1/M2 gate capacitance, strongly
voltage-dependent, averaged over the window the membrane traverses — and the
swing *is* that window. Since `swing = 4.114·W^0.951·L^1.065·Cm^-1.006`, what
looked like separate `Cm` and `L` dependences are one variable seen twice.

The bold point (`W = 2.5`, `Cm = 1200`) misses by 26% and is unexplained. Its
voltage window is nearly identical to a point that fits, so window position
does not account for it.

**Deliberately not modelled.** The residual reaches 15% of `C_in` in the
large-`Cm`/small-`W` corner, but `C_in` only carries weight when `Cm` is small,
and there the law is accurate. The product stays under **0.15% of frequency**
across the entire space the solver reaches — eight times below the frequency
law's own 1.23% RMS. Refining a correction far below the error of what it
corrects buys nothing.

Worth reopening if M1/M2 are ever sized (the 0.945 term *is* those gates, so
the law would need refitting, not refining), if `CM_FLOOR` drops well below
50 fF, or to publish the mechanism.

---

## Consumo de corriente (2026-09-02)

Medido sobre la celda v3 del equipo (`W_reset=2.3, L_reset=50, Cm=280 fF,
inversores W=0.5/0.28`), promediando `i(vdd)` en transitorio:

    Iex [nA]    f [kHz]    I media [nA]    de la cual Iex
        50         143        14604              0 %
       100         250        13656              1 %
       300         786        15504              2 %

**La neurona consume ~14.6 uA para procesar 50 nA de entrada** -- 290 veces lo
que le entra, y el consumo apenas depende de `Iex`.

### Es la corriente de cortocircuito del inversor de entrada

Barrido DC del inversor M1/M2 solo, en funcion de la tension de membrana:

    Vin [V]    I [nA]      salida
      0.50        270        3.30
      1.00      22815        2.98
      1.32      43200 <-pico
      1.65      29591        0.19
      2.00      14242        0.07
      2.50       1096        0.00
      3.00          0        0.00

    conduce por encima del 10 % del pico entre 0.70 y 2.32 V: ventana de 1620 mV

La membrana recorre de 0 a ~2.1 V en cada ciclo, **despacio**, asi que atraviesa
esa ventana entera en cada disparo. No hay transicion rapida que limite el
cortocircuito: el inversor conduce casi todo el tiempo.

Comprobacion: integrando la curva DC sobre el recorrido de la membrana salen
17.4 uA de media, contra los 14.6 uA medidos en la celda completa. Cierra (la
diferencia es que la membrana no pasa el mismo tiempo en cada tension y el
reset es rapido).

Es el problema clasico de usar un inversor como comparador con una entrada
lenta. Se ataca limitando la corriente del inversor (un transistor de
estrangulamiento en serie) o con un comparador con histeresis.

**AVISO sobre el compromiso**: estrangular el inversor ralentiza su transicion,
y `F_MAX = 4500 kHz` ya esta limitado por que "el reset no completa". Bajar el
consumo por esta via se paga en frecuencia maxima. Hay que medirlo, no
despejarlo.

### En contexto de chip

    NEURONA        14600 nA     95 % del total
    ENCODER         2934 nA     (compartido entre 4 neuronas -> 733 nA c/u)
    INTEGRADOR        50 nA     (25 el mejorado)

El encoder, ademas, entrega 180 nA de los 2934 que consume (6.1 % de
eficiencia): el 94 % se va en la etapa diferencial porque el espejo de salida
divide 1:7.6. Subir `W8/L8` para acercar la relacion a 1 bajaria su consumo
~5x, y de paso mejoraria su impedancia de salida (que va con `Wo^1.11` y se
queda corta por encima de 126 nA). Una sola dimension arreglando dos
problemas -- pero cambia el `Iex` entregado, asi que el motor tendria que
reajustar el resto.
