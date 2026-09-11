# STDP: un nodo partido en dos, y las dos ramas infra-polarizadas

Medido el 2026-09-09 sobre `designs/libs/snn_analog/stdp/stdp_sch.spice` con un
banco de 7 amperímetros. Afecta al `stdp_4x2` que ya está integrado (8 copias).

---

## 1. El bug: `n3` y `n4` deberían ser el mismo nodo

Poniendo las dos mitades en paralelo, el espejo de la depresión pide esto:

```
  DEPRESION                          POTENCIACION (como está)  debería ser
  M9  n5 n5    avss   <- diodo EN n5  M7  n4 n3    avdd        M7 n4 n4 avdd
  M12 n5 vpost vdep   <- switch       M8  n3 nvpre vpot        M8 n4 nvpre vpot
```

Tal como está, **`n3` solo toca la puerta de M7 y el drenador de M8**. Con
`nvpre` en reposo a 3.3 V, M8 está cortado, así que `n3` es un **nodo flotante
sin camino de continua**: deriva de 3.13 a 3.55 V durante la simulación. Y con
`n3 ≈ 3.13` contra `avdd = 3.3`, M7 tiene `|Vgs| = 0.17 V` — cortado. `MCM_1`
arrastra `n4` a tierra y `Ipot` no circula.

Uniendo `n3` y `n4`, M7 queda diodo-conectado (que es el camino de continua que
le falta) y M8 cuelga del mismo nodo que la fuente, igual que M12 abajo.

Medido:

```
                     n4[V]    I_pot[nA]
  como está         0.0000       0.0033
  con n3 = n4       2.4303     224.4575
```

**El LVS no lo detecta**: esquemático y extraído llevan el mismo circuito
incompleto, así que coinciden. Solo se ve simulando el punto de operación.

