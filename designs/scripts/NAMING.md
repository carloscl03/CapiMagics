# Naming scheme — devices and engine parameters

**Status: phase 1 applied.** Engine parameters and knowledge bases now use
these names; netlist device names do not yet (see Migration).

## Why

`M1` means four different things across the four cells: half of a comparator in
the LIF, the potentiation trace readout in the STDP, the leak pass device in the
integrator, and nothing at all in the encoder (which uses `xm1`). `M5` is worse:
in the LIF it is the reset switch — the largest device in the cell at 115 µm² —
and in the STDP it was the weight readout, the one whose sign was inverted.

Device numbers are assigned by schematic-entry order. They carry no information
about what the device does, and they actively mislead when the same number
means unrelated things in neighbouring blocks.

## Rules

1. **The name states the function, never the position.**
2. **Same function, same word, across all four cells.** `SRC` is always a
   current source; `SW` is always a switch; `RD` is always a readout.
3. **The two halves of the STDP differ by suffix** (`_DEP` / `_POT`), not by
   number — they are mirror roles and the name should say so.
4. **Engine parameters follow `W_<role>` / `L_<role>`.** The package already
   namespaces them (`encoder_design.laws`), so no cell prefix is needed.
5. English, because the PDK, the tools and the netlists are in English and
   mixing languages inside a netlist is worse than either language alone.

## Vocabulary

| word | meaning |
|---|---|
| `IN` | signal input device |
| `LOAD` | active load |
| `TAIL` | tail current source of a differential pair |
| `BIAS` | bias generation (divider, reference) |
| `SRC` | current source |
| `SW` | switch (gated by a digital signal) |
| `RD` | readout (converts a stored value into current) |
| `WR` | write path (moves charge onto a storage node) |
| `CEIL` | device that sets a clamping level |
| `MIRR` | current mirror device |
| `GM` | transconductor |
| `COMP` | comparator |
| `BUF` | buffer / fan-out |
| `C_` | capacitor |

---

## ENCODER

| now | proposed | function | engine param |
|---|---|---|---|
| `xm1`, `xm2` | `MN_IN_P`, `MN_IN_N` | input differential pair | `W_in`, `L_in` (was `Wd`, `Ld`) |
| `xm3`, `xm4` | `MP_LOAD_P`, `MP_LOAD_N` | active load | `W_load`, `L_load` (was `Wl`, `Ll`) |
| `xm9` | `MN_TAIL` | tail current source | `W_tail`, `L_tail` (was `W9`, `L9`) |
| `xm10` | `MN_BIAS` | bias divider, n side | `W_bias_n`, `L_bias_n` |
| `xm11` | `MP_BIAS` | bias divider, p side | `W_bias_p`, `L_bias_p` |
| `xm8`, `xm5` | `MP_OUT_ON1`, `MP_OUT_ON2` | output copies, **ON** channel | — |
| `xm7`, `xm6` | `MP_OUT_OFF1`, `MP_OUT_OFF2` | output copies, **OFF** channel | — |

The `ON`/`OFF` suffix is measured, not assumed: `Iex_1,2` rise with `Vdif`
(40.8 → 57.0 nA) and `Iex_3,4` fall. The current names hide that completely —
`xm5` and `xm7` look like a pair and have opposite polarity.

## LIF

| now | proposed | function | engine param |
|---|---|---|---|
| `M1`, `M2` | `MP_COMP`, `MN_COMP` | threshold comparator | — |
| `M3`, `M4` | `MP_RSTGEN`, `MN_RSTGEN` | reset pulse generator | — |
| `M7`, `M8` | `MP_BUF`, `MN_BUF` | output buffer (fan-out) | `W_buf` (was `W_M7M8`) |
| `M5` | `MN_RESET` | reset switch | `W_reset`, `L_reset` (was `W_M5`, `L_M5`) |
| `XC2` | `C_MEMBRANE` | membrane capacitor | `C_mem` (was `Cm`) |

`MN_RESET` deserves the explicit name: it is 115 µm², bigger than everything
else in the cell put together, and its geometry sets the frequency through
**channel charge injected at turn-off**, not through conductance — which is why
`f ∝ 1/(W·L)` and not `1/(W/L)`. The `Vth` law carries the same term:
`Vth = 1.2792 + (−16.83·W + 0.4884·L + 1.766·W·L)/Cm`.

