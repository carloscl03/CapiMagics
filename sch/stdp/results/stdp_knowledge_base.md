# STDP — caracterización

Medido sobre `designs/libs/snn_analog/stdp/stdp_sch.spice` (gf180mcuD, ngspice),
septiembre 2026. **10.741 puntos** repartidos en 25 ficheros `.npz` en esta
carpeta; los bancos que los generan están en `../tb/scripts/`.

Mismo método que `../../encoder/results/encoder_knowledge_base.md` y
`../../integrator/results/integrator_knowledge_base.md`.

---

## 0. Lo primero: hay un bug de netlist

**`n3` y `n4` deberían ser el mismo nodo.** Poniendo las dos mitades en paralelo,
el espejo de la depresión pide:

```
  DEPRESION                          POTENCIACION (como está)   debería ser
  M9  n5 n5    avss   <- diodo       M7  n4 n3    avdd          M7 n4 n4 avdd
  M12 n5 vpost vdep   <- switch      M8  n3 nvpre vpot          M8 n4 nvpre vpot
```

Tal como está, `n3` solo toca la puerta de M7 y el drenador de M8. Con `nvpre`
en reposo a 3.3 V, M8 está cortado: **`n3` es un nodo flotante sin camino de
continua**, deriva de 3.13 a 3.55 V, M7 queda a 0.17 V de `Vgs` — cortado — y
`MCM_1` arrastra `n4` a tierra.

```
                     n4[V]    I_pot[nA]
  como está         0.0000       0.0033
  con n3 = n4       2.4303     224.4575
```

**El LVS no lo detecta**: esquemático y extraído llevan el mismo circuito
incompleto. Solo se ve simulando el punto de operación. El `stdp_4x2` integrado
lleva 8 copias.

Toda la caracterización de este documento está hecha sobre el netlist arreglado
(renombrando `n3` → `n4`; ver `carac_stdp.corto_n3n4`).

---

## 1. Qué implementaron

La **Fig. 2(a)** del paper `12_685.pdf` — 12 transistores, STDP **aditivo**. NO
la Fig. 4 (21 transistores, con decaimiento `Itar` y dependencia del peso
`VW0`). No hay `vb_itar` ni `VW0` en los puertos.

`Cdep` = 109 fF (2 unitcap de 5×5 µm), `CW` = 545 fF (10), `Cpot` = 109 fF (2).

---

## 2. El banco

Siete amperímetros (fuentes de 0 V) en cada eslabón de la cadena causal:

```
  Idep -> Vdep0 -> decae con Itd -> Vdep(tpre) -> I_stdp -> DVw -> Iout
```

```
  VAM_dep   M16 -> n5          la Idep TOTAL
  VAM_c     M12 -> vdep        la fraccion que CARGA Cdep
  VAM_cp    M8  -> vpot        el espejo
  VAM_td    la pila de Itd
  VAM_tp    M17
  VAM_sd    M3 -> vw           el nucleo, depresion
  VAM_sp    M2 -> vw           el nucleo, potenciacion
```

**El amperímetro va en la rama que hace el trabajo, no aguas arriba de un
reparto.** Con el de M16 el balance de carga daba +40.1 %, porque el diodo M9 se
lleva ~40 % de `Idep` en reposo. Movido a M12: +0.3 %.

### Guardas del banco

```
  arranco_bien(d)        rechaza el punto si vw(0) != 1.65
  guarda de excitacion   revienta si vpre/vpost/nvpre/nvpost no tienen fuente
  balance de carga       Q/C contra la tension medida, en cada punto
  medida en blanco       estimulo nulo, donde la respuesta DEBE valer cero
  test de aceptacion     cada banco nuevo reproduce una medida anterior
```

El último ha cazado, en una sola sesión: un amperímetro mal puesto, un `.ic`
ignorado en silencio, cuatro nodos sin excitar, y una ventana de ajuste mal
declarada.

---

## 3. Las leyes

### 3.1 Amplitud de la traza — `L1_dep.npz`, `L1_pot.npz` (160 + 160)

**SATURA con la anchura del pulso**, meseta desde ~50 ns:

```
  Dtp[ns]    20      33      50     100     200
  Vdep0   1.0107  1.0482  1.0505  1.0506  1.0506
```