Encaja con la nota del esquemático (*"replaced by current mirror external to
this subcircuit"*): al sacar los espejos fuera se partió un nodo que debía
seguir unido.

---

## 2. Con eso no basta: las dos ramas necesitan mucha más corriente

El arreglo del nodo pone `Ipot` a circular, pero la traza sigue sin llegar al
umbral. Subiendo `vb_pot`:

```
  n3=n4 + vb_pot     caída de vpot       DVw
            0.755      -119.28 mV     -0.57 mV
            0.95       -404.53 mV     -0.61 mV
            1.10       -784.71 mV     +2.64 mV   <- cruza el umbral
            1.30      -1213.06 mV   +146.76 mV   <- potencia de verdad
```

Y lo mismo en la depresión, con `vb_idep`:

```
  vb_idep   Idep       Vdep0(33ns)   DVw/evento
    2.52     195 nA      0.136 V       -2.88 mV   <- nominal: es todo artefacto
    2.40    1.17 uA      0.414 V         ~ -3 mV
    2.32    2.57 uA      0.767 V       -46.56 mV  <- punto de trabajo bueno
    2.15    7.55 uA      1.048 V      -421.77 mV  <- satura, ventana con meseta
```

La transición es brusca porque la lectura es subumbral: **e-plegado cada 76 mV
de traza**, o sea un factor 180 en tasa de aprendizaje por 600 mV.

---

## 3. Con el bias nominal, el 98.2 % de lo que se mide es inyección de carga

Midiendo el punto donde la respuesta debe valer cero:

```
  DVw(Vdep = 0.00) = -2.832 mV   <- suelo: acoplo por la puerta de M3 a CW
  DVw(Vdep = 0.40) = -2.882 mV   <- lo que da el bias nominal
  -> STDP real = 0.050 mV = 1.8 %
```

Y ese suelo depende **solo del pre**, no del post: es un término **no hebbiano**
que hace derivar el peso con actividad presináptica sola.

Ojo al control: quitar el spike post NO sirve de blanco, porque el post tiene su
propia inyección de carga de **+4.30 mV** en sentido contrario. El control bueno
es **con los dos spikes y `Dt >> tau`**.

`CW` no ayuda: diluye suelo y señal por igual. Con `nCW` de 5 a 40 (factor 8) el
cociente señal/artefacto se queda en 147-149.

---

## 4. Cómo queda la celda arreglada

Con `n3 = n4`, `vb_idep = 2.32` y `vb_pot = 1.30`:

```
     Dt[ns]    senal[mV]        Dt[ns]    senal[mV]
       50.0     -46.5574        3000.0     -28.7330
      200.0     -44.5926        6000.0     -16.9895
     1000.0     -38.9971       11000.0      -5.3787
```

Exponencial con **tau_eff ~ 5.5 us** (el paper da ~5). Amplitud 1.9 % del rango
de peso por evento.

**Cubre el rango de disparo del LIF** (intervalos de 222 ns a 13.5 us) al 96 %
del pico en el extremo rápido y ~10 % en el lento.

Otras dos medidas de la celda:

- **decaimiento**: -10.16 uV/ns medido vs -10.33 predicho de `Itd/Cdep` (-1.7 %).
  El paper da 10 uV/ns para `Itd=1nA, Cdep=100fF`: clavado.
- **lectura del peso**: `Iout` de 0 a 2.35 uA, rango útil `vw` en [0, 2.4] V,
  e **independiente de la carga al 0.11 %** (0 V vs 0.9 V). El `L=15u` de M5
  cumple.

---

## 5. Dos cosas que hay que decidir, no son bugs

**El coste en corriente permanente.** `Idep` no es corriente de evento: el diodo
M9 la quema en reposo. A `vb_idep = 2.32` son **2.57 uA por sinapsis, ~21 uA con
las ocho**, disparen o no. Es el eje de diseño de la celda.

**La polaridad del peso parece invertida.** `M5 iout vw avdd avdd pfet`: subir
`vw` **reduce** `Iout`. Y el camino de potenciación (M1/M2, pfets desde `avdd`)
**sube** `vw`. Medido: la depresión baja `vw` (1.7728 -> 1.7697) y la
potenciación lo sube (+146.76 mV). O sea que **potenciar reduce la salida y
deprimir la aumenta**. Puede ser deliberado — peso guardado invertido y
compensado en cómo la neurona integra `iout` — pero no se puede saber mirando
solo esta celda. ¿Está compensado aguas abajo?

---

## 6. Límite conocido

El suelo de inyección acota la cola útil de la ventana: a `Dt = 11 us` la señal
son 5.38 mV contra 2.83 mV de artefacto (1.9x). La neurona más lenta dispara a
13.5 us, así que **el extremo lento de la ventana cae justo donde el término no
hebbiano empieza a pesar**. Subir `CW` no lo arregla (diluye los dos por igual);
lo que lo movería es reducir el acoplo de puerta de M3/M2, que sí es un cambio
de dimensiones.

---

## 7. Ficheros que no coinciden entre sí

Comparando las tres fuentes de verdad del mismo bloque:

```
              stdp.sch        stdp_lvs.sch    stdp_sch.spice
  fecha       31 jul          7 sep           7 sep
  pequenos    0.22u/0.28u     0.5u/0.63u      0.5u/0.63u
  M5          0.22u/10u       0.5u/15u        0.5u/15u
  M17 (Itp)   0.3u/4.6u       0.3u/4.6u       0.5u/4.6u   <-- DIFIERE
  M7          no existe       si              si
  Itd         no existe       MCM_5..9        MCM_5..9
  M10, M13    existen         no              no
```

**`stdp.sch` está obsoleto** (31 de julio) y es el que lleva el nombre
principal: tiene otra geometría, transistores que ya no existen (M10, M13), le
falta M7 y toda la pila de `Itd`. Quien lo abra creyendo que es el diseño verá
otra celda. El vivo es `stdp_lvs.sch`.

**`stdp_lvs.png` es del 22 de agosto** y se rendirizó desde un estado anterior:
muestra `0.22u/0.28u`. No diseñar leyendo esa imagen.

**Y queda una discrepancia real entre dos ficheros de la MISMA fecha**: `M17`,
la fuente de `Itp`, es `W=0.3u` en el esquemático y `W=0.5u` en el netlist. Un
67 % de diferencia en corriente al mismo bias, o sea un 67 % en `tau+`. Hay que
decidir cuál manda.

Nota: la caracterización se hizo sobre `W=0.5u`, pero **las leyes no se caen
por esto**, porque están expresadas en la CORRIENTE MEDIDA y no en la tensión de
bias (`tau = C*eta*VT/I`). Cambiar la geometría mueve el mapeo `vb -> I`, no la
ley. El barrido cubrió `Itp` de 0.13 a 16.6 nA, así que el rango sigue
alcanzable con otra tensión.
