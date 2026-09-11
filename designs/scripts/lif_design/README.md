# LIF design engine — GF180MCU

Turns an electrical intent into the dimensions of the LIF neuron, and says
what it had to change and why. A tool *for* an AI to use, not an AI: the
input is deterministic and the output is structured data, including the
reason something cannot be done.

```python
from lif_design import NeuronSpec, design

d = design(NeuronSpec(freq_range=(200, 1500), iex_range=(20, 200)))
print(d.report())
```

## The laws

Fitted to ngspice sweeps on GF180MCU, `.tran 1n`. Frequencies are **kHz**,
dimensions **µm**, capacitance **fF**, current **nA**.

| | law | RMS |
|---|---|---|
| frequency | `f = 24837 · W⁻¹·⁰⁷⁶ · L⁻⁰·⁹⁴⁰ · (Iex/100nA)` | 2.03% |
| gain | `k = 280.22 · W⁻¹·⁰⁴⁴⁷ · L⁻⁰·⁹⁹²³` | 2.18% |
| threshold | `Vth = 1.2792 + (−16.83W + 0.4884L + 1.766WL)/Cm` | 1.32% |
| swing | `swing = 4.114 · W⁰·⁹⁵¹ · L¹·⁰⁶⁵ · Cm⁻¹·⁰⁰⁶` | 1.68% |
| oscillation floor | `Cm_min = 8.94 · W¹·⁰³⁸ · L⁰·⁷⁰⁰` | — |
| input capacitance | `C_in = 0.945 + 0.865 · W` | 0.67% |

Externally validated on 18 points outside the fitting grid: frequency error
−0.00% mean, 1.23% RMS.

W and L are M5, the integrator transistor. The inverters (M1–M4) are not
characterised — they are sized as ordinary digital gates.

`C_in` is what the cell presents to whatever drives current into it, on top of
`Cm`. It is a predicted output, never an objective: it depends only on `W_reset`,
and 1.1–4.0 fF across the envelope is too narrow to constrain anything. A
`c_in_max` in the spec is checked, not solved. **It must not be added to `f`** —
the frequency law was fitted on simulations that already include it.

## Validity range

```
W       0.22 … 3.5 µm     above 3.5 the membrane leaves the rail
L       20 … 50 µm        L=60 does not converge
L       ≥ 25 µm           below this, frequency error rises from ~1% to 5–7%
f       ≤ 4500 kHz        the reset does not complete below ~215 ns
Iex     ≥ 5 nA            verified with no degradation; there is no real floor
```

Outside these the laws are extrapolation, and `design()` says so in its notes.

## What does not affect the electrical result

`fingers` and `multipliers` on M5 are a layout decision. Measured on
W=1.08 L=35.42 Cm=141.1 fF: frequency moves ≤0.40% between 1, 2 and 4
fingers, which is inside the cycle-to-cycle spread of the simulation itself
(0.13–0.32%) and well under the laws' own 2.03% RMS.

So the layout picks them for area and routing, and does not have to report
back.

## Resolution layers

`design()` resolves in four passes, and never raises — see `NeuronDesign.notes`:

1. **geometry** — (W, L) from the frequency target
2. **Cm** — from the threshold, floored at `Cm_min`
3. **output buffer** — sized from the load, independent of the rest
4. **validation** — predicts what the design will do, flags what it cannot meet

Design intent wins over fixed dimensions: if a pinned W or L contradicts the
target, the engine adjusts it and emits a WARNING; if the contradiction cannot
be resolved at all, an ERROR with the causal chain.

## Files

```
laws.py     the fitted laws and their inverse solvers
spec.py     NeuronSpec (what you ask) / NeuronDesign (what you get)
solver.py   the four resolution layers
example.py  six runnable cases
```

Verification lives with the testbench, in
`designs/libs/tb_analog/tb_lif/` — it simulates a design and compares the
measurement against the prediction.

Standard library only: `math`, `dataclasses`, `enum`. No numpy — a design is
about fifteen `pow()` calls.