La amplitud NO la limita la carga, pero tampoco `Vpost − Vth` como escribí en
la primera versión de este documento. **El techo es `n5`**: la traza carga hasta
igualarlo y ahí M12 se queda con `Vds = 0` y deja de conducir. Equilibrio de
carga, no limitación por umbral.

Medido barriendo M12 en 5×5 geometrías (`m12.npz`): la meseta vale **0.8712 V en
las veinticinco**, idéntica a cuatro decimales, y ese valor es exactamente el
`n5` medido en el `.op` (0.8713 V). La ley `Q = Idep·Dtp` del paper no vale aquí.

Reparto de papeles:

```
  M9   fija n5, o sea EL TECHO          (0.5679 a 0.8793 V en su rejilla)
  M12  fija la VELOCIDAD para llegar    (83.8 % a 96.4 % del techo en 33 ns)
```

**Consecuencia: el spike de 33 ns del LIF basta.** Lo que faltaba era corriente.

Balance de carga: mediana −0.02 % (dep), +0.55 % (pot).

### 3.2 Decaimiento — `L2_dep.npz`, `L2_pot.npz` (15 + 15)

```
  pendiente = Itd / Cdep      con Itd medida en la ENTRADA de la pila
```

Medido −10.16 µV/ns contra −10.33 predicho: **−1.7 %**. El paper da 10 µV/ns
para `Itd = 1 nA, Cdep = 100 fF` — clavado.

**NO hay fuga, y no hay suelo en `Itd`.** La primera versión de este documento
reportaba ~20 pA de fuga parásita y un suelo a `Itd ≈ 0.4 nA` por debajo del
cual `tau⁻` no se podría alargar. Las dos cosas eran un artefacto del
instrumento: `VAM_td` estaba en `MCM_9`, o sea en el **fondo** de la pila de
cinco, y los cuatro nodos intermedios se llevan corriente por sus uniones.

```
  entra por arriba (vdep -> MCM_5)   138.74 pA
  sale por abajo   (MCM_9 -> avss)   115.35 pA      20.3 % de diferencia

  exceso con el amperimetro de ABAJO   26.26 pA     <- la "fuga"
  exceso con el de ARRIBA               2.87 pA     <- de los cuales 1.5 son
                                                       el rshunt del banco
```

Con el amperímetro en la entrada, el balance cierra al 1 %.

**Regla, ampliada:** el amperímetro no va solo en la rama que hace el trabajo,
sino **en el extremo por donde la corriente entra al nodo que estás midiendo**.
Es la tercera vez que el mismo error aparece en esta celda (M16 aguas arriba del
diodo M9, MCM_1 aguas arriba de M7, y MCM_9 en el extremo equivocado de la
pila). Las tres las cazó el balance de carga; ninguna la habría cazado un error
de validación.

### 3.3 El núcleo `DVw(Vdep)` — `L3_dep.npz`, `L3_pot.npz` (60 + 60)

Exponencial subumbral más un suelo aditivo:

```
  e-plegado    73.9 mV de traza (depresion)    138.0 mV (potenciacion)
  suelo        escala como 1/CW exacto (el producto suelo*nCW varia 8 % en 8x)
```

Un **factor 180 en tasa de aprendizaje por 600 mV de traza**. Esa sensibilidad
es el problema de robustez de la celda.

### 3.4 El suelo es un término NO HEBBIANO

Con el bias nominal:

```
  DVw(Vdep = 0.00) = -2.832 mV   <- suelo: acoplo de puerta de M3 a CW
  DVw(Vdep = 0.40) = -2.882 mV   <- lo que da vb_idep = 2.52
  -> STDP real = 0.050 mV = 1.8 % de lo medido
```

**El 98.2 % era artefacto.** Y depende **solo del pre**, no del post: hace derivar
el peso con actividad presináptica sola.

**El control correcto son los dos spikes con `Dt >> tau`**, no quitar el post —
el post tiene su propia inyección de **+4.30 mV** en sentido contrario.

`CW` no ayuda: diluye suelo y señal por igual (cociente 147–149 con `nCW` de 5 a 40).

### 3.5 Lectura del peso — `barD`