## STDP

| now | proposed | function | engine param |
|---|---|---|---|
| `M16` / `MCM_1` | `MP_TRSRC_DEP` / `MN_TRSRC_POT` | trace current source | via `vb_idep` / `vb_pot` |
| `M9` / `M7` | `MN_TRCEIL_DEP` / `MP_TRCEIL_POT` | **ceiling**: sets `n5` / `n4` | — |
| `M12` / `M8` | `MN_TRWR_DEP` / `MP_TRWR_POT` | trace write switch | — |
| `M4` / `M1` | `MN_TRRD_DEP` / `MP_TRRD_POT` | trace readout | `W_trrd_dep` (was `W4`), `W_trrd_pot`, `L_trrd_pot` (was `W1`, `L1`) |
| `M3` / `M2` | `MN_WWR_DEP` / `MP_WWR_POT` | weight write switch | — |
| `MCM_5..9` / `M17` | `MN_DECAY_DEP[1..5]` / `MP_DECAY_POT` | decay current source | via `vb_itd` / `vb_itp` |
| `Mn` | `MN_WOUT_GM` | weight transconductor | — |
| `Mp1`, `Mp2` | `MP_WOUT_MIRR_IN`, `MP_WOUT_MIRR_OUT` | output mirror | `IOUT_MAX` |
| `x1` / `x3` | `C_TRACE_DEP` / `C_TRACE_POT` | trace capacitors | `nCdep` |
| `x2` | `C_WEIGHT` | weight capacitor | `nCW` |

Here the `_DEP` / `_POT` suffix pays for itself: the pairs `M9`/`M7` and
`M4`/`M1` are mirror roles and nothing in the numbers says so. And `n3`/`n4`
being the same node — the bug that stopped potentiation from conducting — would
have been obvious with `MP_TRCEIL_POT` diode-connected to its own drain.

## INTEGRATOR

| now | proposed | function | engine param |
|---|---|---|---|
| `M6` | `MN_INJECT` | spike injection | `W_inj`, `L_inj` (was `W6`, `L6`) |
| `M1` | `MP_LEAK_PASS` | leak pass device from `vm` | `W_leak_pass` (was `W1`) |
| `M2` | `MN_LEAK_MIRR` | leak mirror, set by `Iref` | `W_leak`, `L_leak` (was `W2`, `L2`) |
| `M3` | `MN_REF_DIODE` | reference diode for `Iref` | via `Iref` |
| `XC5` | `C_INTEG` | integrating capacitor | `C` |

`C_INTEG` and not `C_MEM`: the LIF already has a `C_MEMBRANE` and they do
different jobs — one is a neuron membrane that resets every spike, the other
holds a rate estimate for milliseconds.

---

## Migration

**Engine parameters and knowledge bases first.** That is where a human or an AI
reads, and renaming there breaks nothing outside this repository.

**Netlist device names are a separate decision.** Renaming them breaks LVS
against the team's xschem schematics until those are updated too, so it needs
their agreement. Until then this document is the mapping table.

The two halves must not drift: if a device is renamed in the netlist, the engine
parameter and the KB entry change in the same commit.

### Exception: `Cm`

`Cm` keeps its name. It is not a device number but the standard notation for
membrane capacitance, and renaming it would touch 84 places for no gain.

### What phase 1 changed

```
  lif_design         W_M5 -> W_reset      L_M5 -> L_reset      W_M7M8 -> W_buf
  encoder_design     Wd -> W_in           Wl -> W_load         W9 -> W_tail
                     Ld -> L_in           Ll -> L_load         L9 -> L_tail
  integrator_design  W6 -> W_inj          W1 -> W_leakpass     W2 -> W_leak
                     L6 -> L_inj                               L2 -> L_leak
  stdp_design        W4 -> W_trrd_dep     W1 -> W_trrd_pot     L1 -> L_trrd_pot
```

`W1` was the worst case: it meant the integrator's leak pass device **and** the
STDP's potentiation trace readout. Two packages, two unrelated jobs, one name.