`Iout` de 0 a 2.35 µA, rango útil `vw` ∈ [0, 2.4] V, corte a 2.7. Pendiente
677 nA/V en `vw = 1.65`. **Independiente de la carga al 0.11 %** (0 V vs 0.9 V):
el `L = 15u` de M5 cumple.

### 3.6 La ventana completa — `barE_2p32.npz`

Con `n3 = n4`, `vb_idep = 2.32`, `vb_pot = 1.30`:

```
     Dt[ns]   senal[mV]      Dt[ns]   senal[mV]
       50.0    -46.5574      3000.0    -28.7330
      200.0    -44.5926      6000.0    -16.9895
     1000.0    -38.9971     11000.0     -5.3787
```

Exponencial con **tau_eff ≈ 5.5 µs** (el paper da ~5). Amplitud 1.9 % del rango
de peso por evento.

**Cobertura frente al LIF — corregido.** La primera versión decía que cubría el
rango entero, con "intervalos de 222 ns a 13.5 µs". Ese 13.5 µs salía de una
`f_min` de 74 kHz que no corresponde a ninguna celda: el motor del LIF da
**24.7–4500 kHz para la v2 y 12.8–4500 para la v3** (la del equipo, con `W_M5`
de 2.3 µm; `Cm` NO interviene en la frecuencia, verificado de 280 a 864 fF).

```
  v3:  12.8 a 4500 kHz   ->  intervalos de 222 ns a 78 us
  ventana al 10 % del pico con tau = 5.5 us  ->  Dt = 12.7 us  ->  f > 79 kHz
  cubierto de verdad: 79 a 4500 kHz, 1.75 decadas de las 2.55 que hace la neurona
```

**Pero se estira, y solo gracias a la correccion de la fuga (§3.2).** Para
cubrir hasta 12.8 kHz al 10 % hace falta `tau = 78/ln(10) = 34 us`, o sea
`Itd = 73.9 mV/34 us * Cdep = 0.24 nA`. Con el suelo de 0.4 nA que yo habia
reportado eso era inalcanzable; al resultar que ese suelo era el amperimetro en
el extremo equivocado de la pila, el impedimento desaparece. El barrido llega a
0.115 nA, asi que 0.24 esta medido.

Aviso: con `Vdep0` por encima del umbral (`vb_idep = 2.15`) la ventana sale
**con meseta** en vez de exponencial. Amplitud y forma compiten.

---

## 4. Las fuentes de corriente — `dev_nfet.npz`, `dev_pfet.npz` (4300 + 4300)

**No hay espejos**: el bias es una tensión de puerta. Así que hace falta
`I(Vgs, Vds, W, L)`, una ley por tipo de transistor; las cuatro fuentes de la
celda son ese mismo dispositivo evaluado en cuatro puntos.

Contrastado contra la celda: **razón 1.0000** (nfet, MCM_1) con el punto de
rejilla cayendo exacto.

### 4.1 El colapso a `W/L` FALLA

```
  razon max/min de I*L/W a igual (Vgs, Vds)
                todas   sin L=0.35   solo L>=1.6
  nfet Vds 3.0   1.75       1.32        1.23
  pfet Vds 3.0   2.76       1.47        1.27
```

Sería 1.00 si `I` dependiera solo del cociente. **`W` y `L` son dos variables**, y
ni con canales largos baja del 21–27 % residual. Empeora con `Vds`, o sea que la
modulación de canal también depende de `W`.

### 4.2 Sensibilidad al bias, que es la robustez del sistema

```
  fuente   e-plegado   sensibilidad
  Idep      110.0 mV     0.91 %/mV
  Ipot      267.5 mV     0.37 %/mV
  Itd        53.3 mV     1.89 %/mV     <- subumbral: n*VT
  Itp        49.5 mV     2.04 %/mV     <- idem
```

Encadenando con el núcleo:

```
  1 mV en vb_idep  =  3.4 % de tasa de aprendizaje   (50 mV -> factor 5.2)
  1 mV en vb_itd   =  1.9 % de ventana tau-          (10 mV -> 21 %)
```

Sin espejo, esos `vb` son tensiones analógicas repartidas a las ocho sinapsis:
**cualquier caída IR o gradiente térmico entra directo**.

### 4.3 A corriente objetivo fija, qué geometría deriva menos

```
  Idep 2.57 uA    hoy W=10.2 L=2.8  -> 0.90 %/mV  |  W=2.00 L=2.80 -> 0.37 %/mV
  Ipot 5.00 uA    hoy W=0.61 L=2.8  -> 0.50 %/mV  |  W=0.80 L=6.00 -> 0.23 %/mV
  Itd  1.1 nA     toda la rejilla entre 2.35 y 2.61 %/mV -> NO HAY MARGEN
  Itp  2.0 nA     toda la rejilla entre 1.94 y 2.67 %/mV -> NO HAY MARGEN
```

El mecanismo: a corriente fija, un dispositivo **más pequeño** obliga a subir
`Vgs`, y eso lleva a inversión más fuerte, donde la exponencial se aplana.

**A 1 nA no se puede salir de subumbral con geometría razonable**, así que la
sensibilidad de la ventana es irreducible. La **pila de cinco `L=10` del equipo
está bien elegida**: da 1.89 %/mV, mejor que el 2.35 de lo mejor de la rejilla.

### 4.4 Desapareo (Monte Carlo, 200 instancias)

El PDK lo trae pero **apagado por defecto** (`design.ngspice:65`,
`sw_stat_mismatch = 0`). `AVT = 7.15 mV·µm`, o sea `sVth(1 µm²) = 5.05 mV`.

```
  Idep      area        sI/I      deriva
  hoy      28.56 um2    0.84 %    0.90 %/mV
  pequeno   0.23 um2    3.04 %    0.30 %/mV
  MEDIO     5.60 um2    0.76 %    0.37 %/mV   <- gana en las tres
```

**`W = 2.00, L = 2.80` domina al diseño actual**: 2.4x menos deriva, algo menos de
dispersión, y 5 veces menos área. No hay compromiso que negociar.

La pila de `Itd`: apilar cinco cuesta 0.1 puntos de dispersión (1.99 % contra
1.89 % de uno solo de `L=50`) y da **17 % más corriente a igual área**.

---

## 5. Los transistores de la celda

### 5.1 Interruptores de escritura M3 / M2 — `sw_dep.npz`, `sw_pot.npz`

**La señal no depende de ellos**: M3 no es el cuello de botella, lo es M4 en
subumbral (251.8 / 252.5 / 253.3 mV con `W` de 0.5 a 0.22). Así que estrecharlos
no cuesta señal.

**Y el suelo CRUZA POR CERO**:

```
  M3            suelo[mV]    senal[mV]   ratio
  0.50/0.63       -5.4837     -251.82     45.9    <- hoy
  0.22/6.00       -0.6071     -243.40    400.9
  0.30/6.00       +0.1158     -244.03   2107.1    <- nulo
  2.00/6.00       +9.4861     -234.30     24.7
```

El suelo es **sublineal en `W`** (4x de `W` da 2.04x) y **BAJA al alargar `L`** —
al revés del modelo de carga de canal. Lo que manda es cómo se reparte la carga
entre `CW` y el nodo flotante `n2`.

El nulo del pfet M2 cae en `L ≈ 1.5`, no en 6: **otra razón para no tratarlos
como pareja simétrica**.

### 5.2 Diodos M9 / M7 — `dio_dep.npz`, `dio_pot.npz`

**La corriente permanente NO depende de M9**: 2.5552 a 2.5701 µA en toda la
rejilla (0.6 % en un rango de 36x en `W`). La fija `M16`.

Lo que M9 controla es **cuánta traza sacas de esa corriente**:

```
  M9            I perm      V0        V0/I
  8.00/0.28    2.5701    0.5679    0.2210
  0.50/0.63    2.5666    0.7671    0.2989    <- hoy
  0.22/6.00    2.5552    0.8793    0.3441
```

+55 % de amplitud a igual potencia, o **~29 % menos `Idep`** para la misma traza.
Dirección monótona en las dos variables: `W` pequeña, `L` larga. Sin
cancelaciones, o sea robusto por construcción.

**El espejo M7 NO se comporta igual.** Ahí la corriente sí cae (5.00 → 2.75 µA a
`0.22/6.00`) porque `n4` se hunde hasta sacar a `MCM_1` de saturación: **M7 pasa
a ser el que fija la corriente en vez del bias**, y se pierde la perilla. El
margen asimétrico lo explica: `n5` puede subir 2.43 V, `n4` solo bajar hasta el
`Vdsat` de `MCM_1`.

Recomendado: `M7 = 0.22/3.00` (+32 % de figura de mérito, control intacto).

### 5.3 Lectura de la traza M4 / M1 — `lec_dep.npz`, `lec_pot.npz`

```
  M4          e-plegado    suelo     max senal
  0.50/0.63     74.8 mV   -2.87 mV    238.9 mV   <- hoy
  0.22/0.28    123.1      -2.09       499.9      <- gana en las tres
```

**M4 al mínimo gana en los tres ejes**: 1.65x más suave, 27 % menos suelo, el
doble de señal. Canal corto degrada la pendiente subumbral, y aquí eso **es lo
que se quiere**.

Y trae una palanca que no estaba identificada: **el suelo depende de `W` de M4**
(−2.09 a −24.07 mV, factor 11.5), porque `n2` tiene capacidad proporcional a M4 y
`vw` comparte carga con él al conducir M3. **Son dos palancas independientes
sobre el término no hebbiano.**

M1 (el espejo, pfet) no tiene punto que gane en todo: el e-plegado crece
monótonamente con `L` (hasta 541.8 mV, muy suave) pero mata la señal (3.3 mV).
Hay que elegir.

### 5.4 Composición: las dos palancas se suman, pero el óptimo NO es apilarlas

```
  M3            M4          suelo      senal     ratio
  0.50/0.63    0.50/0.63   -2.8678    -131.88       46    <- hoy
  0.30/6.00    0.50/0.63   +0.0830    -128.03     1542    <- M3 solo
  0.50/0.63    0.22/0.28   -2.0935    -346.45      166    <- M4 solo
  0.30/6.00    0.22/0.28   +0.7359    -294.37      400    <- apilados: PEOR
  0.50/4.00    0.22/0.28   +0.1457    -322.46     2214    <- REARMADO
```

Interferencia **−3.3 %**: se suman limpiamente. Pero el objetivo es *anular* el
suelo, no desplazarlo lo más posible; M3 solo ya cruza cero y sumarle M4 se pasa.

**El rearmado da 2.4x más señal con el mismo suelo.** Y más señal por unidad de
traza significa que se puede trabajar con menos `Vdep`, o sea menos `Idep`, o sea
**menos corriente permanente**.

---

## 6. Robustez del nulo (esquinas y temperatura)

El nulo sale de que **dos efectos opuestos se cancelan**, así que se comprobó.
No es una ley ni entra en ningún motor: es una tabla de cuánto se mueve un punto.

```
  geometria (M3)         min      max     rango   |peor caso|
  0.50/0.63  (hoy)     -5.513   -5.231    0.282       5.513
  0.50/3.00            -3.102   -1.614    1.488       3.102
  0.30/6.00            -1.325   +1.727    3.052       1.727
```

(3 esquinas × 3 temperaturas, 0–85 °C)

**El peor caso pasa de 5.51 a 1.73 mV — factor 3.2, no 47.** El +0.12 mV vale
solo en típica a 27 °C.

Y hay un compromiso: la geometría de hoy es siempre mala pero **estable** (rango
0.28); el nulo nunca es peor de 1.7 pero es **inestable** (rango 3.05) y **cambia
de signo** — en oblea lenta el peso deriva hacia abajo y en rápida hacia arriba,
lo cual no se puede compensar globalmente.

El óptimo está donde el valor típico vale cero, porque el peor caso es
aproximadamente `|típico| + dispersión/2` y la dispersión crece con `L`.

---

## 7. Consumo

`Idep` **no es corriente de evento**: el diodo M9 la quema en reposo.

```
  a vb_idep = 2.32:   2.57 uA por sinapsis   ->   ~21 uA con las ocho del 4x2
```

Disparen o no. Es el eje de diseño de la celda. Tres palancas indirectas
medidas: la geometría de M16 (§4.3), la de M9 (§5.2) y la ganancia de señal del
rearmado M3/M4 (§5.4).

---

## 8. Abierto

**La polaridad del peso ESTABA invertida.** Resuelto: no era una ambigüedad,
faltaba trazar la cadena.

```
  paper, linea 162   "When Dt < 0 (Dt > 0), VW is decreased (increased) by the
                      depression (potentiation) circuit"
  celda              potenciacion sube vw (+146.76 mV)        -> DE ACUERDO
  M5 iout vw avdd    pfet: vw arriba -> Vsg abajo -> MENOS Iout
  neurona            XC2 Iin vss cap_mim -> `Iin` ES la membrana, y la
                     corriente que ENTRA la carga hacia el umbral
  => potenciar DEBILITABA la sinapsis
```

El nucleo STDP esta bien y respeta la convencion del paper; **el que invierte es
`M5`**, que es anadido del equipo (el paper caracteriza `DVW(Dt)` y no especifica
la lectura). Un pfet con la puerta en `vw` tiene transconductancia negativa por
construccion, y un nfet solo DRENA de `iout` cuando la membrana necesita que le
inyecten. Hace falta transconductor + espejo. Medido con la misma metrica:

```
                 Imax     rango   linealidad    area      signo
  M5 (hoy)      2.350 uA  1.90 V     8.3 %     7.50 um2   INVERTIDO
  Mn+Mp1+Mp2    2.231     1.90       4.6       5.62       correcto
```

Gana en todo: misma corriente, mismo rango, la mitad de alinealidad, 25 % menos
area y el signo bien.

**`Itar` y `VW0` no existen** y son la Fig. 4 del paper. `Itar` son dos
transistores (interruptor con puerta `vpost` + fuente con puerta `vb_itar`, de
`vw` a `avss`) y su ley es lineal: `DVw_tar = Itar·tp/CW`. Con nuestro `CW` de
545 fF y `tp = 33 ns` la pendiente es **0.0606 mV/nA, 6.3 veces más débil** que
los −0.3822 mV/nA del paper.

Ojo: **`Itar` NO estabiliza** — resta siempre, en los dos lados, y se suma a
nuestra deriva. Lo que acota el peso es la dependencia del peso (`VW0`).

**Sin barrer**: M8/M12 (escriben la traza; dueños del techo `Vpost−Vth`) y M5 a
más de una geometría.

**Ficheros que no coinciden**: `stdp.sch` es del 31 de julio y describe otra
celda (otra geometría, M10/M13 que ya no existen, sin M7 ni la pila de `Itd`);
`stdp_lvs.png` es del 22 de agosto y muestra `0.22u/0.28u`. Y `M17` es `W=0.3u`
en `stdp_lvs.sch` y `W=0.5u` en el netlist, con la misma fecha.

---

## 9. Trampas pagadas en esta caracterización

1. **No medir el blanco**: el 98.2 % de lo que llamé señal era inyección de
   carga. Repetible, suave y perfectamente ajustable — ninguna validación
   estadística lo ve. Lo caza un punto de estímulo nulo.
2. **Un blanco incompleto es peor que ninguno**: quitar el post quita la traza
   *y* la inyección del propio post (+4.30 mV). El control son los dos spikes
   con `Dt >> tau`.
3. **Amperímetro aguas arriba de un reparto**: +40.1 % de error de balance.
4. **Caracterizar un circuito sin punto de operación** (el `n3` flotante).
5. **Nodos sin excitar**: `pulso('pre', ..)` en vez de `'vpre'` dejaba el nodo
   flotante. Ngspice solo dice `singular matrix: check node vpre`. Costó cuatro
   hipótesis equivocadas; lo cerró **diffear el netlist generado contra uno que
   funcionaba**.
6. **`.ic` sobre un nodo impuesto por una fuente**: se descarta la línea entera,
   con aviso y sin error.
7. **Ventana de ajuste no declarada**: el e-plegado sale 100.4 o 74.8 mV según
   dónde se ajuste. El mismo dato.
8. **Interpolar linealmente una exponencial**: +10.6 % de error. Y el barrido
   interior era gratis — 43 puntos cuestan lo mismo que 8.
9. **Optimizador que no converge y lo parece**: `minimize_scalar` con
   `xatol=1e-5` sobre un rango de 1e-10 devuelve el primer sondeo. Daba el mismo
   valor en seis casos, incluido uno donde empeoraba el error.
10. **Imponer la física en vez de medirla**: de cuatro predicciones sobre el
    suelo, acerté una. `Cgdo·W` y `Cox·W·L·Vov` no describen un interruptor cuyo
    nodo intermedio flota.

---

## 10. Las ecuaciones, ya ajustadas y validadas

Validacion **LOO por geometria entera**, nunca por punto: se deja fuera una
geometria completa y se predice sin haberla visto, que es lo que le pedira el
motor. El indicador de salud es que el error interno y el LOO **coincidan**;
cuando se separan 12x, la ley no tiene los datos que dice tener.

### 10.1 Nucleo de DEPRESION — `nucleo_w.npz` (168 pts)

`L(M4)` va **FIJA a 0.28 um**, el minimo del proceso, y se justifica midiendo:
el optimo esta ahi y gana en los tres ejes a la vez (e-plegado 123.1 mV contra
74.8, suelo -2.09 contra -2.87, senal 499.9 contra 238.9). Ademas entre L=0.28
y L=0.45 hay una transicion fisica: la dependencia con `W` **cambia de sentido**,
el doble centrado da rango 2 y ninguna ley de potencia lo describe. Con `L`
fija la interaccion desaparece por construccion.

```
  familia            interno    LOO    peor geom
  E1 exponencial      49.4 %   49.7 %    59.0 %     <- la forma "obvia": la peor
  E2 exp+cuad (3)      7.1      7.3       8.0
  M1 mixta    (3)      2.5      3.05      4.51      <- elegida, por parsimonia
  E3 exp+cub  (4)      0.69     1.59      4.35
```

```python
SUELO_W  = (-2.775747e-03, -1.481682e-03)      # suelo[V] = a*W4 + b   (0.03 %)
NUCLEO_W = (
    (+4.349992e-01, -2.128562e+00, -2.074077e+01),   # c_V     cuadratica en ln(W4)
    (-8.902535e-01, +1.475265e+00, +2.274034e+01),   # c_logV
    (-3.021607e-01, +2.972607e+00, +2.121030e+01),   # c_1
)
# DVw(V, W4) = suelo - exp(c_V*V + c_logV*ln(V) + c_1)
```

**11 numeros.** Valida para `W4` en [0.22, 0.90] um y `Vdep` en [0.50, 1.00] V.
(El encoder necesitaba 35 por ley; la diferencia no es el circuito, es haber
reducido bien los grados de libertad antes de ajustar.)

### 10.2 Nucleo de POTENCIACION — `pot_denso.npz` (504 pts)

Aqui `L` **NO se puede fijar**: no hay punto que gane en todo (un factor 5.7 de
suavidad cuesta un factor 27 de senal). Y tampoco se puede interpolar:

```
  LOO dejando fuera una W  (con L fija)     3.5 - 5.2 %
  LOO dejando fuera una L  (con W fija)    43.0 - 47.5 %,  peor 140 %
```

Asi que la ley es **continua en `W` y DISCRETA en `L`**. El motor elige `L` de
una lista corta -- que es lo que se hace en layout, donde nadie pone 1.37 um.
Fingir una superficie suave daba 30 % de error pretendiendo ser 5 %.

Familia ganadora `E3` (4 coef), distinta de la de depresion: no hay una familia
"correcta", se compite en cada caso.

```python
SUELO_POT = (+7.666903e-04, -2.738296e-04)   # suelo[V] = a*W1 + b; cruza en W=0.357
```

**El suelo de potenciacion NO depende de `L`** -- identico a 4 cifras en las tres
medidas -- y **se anula solo** eligiendo `W1 = 0.357 um`. Contrastado con el de
depresion, cuyos dos terminos son negativos y por tanto **no cruza**: alli hay
que jugar con la `L` de M3 y aceptar un nulo por cancelacion con 3 mV de
dispersion en esquinas. Dos problemas distintos y dos remedios distintos.

Coeficientes del nucleo en `../tb/scripts/gen_ley_pot.py` (se regeneran).

### 10.3 Techo y lectura — `m12.npz`, `m5.npz`

```
  M9   fija n5, o sea el TECHO         0.5679 a 0.8793 V
  M12  fija la VELOCIDAD para llegar   83.8 % a 96.4 % del techo en 33 ns
  M5   independencia de carga = f(L) SOLA, no depende de W
       L=1: 1.25 %   L=6: 0.171 %   L=15: 0.078 %
```

Para dar los 2.35 uA que pide la neurona con la `W` minima del proceso basta
`L ~ 7.5`, no 15: **4.5x menos area** (1.65 um2 contra 7.50) con independencia
de carga de ~0.15 %, un orden de magnitud mejor de lo que cualquier espejo pide.

### 10.4 `CW` entra como divisor, con 27 fF de parasita

Las leyes del nucleo estan ajustadas a `nCW = 10` fijo. Verificado que `CW` solo
divide: `senal x nCW` es constante al 8 % en un factor 8 de capacidad. Pero ese
8 % es **sistematico**, no ruido, y sale de una parasita fija en `vw`:

```
  depresion     C0 = 0.500 unidades = 27.2 fF   ->  8.41 % -> 0.33 %
  potenciacion  C0 = 0.490 unidades = 26.7 fF   ->  8.07 % -> 0.04 %
```

Las dos mitades, con estimulos distintos y signos opuestos, dan el mismo numero.
Con el:

```
  DVw(V, W4, CW) = DVw_10(V, W4) * (10 + 0.5) / (nCW + 0.5)      0.04 % de error
```

**Y esa parasita es la puerta de M5**, medido barriendo su geometria:

```
  area de puerta   C0
  7.50 um2        27.2 fF     <- hoy
  1.65             8.1        <- el M5 recomendado por area
  0.50             4.4
  -> C0 = 3.26*area + 2.77 fF
```

O sea que encoger M5 sube la senal de TODAS las sinapsis: 3.4 % a `nCW = 10`,
6.8 % si ademas se reduce `CW`. La decision de area y la de senal estan
acopladas.

### 10.5 Lo que NO cierra

- **`L` fuera de los valores medidos**: si el DRC de layout impide `L(M4)=0.28`,
  o si se necesita una `L(M1)` distinta de 0.40/0.80/2.00, hay que volver a
  medir. La transicion canal corto/largo no se extrapola.
### 10.6 El punto de diseno, determinado por la condicion de equilibrio

`A+/A-` no es una preferencia. En STDP aditivo con pre y post no correlacionados
a tasa `r`, la deriva media del peso va como `r^2*(A+ tau+ - A- tau-)`; si no es
cero, los pesos se van al rail. Con `tau+ = tau-` queda **`A+ = A-`**.

Cruzando esa condicion con el hecho medido de que el suelo de potenciacion se
anula en `W1 = 0.357` (independiente de `L`), la solucion es **unica**:

```
  W4 = 0.30   L4 = 0.28   ->  A- = 223 mV
  W1 = 0.357  L1 = 0.40   ->  A+ = 222 mV, suelo NULO
```

`L1 = 2.00` queda **descartada**: ninguna `W` dentro del proceso alcanza a
equilibrar (su maximo es 141 mV contra los 209 minimos de la depresion). Con
`L1 = 0.80` y `W1 = 0.357` harian falta `W4` por debajo del minimo. Las dos
condiciones juntas fijan las cuatro dimensiones.

**Lazo cerrado sobre el netlist propuesto**, midiendo `Iout` -- lo que la
membrana recibe -- en vez de `vw`:

```
      dt[ns]      DVw[mV]     DIout[nA]      efecto
       -4000     -148.42       -151.56      debilita
        -200     -210.77       -208.81      debilita
        +200     +222.93       +266.53      refuerza
       +4000     +186.51       +219.92      refuerza
```

Pre antes que post refuerza; post antes que pre debilita. Desequilibrio del
5.5 % cerca de `Dt -> 0`, coherente con el 4.6 % de error de las leyes con que
se dimensiono.

El netlist con las tres correcciones esta en
`designs/libs/snn_analog/stdp/stdp_propuesta.spice`.
