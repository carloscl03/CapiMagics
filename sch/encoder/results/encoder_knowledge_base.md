# Encoder — base de conocimiento

Caracterización del encoder de CapiMagics (GF180MCU). Mismo protocolo que
`sch/lif/results/lif_knowledge_base.md`: leyes sacadas de los datos, validadas
con conjunto externo, límites medidos y residuos documentados en vez de
sobreajustados.

Dimensiones de referencia: `sch/encoder/encoder.sch` (el esquemático).
**No** `layout/encoder/encoder_comp.spice`, que lleva `W=0.28u` donde los otros
cinco ficheros del repo llevan `0.5u`.

Banco: `sch/encoder/tb/tb_charac_encoder.spice`.

---

## 1. Qué es el circuito

Una VCCS diferencial: convierte una entrada diferencial en cuatro corrientes.

    referencia autopolarizada  M10+M11 en diodo -> net1
    cola                       M9, puerta en net1
    par diferencial            M1/M2, W/L = 0.05 (L=10u), subumbral
    cargas en diodo            M3/M4 -> nodos x, y
    espejos de salida          M5-M8, L=1.86u -> Iex_1..4

`Iex_1 ≡ Iex_2` (rama x) y `Iex_3 ≡ Iex_4` (rama y): **cuatro pines, dos
corrientes independientes**. Comprobado a 3.3e-16 de error relativo.

`Vin_neg` no es una señal negativa ni una inversión lógica: es la mitad
complementaria de una entrada diferencial, `Vin + Vin_neg = 3.3 V`.

---

## 2. La ley del bias (net1)

Los cuatro parámetros de diseño son `Wp, Lp, Wn, Ln`. Los datos, no la física,
dicen cómo entran.

### El colapso

Minimizando **solo la dispersión vertical** —sin proponer ninguna curva— los
cuatro exponentes convergen a:

    Wp +0.5000   Lp -0.5000   Wn -0.5000   Ln +0.5000
    dispersión entre ellos: 0.0000

sobre 6561 geometrías. O sea, los cuatro parámetros colapsan **exactamente** en

    t = sqrt( (Wp/Lp) / (Wn/Ln) )

Los exponentes se hallaron minimizando la dispersión vertical, que es una
operación multiplicativa y por eso se resolvió en logaritmos. Pero eso es el
método de búsqueda, no la variable: lo que los datos dicen es que `net1`
depende del producto `Wp^0.5·Lp^-0.5·Wn^-0.5·Ln^0.5`, y ese producto es `t`.

Con la malla gruesa (4 niveles por eje) salían 0.4385 / -0.5170 / -0.4327 /
+0.4922 y parecía haber una asimetría sistemática entre los `W` y los `L`.
**No existe: era el muestreo.** Ver sección 5.

### La forma

Familias probadas contra el conjunto externo, sin presuponer ninguna:

| familia (en t) | externo |
|---|---|
| racional, `(a+b·t)/(1+c·t)` | 2.84% |
| potencia | 4.44% |
| recta | 15.44% |

`t = sqrt( (Wp/Lp) / (Wn/Ln) )`, la variable que sale del colapso.

**No hace falta ningun logaritmo.** Una version anterior de este documento
escribia la ley como una sigmoide en `s = log10(t)`; es la MISMA funcion en
otra coordenada -- una logistica en log(t) es una racional en t. Medido:
2.84% las dos, y con el exponente libre `t^n` sale `n = 1.0025`. El logaritmo
era cosmetico y se ha quitado.

Eso resuelve tambien la pregunta de que sigmoide era. En coordenada log,
logistica / tanh / arcotangente / algebraica quedaban entre 2.99% y 3.02%,
indistinguibles. La razon: solo se separan en las colas, y las colas no son
alcanzables. Dentro del rango de datos difieren 6-37 mV, por debajo del
residuo propio del modelo (~35 mV); llegar a donde se separan de verdad
(240 mV) exigiria una relacion de W/L de 10^6, fuera del espacio fisico.
**La pregunta no tiene respuesta y no la necesita.**

### La ley

    net1 = (a + b·t) / (1 + c·t)

        t = sqrt( (Wp/Lp) / (Wn/Ln) )
        a = 0.5876      b = 1.3113
        c = 0.5033 + 0.0366·log10(Wp·Lp)        [Wp·Lp en um2]

    ajuste 2.54%   EXTERNO 2.30%   sesgo -0.02%   max 9.80%

Ajustada sobre 6561 geometrias, validada sobre 2401 que no vio.
Rango cubierto: t de 0.043 a 23.5, Wp*Lp de 0.062 a 34 um2, net1 de 0.579 a
2.490 V. Vdd = 3.3 V.

Las asintotas caen solas donde la fisica las pone: con t -> 0, `net1 -> a =
0.588` ~ Vthn; con t -> inf, `net1 -> b/c = 2.6` ~ Vdd - Vthp. Ley empirica
con coeficientes que resultan tener significado fisico.

### La segunda variable

El residuo del colapso a una sola variable (0.0403 V RMS, 2.11% del recorrido)
**no es ruido**: con 6561 puntos correlaciona con el área del PMOS.

    log(Wp·Lp)   r = -0.516
    log Lp       r = -0.424
    log(Wn·Ln)   r = +0.038     <- el área del nfet no entra

Asimetría medida: el tamaño absoluto del pfet importa, el del nfet no.
Entra por el denominador de la racional, y **logaritmica**: al ajustarla como
potencia el optimizador degenero a `c = -66.88 + 67.38·(Wp·Lp)^0.0002`, que es
la forma numerica de escribir un logaritmo (`x^e ~ 1 + e·ln x`) con coeficientes
enormes que se cancelan. Dandoselo explicito, el error externo baja de 2.84% a
**2.30%** con un solo parametro mas.

Dejar además libres los exponentes de esa segunda variable baja a 2.13%, pero
salen `Wp^1.250 · Lp^2.175 · Wn^-1.372 · Ln^-0.975`, sin patrón interpretable,
a costa de 9 parámetros. **No se adopta**: 0.7 puntos no pagan duplicar los
parámetros con exponentes que no significan nada.

---

## 2b. La etapa diferencial (M1/M2, M3/M4, M9)

Caracterizada con `Vbias` como **entrada** (fuente ideal), no generada por
M10/M11. Seis parametros: `Wd,Ld` (par M1=M2), `Wl,Ll` (cargas M3=M4),
`W9,L9` (cola M9). Barrido de `Vbias` 0.40-2.40 V, 41 puntos.

Datos: `dif.npz` (400 geometrias, entrenamiento), `ext_dif.npz` (400 nuevas,
validacion + condicion desbalanceada), `dif_sweep.csv` (16400 filas legibles).

### No hay dos regimenes

La pendiente local `d log10(I_tail)/dVbias` decae de forma **continua** de 11.2
a 0.076 decadas/V, y su histograma es unimodal. Una version anterior de este
analisis hablaba de una "frontera de saturacion de M9" con un porcentaje de
geometrias a cada lado: eso era un criterio binario (`V(a) > Vbias - Vth`)
impuesto sobre un continuo, no un hallazgo.

### La superposicion: tres parametros

Las 400 curvas `I(Vbias)` son **una sola curva**, transformada:

    log10 I_i(V)  =  A_i  +  F( (V - D_i) / S_i )

`F` es no parametrica (interpolada). Cada geometria aporta tres escalares.

| modelo | residuo de la curva maestra |
|---|---|
| A, D (desplazar y escalar) | 0.1137 dec |
| A, D, S (+ estirar) | **0.0613 dec** |

El estiramiento `S` varia de 0.558 a 1.355 -- un factor 2.4 en anchura. Se
descubrio **descomponiendo el error**, no proponiendolo: con `A` y `D`
ajustados por geometria (o sea, perfectos) el error de extremo a extremo seguia
siendo 0.1137 dec, el 79% del total. Tres rondas de mejora de `A` y `D`
(colapso 1-D, 21 cruzados, colapso 2-D) peleaban por el 21% restante.

### Las leyes y su validacion

`A`, `D` y `log10 S` contra los 6 logs mas sus 21 productos cruzados:

    A explica 86.5%    D 80.6%    S 86.2%     (dentro de muestra)

Extremo a extremo, prediciendo la curva completa de 400 geometrias **que el
ajuste nunca vio**:

    3 parametros (A,D,S)   0.0834 dec  =  +21% / -17% en corriente
    2 parametros (A,D)     0.1280 dec  =  +34% / -26%

El error es ahora uniforme (0.05-0.10 dec en todo el rango de `Vbias`), no
concentrado. Reparto del error restante: curva maestra 54%, leyes 46%.

**El 5-fold predijo el error externo con un 4% de margen** (0.1334 vs 0.1280),
asi que la validacion cruzada es fiable aqui y los 21 cruzados no sobreajustan.

### Estructura de las leyes

Buscando la direccion de colapso por busqueda global (30000 direcciones +
refinado, objetivo suave):

    D  <-  (Wd/Ld) / (W9/L9)     el COCIENTE par/cola     signos opuestos
    A  <-  (Wd/Ld) * (W9/L9)     el PRODUCTO par*cola     mismo signo

Las cargas M3/M4 pesan casi nada en ambas (coeficientes < 0.26 frente a ~1.0).
Una sola variable explica ~61% de cada una; con dos variables y una superficie
cubica sube a 72.8% (D) y 85.6% (A), pero al validar en el lote externo el
modelo de dos variables (0.1331 dec) NO gana al de cruzados (0.1280 dec).
Se documentan ambos: el de dos variables es interpretable, el de cruzados es
marginalmente mas preciso.

### El residuo es real, no ruido

Estimando `A` y `D` con los puntos pares y con los impares por separado
(mitades con la misma informacion):

    ruido de estimacion:  D 0.0017 V,  A 0.0025 dec
    residuo tras colapso: D 0.0300 V,  A 0.2643 dec

El ruido es 17x menor. Lo que falta es estructura, no incertidumbre.

**Aviso metodologico**: la primera version de esta prueba partia el barrido por
rango (Vbias <= 1.4 contra >= 1.4) y daba un "ruido" mayor que la propia
dispersion del parametro. La mitad baja contiene la zona empinada, donde `D`
esta bien determinado, y la alta es plana, donde es casi indeterminable: se
comparaban dos estimaciones de calidad muy distinta. Pares/impares lo arregla.

### El reparto entre ramas

Con `Vin = Vin_neg` las dos ramas son identicas y `V(y)`/`I(rama y)` no aportan
nada. El lote externo repite cada geometria con 100 mV de desbalance:

    fraccion de I_tail en la rama x
    Vbias 0.40   mediana 1.014     <- 100 mV desvian TODA la corriente
    Vbias 1.40   mediana 0.652
    Vbias 2.40   mediana 0.609     <- apenas la desequilibran

La eficacia del desbalance depende de `Vbias`, y la dispersion entre geometrias
es grande a Vbias medio (p10 0.59 contra p90 0.91): la geometria decide cuanto
desvia una misma tension de entrada. Esta es la magnitud que gobierna el rango
de entrada del encoder.

### Limites medidos

    corriente alcanzable: a 1e-5 A solo 264 de 400 geometrias llegan
                          a 3e-5 A solo 112
    error de la ley crece 10x con la corriente objetivo:
                          12 mV a 30 nA  ->  115 mV a 10 uA

### Sin cerrar

- `S` se descubrio al final y no ha pasado el protocolo completo: no se le ha
  buscado direccion de colapso ni se han competido familias, solo se le echaron
  los 21 cruzados.
- ±21% sigue lejos del 1-2% que las leyes del LIF consiguen.
- Todo en `typical`, sin esquinas de proceso.
- Un solo punto de desbalance (100 mV); no hay barrido de la entrada.

---

## 2c. La etapa diferencial: entrada, ganancia y modo comun

Tres entradas reales del bloque: geometria (6 params), `Vbias`, y la entrada
diferencial. Datos: `dif_in2.npz` (reparto), `gan2.npz` (ganancia y excursion),
`cmr_rasgos.npz` (modo comun), `bigx.npz` (1600 geom, Vbias 0.10-2.40).

### Vin y Vin_neg: senal y nivel

    Vcm  = (Vin + Vin_neg)/2      el nivel
    Vdif =  Vin - Vin_neg         la senal

`Vin_neg` no es una senal negativa ni invertida: es la mitad complementaria.
El testbench del equipo hace `Vin` 0->3.3 con `Vin_neg` 3.3->0, asi que su
`Vcm` es constante en 1.65 V y el efecto del modo comun queda invisible.

### El reparto entre ramas es universal

Normalizando cada curva por su centro y su anchura, las 1475 curvas caen sobre
**una sola sigmoide**: residuo 0.0143 sobre una fraccion de 0 a 1 (96.8%).
El centro sale **exactamente cero** por simetria del par -- comprobacion de
cordura que sale bien.

Basta una magnitud para situarla: la anchura 10%-90%.

    Vbias 0.6     187 mV
    Vbias 0.9     464
    Vbias 1.2     995
    Vbias 1.6    1439
    Vbias 2.1    1638        factor 8.7 en todo el recorrido

`Vbias` gobierna el rango de entrada. La geometria pesa parecido: a Vbias 1.2
la anchura va de 299 a 2011 mV segun geometria.

### Corriente de rama

    I_rama = I_tail x reparto

    fraccion que lleva la rama     error
       >= 0.40                     ±20%      igual que I_tail sola
       0.20 - 0.40                 ±38%
       0.05 - 0.20                 ±91%
       < 0.05                      no fiable

En las colas de la sigmoide un error del 33% en la anchura se recorre a lo
largo de una exponencial. No es del modelo: es la magnitud.

### Ganancia y excursion en x, y

    donde se situa V(x)      ±164 mV     73.2%
    cuanto excursiona V(x)   ±14%        79.4%
    ganancia dV(x)/dVdif     ±48%        51.4%   <- el mas flojo

La ganancia mediana ronda **-0.5 V/V**: la etapa ATENUA. Rango completo 0.017
a 4.07 V/V (factor 245); algunas geometrias si amplifican.

Colapso de la ganancia, por busqueda global: la variable dominante es
`(Wl/Ll) / (Wd/Ld)` -- la carga frente al par. Una sola variable explica 36%;
con dos direcciones sube a 51.4% fuera de muestra, contra 32.0% de los 21
cruzados. La segunda direccion mezcla `(Wd/Ld)`, `(W9/L9)` y `Vbias`, o sea el
punto de operacion. Anadir la densidad de corriente solo suma 4 puntos.

### Modo comun: importa, y mucho

    I_tail(Vcm)/I_tail(1.65)     Vcm=0.9    Vcm=3.0
       Vbias 0.6                   0.968      1.072     inmune
       Vbias 2.1                   0.124      2.191     factor 17.7

Rango util (I_tail entre 0.5x y 2x):

    Vbias 0.6    Vcm 0.570 - 3.000    anchura 2.430 V
    Vbias 2.1    Vcm 1.260 - 2.820    anchura 1.575 V

    Vcm minimo         74.1%   ±72 mV
    anchura del rango  66.3%   ±181 mV

`Vcm_min` **sigue a `Vbias`** (0.93 con Vbias 0.9, 1.20 con 1.2, 1.26 con 1.6).

**Aviso**: lo caracterizado en 2b y en el resto de 2c esta medido a
`Vcm = 1.65 V` y no generaliza a otros modos comunes para `Vbias >= 1.2`.
El reparto SI se ha extendido a `Vcm` -- ver 2d.

### El compromiso de Vbias, con las tres columnas medidas

                 corriente   rango de entrada   rango de Vcm   rechazo de Vcm
    Vbias 0.6      baja          187 mV            2.43 V         inmune
    Vbias 2.1      alta         1638 mV            1.58 V         factor 17.7

Subir `Vbias` compra rango de senal y paga con rango de modo comun e inmunidad.
El encoder del equipo trabaja en `net1 = 1.311`, en la mitad alta del
compromiso.

### El hilo comun: la cola

El cociente par/cola decide si M9 satura. Cuando no satura -- que es el caso en
la zona de trabajo real -- pasan tres cosas a la vez, medidas por separado
antes de ver que eran la misma:

1. la corriente total no se regula (17% de variacion con la entrada)
2. el modo comun deja de rechazarse (factor 17.7)
3. la entrada diferencial aporta menos de lo que deberia

### Limite del circuito, no del barrido

A `Vbias = 2.1`, el **61.7%** de las geometrias no completa su transicion en
±2.4 V de `Vdif`: necesitarian mas excursion diferencial que el propio rail.
Eso define una frontera del espacio de diseno utilizable.

### Sin cerrar

- `Vcm` como cuarto eje.
- Validacion externa de las leyes de ganancia, excursion y modo comun
  (las de `I_tail` y `A`/`D`/`S` si la tienen).
- La ganancia en 51.4% es el eslabon debil.
- Esquinas de proceso: todo en `typical`.

---

## 2d. Vcm como cuarto eje: el reparto, cerrado

Barrido `vcm4.npz`: 200 geometrias x 3 `Vbias` (0.9/1.4/2.0) x 3 `Vcm`
(1.00/1.65/2.30), `Vdif` de -2.4 a 2.4 V.

### Cuanto importa Vcm

    anchura de la transicion [mV]   Vcm=1.00  Vcm=1.65  Vcm=2.30   factor
       Vbias 0.9                       458       530       540      1.18
       Vbias 1.4                       624      1443      1880      3.01
       Vbias 2.0                       675      1714      2903      4.30

    I_tail en el centro                                             factor
       Vbias 0.9                    1.16e-6   2.55e-6   2.84e-6      2.4
       Vbias 2.0                    2.71e-6   1.30e-5   1.93e-5      7.1

A `Vbias` bajo casi no influye (1.18); a `Vbias` alto cambia el rango de
entrada por 4.3 y la corriente por 7.1. Coherente con que M9 solo regula a
`Vbias` bajo.

### La sigmoide sobrevive

    residuo del reparto, Vcm variable   0.01566   96.5%
                         Vcm fijo       0.01430   96.8%

    desviacion de la forma media de cada Vcm respecto a la global:
       Vcm 1.00  0.0037    Vcm 1.65  0.0173    Vcm 2.30  0.0119

**`Vcm` no cambia la forma, solo la anchura.** El cuarto eje entra por un
escalar y no obliga a rehacer la estructura. La descomposicion aguanto un
factor 4.3 en anchura y 7.1 en corriente sin deformarse.

### La ley de la anchura, con Vcm

    5-fold sobre GEOMETRIAS (no sobre puntos)

    sin Vcm    explica 36.5%   ±66%
    con Vcm    explica 70.3%   ±27%

Mas general Y mas precisa que la version anterior a `Vcm` fijo (68.7%, ±33%).

### El reparto, cerrado

    frac(Vdif) = SIGMOIDE_UNIVERSAL( Vdif / anchura )

       sigmoide   96.5%   invariante frente a Vbias y Vcm
       centro     exactamente 0 por simetria
       anchura    70.3%   ±27%   sobre geometria + Vbias + Vcm

### Sin cerrar tras 2d

- `I_tail`, ganancia y excursion siguen medidas solo a `Vcm = 1.65`.
- Validacion externa de la ley de anchura con geometrias nuevas.

---

## 2e. La salida (Iex) y el presupuesto de error

Barrido `iex.npz`: 400 geometrias con **ocho** parametros (los 6 de la etapa
diferencial + `Wo,Lo` del espejo M5-M8) x 3 `Vbias`, `Vdif` de -1.6 a 1.6.
Primera vez que se mide `Iex` en el circuito completo.

### El ratio del espejo

    ratio = Iex / I_rama,  normalizado por (Wo/Lo)/(Wr/Lr)

    en contexto      p10 0.64-0.72   mediana 0.96-0.98   p90 1.19-1.34
    aislado          p10 0.48        mediana 1.00        p90 2.10

Un barrido del espejo AISLADO (`esp.npz`, fuente ideal, geometrias al azar)
**sobrestima la dispersion al doble**: muestrea combinaciones que el circuito
real no visita. Medir la pieza fuera de su contexto dio una alarma falsa.

    ley del ratio (5-fold por geometria)   92.8%   ±14%
    usando solo el cociente geometrico             ±34%

**El cociente geometrico no sirve.** Es el atajo natural -- una estimacion por
W/L daba 1/14 cuando el valor real es 1/48 -- y cuesta ±34% en vez de ±14%.
Compuesto con `I_tail`, lleva la salida de ±24% a ±42%.

El exponente de `Vbias` en el colapso del ratio sale **-0.002**: el ratio no
depende del punto de polarizacion. Simplificacion autorizada por los datos.

### Presupuesto de error de la señal

    Iex = ratio x I_tail x fraccion        (zona util, rama >= 40%)

       I_tail   0.0756 dec   ±19%     64% del error
       ratio    0.0567 dec   ±14%     36%
       anchura               ±27%     <=7%  (cero en el centro del reparto)
       ganancia              ±41%       0%  (no esta en la cadena de continua)
       ─────────────────────────────
       Iex      0.0945 dec   ±24%

La ganancia, la excursion de `V(x)` y el rango de `Vcm` **no entran en la
cadena de corriente continua**: son caracterizacion de contexto. Su error no
llega a la señal.

**Aviso**: componer presupuestos a partir de piezas medidas por separado fallo
una vez en esta caracterizacion (el espejo aislado). Este presupuesto usa la
salida medida en el circuito completo, no una proyeccion.

---

## 2f. Metodo: se probaron otras familias de ecuacion

Todas las leyes de este documento se ajustaron inicialmente con polinomios de
los **logaritmos** de los parametros mas sus 21 productos cruzados. Eso explora
solo estructura MULTIPLICATIVA (productos de potencias): en escala logaritmica
no se puede expresar `W + L`, ni `W/(W+L)`, ni `Wo*Lr - Wr*Lo`.

Se comprobo con una biblioteca de ~90 candidatos que mezcla las dos
estructuras (logaritmos, inversos, raices, sumas, restas, productos, formas
saturantes), con seleccion hacia delante juzgada por validacion cruzada y con
**biblioteca creciente**: cada termino elegido genera sus productos con toda la
base, que compiten en la ronda siguiente.

| ley | mixta/creciente vs 21 cruzados |
|---|---|
| `A` de I_tail | +1.1 puntos (10 terminos vs 28) |
| `D` de I_tail | +1.8 puntos |
| `S` de I_tail | -3.0 puntos |
| ratio del espejo | +1 punto |
| anchura | sin ganancia |

**La familia multiplicativa no era la limitacion.** En las cinco pruebas los dos
primeros terminos elegidos son siempre los `W/L` (como diferencias de
logaritmos); lo aditivo entra en tercera posicion o mas abajo, multiplicando a
los logaritmicos. Gana parsimonia (10 terminos donde antes 28) pero no
precision.

### Que NO recibio este tratamiento

Ganancia, excursion y centro de `V(x)`, rango de `Vcm`, e `I_ref`. Ninguna
esta en la cadena de corriente, asi que su error no llega a la señal. Quedan
documentadas como **ajustadas dentro de la familia multiplicativa, sin
verificar**.

---

## 2g. Dominios de validez: leer antes de usar cualquier ley

Dos formas de equivocarse por factores, no por porcentajes:

**1. Fuera del reparto util.** En las colas (rama con <5% de la corriente) el
error de la corriente de rama va de +91% a +789%. Es una propiedad de la
magnitud, no del modelo: un error del 27% en la anchura se recorre a lo largo
de una exponencial.

**2. A `Vcm` distinto de 1.65 V.** `I_tail`, la ganancia, la excursion y el
centro de `V(x)` se midieron TODAS a `Vcm = 1.65 V`. A `Vbias >= 1.2` la
corriente cambia por un factor **17.7** entre `Vcm` 0.9 y 3.0. Estas leyes
**no son leyes del bloque: son leyes de un corte del bloque**.

El reparto y su anchura SI tienen `Vcm` incorporado y validado (seccion 2d).

---

## 2h. Global contra local: como se llega al ±15%

El error de `Iex` no depende de la calidad del ajuste sino de **cuanto espacio
de diseno pretende cubrir una sola ley**. Tres palancas probadas, todas
medidas, ninguna suficiente por si sola:

| palanca | ganancia |
|---|---|
| mas datos (400 -> 1600 geometrias) | 2-3 puntos |
| otra familia de ecuacion (mixta/creciente) | 1-2 puntos |
| menos dimensiones (8 -> 6, espejo fijo) | 2 puntos |

Las tres juntas llevan de ±24% a ~±18%. **La cuarta es la que decide**:

    espacio completo (Ld de 0.28 a 20 um, factor 70)      ±19-21%
    entorno x5 del nominal                                ±18-20%
    entorno x3 del nominal                                **±11-12%**

Confirmado con un barrido dedicado de 1600 geometrias **todas** dentro del
entorno (no filtradas), 5-fold por geometria:

    Vbias 1.4   ±12%       Vbias 2.0   ±11%

Punto nominal del entorno:

    Wd 0.779   Ld 2.470   Wl 0.952   Ll 1.115   W9 0.912   L9 1.498
    (espejo fijo Wo=0.93, Lo=1.86; cada parametro entre /3 y x3)

### Como usar esto

    ley GLOBAL   ±21%    acotar el espacio, elegir donde empezar
    ley LOCAL    ±12%    refinar alrededor de un nominal
    ley de Vbias ±2.3%   valida en todo el espacio

Un motor que trabaje **por refinamiento** -- proponer un punto y explorar su
entorno -- opera en el regimen de ±12%. Uno que pretenda predecir cualquier
geometria del espacio de golpe se queda en ±21%. La diferencia no es de metodo:
ninguna ley suave describe bien un espacio que abarca un factor 70 en una de
sus dimensiones.

### Aviso

El error local vale **dentro del entorno**. Fuera de el la ley local no tiene
garantia ninguna: es un plano de barrio, no un mapa. Reajustar el entorno cada
vez que el nominal se mueva de forma apreciable.

---

## 2i. RESULTADO PRINCIPAL: Iex a ±2-3%

Caracterizacion final de la salida, que es lo que `NeuronSpec` consume como
`iex_range`. Datos: `util.npz` (1600 geom de la region util, ajuste),
`val.npz` (400 geom nuevas, validacion externa), `vxutil.npz` (con V(x)),
`et2.npz` (etapa de salida aislada).

### Arquitectura de tres bloques, interfaz por TENSION

    etapa 1   geometria + Vbias + Vdif  ->  I_rama
    etapa 2   I_rama + Wl, Ll           ->  V(x)     ±3 mV
    etapa 3   V(x) + Wo, Lo             ->  Iex

Bloques independientes. La etapa 3 se mide aislada (puerta impuesta con fuente
ideal) porque la I-V de un transistor no depende de quien genero esa tension.

### Iex, validado en geometrias nuevas

    Vbias   Vdif      EXTERNO     5-fold
     1.0    0.00        8.5%       7.7%
     1.4    0.00        2.7%       2.7%
     1.4   +0.30        1.8%       1.9%
     2.0    0.00        2.0%       1.9%
     2.0   +0.15        1.7%       2.0%

**±1.7-3.4% a Vbias 1.4-2.0**, sobre 400 geometrias que el ajuste no vio.
El 5-fold predijo el externo con menos de un punto de diferencia.

### La asimetria encender/apagar es fisica

    Vdif  +0.30 a -0.15    ±2-3%
    Vdif  -0.30            ±8-12%
    Vdif  -0.60            ±29-32%

Apagar una rama es entrar en la exponencial. Afecta donde la corriente ya es
pequeña, asi que su peso en la frecuencia de disparo es menor.

### Dos condiciones indispensables

**1. Ajustar por REGIMEN, no sobre todo el rango.**

    V(x) sobre 5 decadas de corriente en un ajuste   ±31 mV  ->  Iex ±95%
    V(x) por tramo de corriente                      ±3 mV  ->  Iex ±4%

Y para la etapa 3 el regimen lo fija la DENSIDAD `I/(W/L)`, no la corriente:
dos transistores a la misma corriente con W/L distintos estan en regimenes
distintos. Troceando por corriente: ±14%. Por densidad: ±4.4% a densidad alta.

**2. Caracterizar solo la region que sirve al LIF.**

    Wd 0.26-2.2   Ld 1.1-7.3   Wl 0.58-2.9
    Ll 0.37-1.08  W9 0.30-2.6  L9 0.50-4.5

De 1600 geometrias muestreadas en el espacio amplio, solo **63** entregaban
5-400 nA. El 96% del esfuerzo caia fuera de lo util.

### Como se paso de ±21% a ±2%

| paso | resultado |
|---|---|
| espacio completo, 8 grados de libertad | ±21-24% |
| mas datos (400 -> 1600 geom) | ±21% |
| otra familia de ecuacion | ±20% |
| menos dimensiones (espejo fijo) | ±19% |
| entorno x3 del nominal | ±12% |
| region que sirve al LIF | ±3-6% |
| + ajuste por regimen e interfaz V(x) | **±2-3%** |

**Ninguna mejora vino de ajustar mejor.** Todas vinieron de acotar el problema:
menos espacio, menos rango, un regimen a la vez.

### El error de encuadre, cinco veces

    1. Vbias desde 0.40       el pico de pendiente quedaba fuera (100%)
    2. Vdif hasta ±0.6        el 72% de las transiciones no cabian
    3. Vdif hasta ±0.4        94-100% de las curvas de V(x) truncadas
    4. corriente en 5 decadas un ajuste sobre regimenes mezclados
    5. minimo de Iex          el 100% ocurria en el borde del barrido

Los cinco con el mismo sintoma: un rasgo pegado al limite, o un `n` que cae.
**Regla: antes de ajustar, comprobar que ningun rasgo medido vive en el borde
del barrido.** Los cinco se detectaron despues de ajustar, y dos dieron
numeros publicados que resultaron falsos.

---

## 3. Consecuencias de diseño

### Las dos perillas

| quieres | tocas | efecto colateral |
|---|---|---|
| otro `net1` | la relación `(W/L)p / (W/L)n` | cambia la inmunidad a `Vdd` |
| menos consumo | `L` de ambos, `W` fijo | `net1` baja un 4.7% |

`I_ref` alargando ambos con W fijo (medido):

    W/L        net1      I_ref      potencia
    0.5/0.28   1.3112   43.16 uA   142.4 uW
    0.5/1      1.2676   10.54 uA    34.8 uW
    0.5/4      1.2532    2.45 uA     8.1 uW
    0.5/16     1.2491    0.60 uA     2.0 uW

**72x menos corriente moviendo `net1` un 4.7%.** Hoy el 89% del consumo del
encoder se va en polarizar; se recorta casi entero con una sola dimensión.

### `net1` está acotado

    Vthn (~0.565 V)  <=  net1  <=  Vdd - Vthp (~2.68 V a 3.3 V)

Medido: mínimo 0.5786 V y máximo 2.4903 V en 6561 geometrías. No se sale de
ahí por mucho que se fuerce la geometría.

### Elegir `net1` es elegir el PSRR

Como `Vdd` solo entra en el techo:

    dnet1/dVdd = (peso de la asíntota alta)

A relación 1 la ley predice 0.329 V/V; medido 0.363. Un `net1` alto queda
atado a la alimentación; uno inmune tiene que quedarse cerca de 0.565 V.

---

## 4. La cola no regula (M9)

M9 tiene la misma geometría que M10 y debería espejar sus 43 uA. Entrega
**4.64 uA**, porque su drenador (nodo `a`) está a **35 mV**: está en triodo,
no en saturación. El par (W/L = 0.05) es demasiado débil para absorber lo que
M9 podría dar.

Tres consecuencias medidas del mismo defecto:

1. **La corriente total no se regula**: 5.45 -> 4.64 -> 5.13 uA a lo largo del
   rango de entrada, un 17% de variación. Una cola de verdad la mantendría fija.
2. **Aísla la salida de la alimentación**, sin querer. De 3.0 a 3.6 V:
   `I_ref` +62%, `I_tail` +2.7%, `Iex` +3.9%. Como M9 no transmite lo que la
   referencia le manda, tampoco transmite su sensibilidad.
3. **La entrada diferencial aporta menos de lo que debería**: contra
   `Vin_neg` fija, el rango dinámico es 380x frente a 187x (el doble, bien),
   pero la ganancia apenas cambia (+3%) cuando en un par con cola de verdad
   sería el doble.

**Aviso de diseño.** Meter M9 en saturación regula la corriente *y* abre la
puerta a los +62% de la referencia. Habría que rehacer la referencia
(cascodo, o beta-multiplier) en el mismo movimiento.

---

## 5. Correcciones a conclusiones anteriores

| creencia | qué pasó |
|---|---|
| "el ratio del espejo es 1/14 por geometría" | es **1/48** medido, y además deriva +34% a lo largo del rango |
| "el exponente del colapso es 0.62" | artefacto de fijar las asíntotas a ojo antes de medir la pendiente. Ajustando todo a la vez: 0.4984. Misma clase de error que el `f0` fantasma del LIF |
| "los `W` pesan menos que los `L` en el colapso" | artefacto de 4 niveles por eje. Con 9 niveles: ±0.5000 exacto, dispersión 0.0000 |
| "la S es asimétrica, inflexión en s≈0.4" | ruido de las franjas extremas (n=9). La logística generalizada no gana nada |
| "`W=0.28u` en el encoder" | solo en `encoder_comp.spice`. Los otros cinco ficheros, incluido el extraído del layout, dicen `0.5u` |

---

## 6. Metodología: dos trampas

### Las llaves de `.param` no se sustituyen dentro de `.control`

`dc VIN 0 {VSUP} 0.005` llegaba a ngspice como el literal `vsup`, abortaba el
barrido **en silencio** y dejaba los vectores vacíos. Los errores que salían
después ("vector no disponible") apuntaban a otro sitio.

### La primera línea de un netlist es el título

Un fichero que empieza por `.include` pierde ese include: ngspice se lo come
como título y luego falla con "incomplete or empty netlist", que no dice nada
del origen.

### No leer las asíntotas a ojo

Estimar los extremos de la curva a partir de los puntos extremos de la muestra
y *luego* medir la pendiente propaga el error de unos a la otra. Ajustar todo
a la vez. Aquí convirtió un exponente de 0.50 en un 0.62 aparente.

---

## 7. Datos

| fichero | qué es |
|---|---|
| `grid_datos.json` | 768 pts, malla 4^4 x 3 Vdd (exploratoria) |
| `ext_datos.json` | 2401 pts, malla 7^4 desplazada, Vdd=3.3 (validación externa) |
| `d9_datos.json` | 6561 pts, malla 9^4 log-espaciada, Vdd=3.3 (ajuste) |

Rejillas: W de 0.22 a 2.0 um, L de 0.28 a 17 um, Vdd 3.0/3.3/3.6.

---

## 8. Sin caracterizar

- **`I_ref`**: la forma `A·(W/L)n·(net1-Vthn)^n` da LOO 11.4% y externo 9.3%,
  con exponente 2.08. No es una ley útil al nivel del 1-2% del LIF. Sospecha:
  la transición subumbral -> inversión fuerte, que una sola potencia no cubre.
  Siguiente forma a probar: EKV.
- **`Vbias` del README** (los nodos `x`/`y`, las cargas en diodo): medido el
  recorrido (2.87 -> 2.36 V para Vin 0.6 -> 2.7) y la ganancia (-0.92 a -0.11
  V/V, 8x de variación), pero sin ley ajustada.
- **`Iex(Vbias)`**, la ley del espejo de salida.
- **`I_tail(geometría de M9, V_a)`**: ley de dos puertos, pertenece a la
  caracterización del par, no a la del bias.
- **Todo lo dinámico**: el encoder se ha caracterizado en continua.
- **Esquinas de proceso**: solo `typical`.

## 3. EncoderSpec: validación de lazo cerrado (2026-09-01)

Modelo sustituto sobre `caja.npz` (1200 geometrías, Vbias=1.2): polinomio cúbico
completo en las 6 dimensiones en log (84 términos), para `Iex(-)`, `Iex(+)`,
ganancia `dV(x)/dVdif` y `V(a)`.

    validación externa 70/30 (semilla fija)   ajuste    externo
      lg Iex(-)                                0.35%     0.40%
      lg Iex(+)                                0.44%     0.46%
      ganancia                                 0.41%     0.46%
      V(a)                                     0.24%     0.22%

Solver: 150k candidatos aleatorios + refinado local, minimizando el error
relativo a los tres objetivos, con `V(a) > 0.15 V` y con la restricción de no
usar más de 2 ejes en el 5% exterior de la caja (solo 17 de 1200 geometrías de
entrenamiento tienen 3 o más, así que ahí el modelo no tiene con qué apoyarse).

Cuatro pedidos resueltos y simulados en ngspice:

    MODELO vs NGSPICE:  sesgo -0.25%   |error| medio 0.49%   peor 1.13%

El lazo especificación -> geometría -> simulación cierra al 0.5%, coherente con
la validación externa. `V(a)` sale 576-593 mV en los cuatro, cuatro veces el
umbral pedido.

### 3.1 Corrección: ±0.15 V no estaba en la malla del barrido

Una primera validación dio -8% sistemático en `Iex(-)` y +2% en `Iex(+)`.
No era el modelo. `caja.npz` barrió Vdif de -0.6 a +0.6 con paso 0.02, así que
±0.150 no cae en la malla; `argmin(|vd-0.15|)` devolvía ±0.140 y el modelo quedó
etiquetado con un Vdif que no era el suyo. Con ~2.9 décadas/V, 10 mV son el 7%
observado. Comparando al mismo Vdif el error cae a 0.49%.

**Regla**: antes de nombrar un rasgo por su abscisa, comprobar que esa abscisa
existe en la malla del barrido. Es la misma familia que los artefactos de borde
de la sección 6: un número que sale del muestreo y no del circuito.

### 3.2 Abierto: el pedido no se alcanza exactamente

El modelo se queda a -3/+9% del pedido (Iex bajo por debajo, Iex alto por
encima, ganancia por debajo). No es error de ajuste — el óptimo del solver está
ahí. Sugiere que los tres objetivos están acoplados y no son independientes:
`log(Ib/Ia)` correlaciona +0.649 con `log(G)`. Falta caracterizar ese
acoplamiento y darle a EncoderSpec una comprobación de viabilidad que diga qué
ternas (Ia, Ib, G) existen antes de intentar resolverlas.

### 3.3 Barrido de validación: 40 pedidos alcanzables (2026-09-01)

Protocolo, para que ni el pedido ni la medida pasen por el modelo:
40 geometrías nuevas (semilla 101, <=2 ejes en el borde) se simulan en ngspice;
lo que da cada una se convierte en el pedido. El solver los resuelve sin saber
de dónde salieron, y sus 40 soluciones vuelven a ngspice. Pedido y logrado, los
dos medidos. Malla de Vdif la de `caja` (paso 0.02) con `assert` sobre la
abscisa, para que el error de la sección 3.1 no pueda repetirse.

Cobertura: Iex(-) de 13.5 a 1033 nA, Iex(+) de 96 a 1663 nA, G de 0.228 a 0.760.

    PEDIDO vs LOGRADO      sesgo   |error| medio   p90    peor
      Iex(-)               -0.11%      0.48%      0.77%   1.88%
      Iex(+)               -0.02%      0.38%      0.79%   0.97%
      ganancia             +0.06%      0.33%      0.72%   1.03%

    40/40 con los tres objetivos dentro de +-2%.   V(a): 316-674 mV

Esto cierra el -3/+9% de la sección 3.2: aquellos cuatro pedidos eran inventados
a mano y no existían. Cuando el pedido es alcanzable el solver lo clava. Sigue
haciendo falta la comprobación de viabilidad, pero como aviso al usuario, no
como límite del método.

**Degeneración medida**: solo 5 de 40 soluciones reencuentran la geometría de
origen dentro de 1.3x en todos los ejes (dispersión 0.09-0.18 décadas por eje).
Las otras 35 son geometrías distintas que cumplen las tres especificaciones al
0.4%. Seis dimensiones contra tres objetivos dejan una familia de soluciones de
dimensión 3, hoy sin aprovechar: el área de la solución sale igual que la de
origen (3.43 vs 3.44 um2, menor en 20/40, o sea al azar). Esos tres grados
sobran para un objetivo secundario -- área, `ro`, o apareamiento.

### 3.4 Pendiente, por orden de importancia

1. **Comprobación de viabilidad en EncoderSpec.** Hoy, si la terna (Ia, Ib, G)
   no existe, el solver devuelve la mejor aproximación en silencio. Debe decir
   que no existe y cuál es lo más cercano. Los tres objetivos están acoplados:
   `log(Ib/Ia)` correlaciona +0.649 con `log(G)`.
2. **Aprovechar los 3 grados de libertad sobrantes** (sección 3.3) para un
   objetivo secundario: área, impedancia de salida o apareamiento. Están
   medidos y hoy se gastan al azar.
3. **`Vcm` como eje** en I_tail, ganancia y excursión. Solo el reparto y la
   anchura de la transición lo tienen.
4. **Esquinas de proceso y temperatura.** Nada medido. La pendiente subumbral
   es proporcional a kT/q, así que afecta directamente a V(x) -> Iex.
5. **`I_ref` del bloque de bias** (~9%, sección 2).

## 4. Ley de viabilidad: los tres objetivos no son independientes (2026-09-01)

Muestreando 295k geometrías válidas (<=2 ejes en el borde, V(a)>0.15) y mirando
la nube en (lg Iex(-), lg Iex(+), lg G):

    desviación por eje principal:  0.4521   0.1856   0.0188 décadas

El tercer eje es 24 veces más fino que el primero. **La imagen no es un volumen,
es una superficie**: dados dos objetivos, el tercero está determinado. Por eso
un pedido de tres cifras inventadas casi nunca existe.

Ajustada sobre las 1200 geometrías reales de `caja.npz` (no sobre el modelo):

    lg(Ib/Ia) = -1.01385
                -0.00325 * lgIa      +0.03980 * lgIa^2
                -2.27221 * lgG       +0.48827 * lgG^2
                                     -0.51114 * lgIa*lgG

    ajuste 0.52%   externo 0.54% (p95 1.50%)
    contra las 40 geometrías ajenas del barrido: 0.66% medio, 4.52% peor

(`Ia` = Iex a Vdif -0.14 V, `Ib` a +0.14 V, `G` = dV(x)/dVdif en 0, Vbias=1.2.
Coeficientes en `viabilidad.npy`.)

### 4.1 Uso en EncoderSpec

**Comprobación.** Los cuatro pedidos inventados de la sección 3.2, verificados:

    60-180 nA G=0.35 -> exige Ib=208.0 nA  (pedí -13%)
    80-240 nA G=0.40 -> exige Ib=285.0 nA  (pedí -16%)
    40-120 nA G=0.30 -> exige Ib=136.4 nA  (pedí -12%)
   100-300 nA G=0.45 -> exige Ib=367.2 nA  (pedí -18%)

Los cuatro se cazan, y el diagnóstico es accionable: dice cuánto y hacia dónde.
Eso cierra la sección 3.2: aquel -3/+9% era el pedido, no el método.

**Pedir dos de tres.** 20 pedidos (Iex_min, G) con Ib derivado de la ley,
resueltos y simulados:

    Iex(-)    |error| 0.57%   peor 1.49%
    Iex(+)    |error| 0.43%   peor 1.48%
    ganancia  |error| 0.33%   peor 1.28%
    20/20 con los tres dentro de +-2%

Es el modo en que EncoderSpec debe pedirse: dos objetivos, no tres.

## 5. Los grados de libertad sobrantes: apareamiento (2026-09-01)

Con `(Ia, G)` pedidos e `Ib` fijado por la ley de viabilidad, quedan 4 de las 6
dimensiones libres. Medido sobre 1.18 M geometrías válidas, a especificación
idéntica (+-1% en Ia y G) el margen es grande:

    pedido            area      area del par de entrada
     40 nA G=0.30     2.7x            9.9x
    100 nA G=0.35     4.1x           13.8x
    250 nA G=0.40     4.8x           15.8x
    600 nA G=0.45     3.6x            8.4x

`V(a)` en cambio apenas varía (+-25..50 mV): ahí no hay nada que ganar.

### 5.1 Pelgrom se equivoca de palanca

El PDK trae modelos de desapareamiento (`fets_mm`, incluido ya por la sección
`typical`; se activan con `.param sw_stat_global=0 sw_stat_mismatch=1`), con
`par_vth=0.007148` -> AVT = 7.15 mV·um para el nfet.

Primer frente de Pareto guiado por "agrandar el par de entrada" (área 1.39 a
6.54 um2, `Wd*Ld` de 0.301 a 4.668 um2, 15.5x). Monte Carlo, 300 tiradas:

    sigma_Vos: 24.8 -> 15.9 mV     mejora 1.71x
    Pelgrom sobre el par de entrada predecía sqrt(15.5) = 3.94x

El par de carga M3/M4 pone un suelo: en subumbral `gm = I/(n·VT)` para los dos
pares con la misma corriente, así que la carga refiere su desviación a la
entrada casi con ganancia unidad.

### 5.2 Ley empírica de la desviación de entrada

150 geometrías x 200 tiradas Monte Carlo, midiendo el cruce por cero de
V(x)-V(y). `sigma_Vos` de 8.3 a 32.8 mV.

    lg sigma_Vos = -2.255  -0.451 lgWd  +0.289 lgLd
                           -0.012 lgWl  -1.023 lgLl
                           +0.026 lgW9  -0.041 lgL9

    ajuste 4.8%   externo 5.0%   (la cuadrática no mejora: 4.8%)

Tres lecturas que Pelgrom no da:
- **`Ll` manda** (-1.023), el doble que cualquier otro. La longitud del par de
  CARGA es la palanca del apareamiento.
- **`Ld` es POSITIVO** (+0.289): alargar el par de entrada EMPEORA la
  desviación. La desviación referida a la entrada es Delta/gm, y `gm` del par
  cae al alargarlo.
- **M9 no importa** (+0.026, -0.041): su desapareamiento es modo común.

### 5.3 Frente de Pareto verificado

Pedido Iex(-)=100 nA, G=0.35 (la ley exige Iex(+)=291.9 nA). Objetivo
secundario = combinación de área y `sigma_Vos` de la ley. Verificado con
nominal + 300 tiradas MC:

    w     area   sigma pred  sigma MEDIDA  error   especificación en ngspice
    0.00  7.41      9.7 mV      8.5 mV     -13%    99.5/291.1 nA G=0.349
    0.25  5.06     10.4 mV     10.8 mV      +4%   100.1/293.3 nA G=0.350
    0.50  1.52     23.4 mV     24.4 mV      +4%    99.8/291.2 nA G=0.349
    0.75  1.39     25.9 mV     27.7 mV      +7%    99.5/290.7 nA G=0.349
    1.00  1.39     27.0 mV     26.6 mV      -2%    99.4/290.5 nA G=0.349

La especificación aguanta en los cinco (0.5%): el objetivo secundario no la
toca. Y el frente guiado por la ley bate al guiado por Pelgrom casi por dos:

    guiado por Pelgrom   area 1.39->6.54   sigma 24.8->15.9 mV  (1.7x)
    guiado por la ley    area 1.39->7.41   sigma 26.6-> 8.5 mV  (3.1x)

## 6. Esquinas de proceso y temperatura (2026-09-01)

40 geometrías x 5 esquinas (`typical, ff, ss, fs, sf`) x 3 temperaturas
(-40, 27, 125 C). Sobre la MISMA geometría:

    Iex(-)     factor 4.5x        (8.2 a 1653 nA en todo el barrido)
    ganancia   factor 1.17x       (siempre dentro de +-10%)
    V(a)       284 a 813 mV       el umbral de 150 mV NUNCA se viola

**La ganancia es robusta a esquinas; la corriente no.** Coherente: la ganancia
es una relación de tensiones, la corriente un valor absoluto. La restricción de
saturación de M9 aguanta en las 15 condiciones sin retoque.

El efecto de esquina NO es un factor de escala: la dispersión geometría a
geometría va del 2.5% al 15%.

La ley de viabilidad (sección 4) **mantiene su forma en todas las esquinas**
pero no sus coeficientes:

    con los coeficientes de tt:      2% a 27% de error
    reajustada por condición:     0.36% a 0.57%

O sea que no hace falta recaracterizar: bastan 15 juegos de coeficientes.

### 6.1 Compensación por Vbias: funciona

`Vbias` es una ENTRADA de esta etapa. Buscando, en cada condición, el `Vbias`
que devuelve `Iex` a su valor nominal (20 geometrías, barrido 0.90-2.00 V):

    condición      Vbias necesario   dispersión entre geom   residuo
    ff     125C        1.055 V            13 mV               5%
    ff      27C        1.065 V             9 mV               8%
    typical 27C        1.200 V             0 mV               0%
    sf      27C        1.294 V            27 mV               4%
    ss     125C        1.359 V           125 mV              12% (peor 29%)

Un ÚNICO `Vbias` por esquina, igual para todas las geometrías, convierte la
deriva de 4.5x en un residuo del 3-13% (peor 30%). La dispersión entre
geometrías es de 9-37 mV sobre un recorrido de corrección de 304 mV: la
corrección es propiedad de la esquina, no del diseño. Solo se degrada a 125 C
en las esquinas lentas (125 y 98 mV).

El `Vbias` necesario depende **casi solo del proceso, no de la temperatura**:
`ff` pide 1.055-1.072 V a lo largo de 165 C; `ss`, 1.341-1.359 V.

### 6.2 Pero el bloque M10/M11 NO puede darla

El divisor de diodos pmos/nmos que fija `net1` mide la magnitud equivocada.
Descompuesto en los dos ejes del proceso (27 C):

                            pide      divisor   cobertura
    eje velocidad ff->ss    279 mV     44 mV       16%
    eje sesgo p/n fs->sf    186 mV    248 mV      133%

**Cubre el 16% del eje que importa y el 133% del que no.** En `ff` los dos
transistores se aceleran a la vez y el punto del divisor apenas se mueve; en las
esquinas cruzadas se pasa de largo. Probadas 6 relaciones `Wn/Ln` : `Wp/Lp`
(incluida la caracterizada en la sección 2): tras ajustar libremente ganancia y
desplazamiento, el residuo es de 64 a 105 mV rms (peor 136-178 mV) sobre los
304 mV a seguir. No es cuestión de dimensionar el divisor: la topología es
insensible a la velocidad global por construcción.

### 6.2.1 Medido con el circuito autopolarizado real

20 geometrías, M9 gobernado por (a) `Vbias` fijo a 1.2 V, (b) el `net1` del
divisor real M10/M11, (c) el `Vbias` ideal de cada esquina. Factor de `Iex`
respecto a `typical` (1.00x = sin deriva), 27 C:

    esquina    net1      Vbias FIJO   autopolarizado   Vbias IDEAL
    typical   1.311 V       1.00x          1.00x          1.00x
    ff        1.289 V       1.75x          1.50x          1.00x
    ss        1.333 V       0.50x          0.63x          1.00x
    fs        1.189 V       1.49x          0.92x          1.00x
    sf        1.437 V       0.63x          1.03x          1.00x

Separado por ejes:

                            Vbias fijo    autopolarizado
    eje sesgo p/n (fs,sf)     2.37x          1.12x     <- casi resuelto
    eje velocidad (ff,ss)     3.50x          2.38x     <- apenas tocado

**Matiz importante**: el autopolarizado NO es inútil. Corrige el desequilibrio
p/n de 2.37x a 1.12x, que es casi perfecto. Lo que no ve es la velocidad global,
y ese es el eje que domina. Queda una deriva de 2.4x entre `ff` y `ss`.

No hay que sustituir M10/M11: hay que AÑADIRLE lo que le falta. Una referencia
que siga la velocidad absoluta (beta-multiplier / constant-gm: un lazo con una
resistencia, que por eso sí nota si los transistores van rápidos o lentos)
cubriría el eje ciego, y el divisor seguiría haciendo bien su parte.

### 6.3 Consecuencia de sistema

Con la ley del LIF (`f = 16.41 kHz/nA`), sin compensar:

    100 nA nominales -> 1641 kHz
      esquina ff     ->  175 nA -> 2870 kHz
      esquina ss     ->   50 nA ->  822 kHz

El mismo estímulo produce 3.5x más disparos en un chip que en otro.

## 7. Cómo compensar el proceso: tres opciones medidas (2026-09-01)

Montada una referencia autopolarizada con resistencia (beta-multiplier
subumbral: espejo pmos, par nmos 1:8, `ppolyf_u_3k` de 0.8x200 um ~ 750 kOhm,
arranque por 200 MOhm). En subumbral su corriente es `n·VT·ln(K)/R`: depende de
la resistencia y la temperatura, NO de Vth ni movilidad. M9 se usa como espejo
del nmos de la referencia, así que la tensión se acomoda sola.

20 geometrías, deriva de `Iex` respecto a typical/27C:

                        PROCESO (a T fija)  TEMPERATURA (a proc. fijo)  TOTAL
    Vbias fijo               4.52x                 1.38x                4.52x
    divisor M10/M11          2.70x                 1.39x                2.97x
    referencia con R         1.12x                 5.67x                6.03x

**La referencia hace exactamente lo que se le pide**: deja el proceso en 1.12x
(y el eje ff->ss en 1.02x). `V(n1)` recorre 221 mV entre ff y ss, cerca de los
279 que hacen falta; el divisor recorría 44.

**Pero el trato es malo.** La dispersión de proceso se puede ajustar UNA VEZ por
chip en el test; la temperatura cambia en operación y ningún ajuste de fábrica
la sigue. Cambiar un error corregible por uno que no lo es empeora el sistema, y
aquí encima el total es peor (6.03x vs 2.97x).

Causa: `I = n·VT·ln(K)/R` sube con la temperatura, y la resistencia de poli baja
(`r_tc1 = -0.001669823` en el modelo). Los dos efectos suman en vez de cancelar.

### 7.1 Recomendación

1. **Ajuste de `Vbias` por chip** (sección 6.1): residuo 3-13%, deja intacto el
   eje de temperatura. Cuesta un pin o un DAC. Es lo que funciona hoy.
2. **Referencia con resistencia CON compensación térmica**: combinar la parte
   proporcional a la temperatura con una de signo contrario (principio del
   bandgap, a nivel de nanoamperios). Resuelve el proceso de verdad, pero es
   trabajo de diseño, no de dimensionado.
3. **Sistema ratiométrico**: que el umbral y la fuga del LIF salgan de la misma
   referencia que el encoder. La frecuencia pasa a ser una relación de dos
   corrientes que derivan juntas. No cuesta pines ni área, y con el LIF ya
   caracterizado es comprobable. Es la vía más prometedora.

Mejora barata sin cambiar topología (sección 6.2): `Lp = 1.0 um` en M11 sube el
seguimiento del divisor en el eje ff->ss de 44 a 117 mV de los 279 necesarios
(del 16% al 42%).

## 8. Reanálisis tras limitar los grados de libertad (2026-09-01)

Con la ley de viabilidad en la mano, `Iex(-)` deja de ser una salida a ajustar:
se deduce de `Iex(+)` y `G`. Eso invita a revisar si hace falta la cúbica de 84
términos. Escalera de coste (validación externa 70/30 sobre `caja.npz`):

    salida    grado 1 (7 coef)   grado 2 (28)   grado 3 (84)
    lgIa          7.33%             1.20%          0.40%
    lgIb          2.35%             0.81%          0.46%
    lgG           2.69%             0.61%          0.22%
    va            2.31%             0.30%          0.22%

`Iex(-)` es la peor de ajustar por ser el extremo exponencial; deducirla de la
viabilidad la baja de 7.33% a 4.40%.

### 8.1 Colapsar a cocientes NO sirve: reduce cálculos, no variables

Ajustando los seis exponentes de la ganancia por separado salen en +-1/2,
formando `sqrt((Wd/Ld)/(Wl/Ll))` sin que se les impusiera el cociente -- y M9
sale en 0.02, o sea que la ganancia no depende del transistor de cola. Escrito
como cociente son 2 coeficientes en vez de 7, con 3.07% en vez de 2.69%.

**Pero eso no reduce variables**: `((Wd/Ld)/(Wl/Ll))` sigue necesitando las
cuatro. Solo ordena la aritmética, y cuesta 0.4 puntos de precisión. Descartado:
se queda la forma libre de 7 coeficientes. Lo que se persigue es reducir GRADOS
DE LIBERTAD, no operaciones.

Lo que sí sobrevive del análisis: `Iex(+)` NO admite el cociente (2.35% ->
8.89%) mientras la ganancia y `V(a)` sí (2.69->3.07%, 2.31->2.53%). Las
magnitudes ratiométricas dependen de la proporción entre dispositivos; la
corriente absoluta, del tamaño. Confirma con datos el aviso del equipo sobre
usar W/L como cociente, y acota dónde aplica.

### 8.2 Reducir variables de verdad: cuáles se pueden fijar

Cobertura del espacio de `(Iex, G)` alcanzable al clavar dimensiones en su valor
central, medida sobre 400k geometrías:

    fijadas          envolvente    REGIÓN ÚTIL (Iex 20-400 nA, G 0.25-0.55)
      W9                90.2%          99.5%
      Ld                85.2%          99.1%
      Ld + W9           76.1%         100.0%
      Ld + Ll + W9      61.1%          94.4%
      Ld+Ll+W9+L9       24.5%          56.9%

**`Ld` y `W9` se pueden fijar gratis**: pierden el 24% del envolvente entero
pero el 0% de la región que el LIF usa. Toda la pérdida está en los extremos.

(Nota: el razonamiento "la superficie es 2D luego bastan 2 dimensiones" es
FALSO. Con 2 dimensiones libres recorres una sub-superficie que no cubre la
región alcanzable: fijar 4 deja el 56.9% de la región útil.)

### 8.3 Leyes en 4 variables

Barrido propio de 800 geometrías con `Ld = 1.612 um` y `W9 = 0.392 um` fijos,
variando `Wd, Wl, Ll, L9` (`cuatro.npz`):

    salida   potencia (5 coef)   cuadrática (15 coef)
    lgIa         6.01%                 0.90%
    lgIb         2.05%                 0.68%
    lgG          2.60%                 0.56%
    va           1.95%                 0.26%

    lgIa = -5.927 -0.358 lgWd -0.897 lgWl +1.751 lgLl -1.367 lgL9
    lgIb = -5.543 +0.149 lgWd -0.963 lgWl +1.613 lgLl -0.880 lgL9
    lgG  = -0.128 +0.470 lgWd -0.461 lgWl +0.544 lgLl +0.027 lgL9

`L9` sale en 0.027 en la ganancia: con `Ld` y `W9` fijos, **la ganancia depende
de tres variables**. Segunda confirmación de que la cola no la toca.

Con 4 variables y 15 términos se llega a 0.6-0.9%, donde con 6 variables hacían
falta 84 términos para 0.2-0.5%.

### 8.4 Lazo cerrado en 4 variables

25 pedidos alcanzables (geometrías nuevas simuladas -> pedido -> solver ->
ngspice; el modelo no toca ninguno de los dos lados):

    Iex(-)    |error| 0.82%   peor 2.26%
    Iex(+)    |error| 0.60%   peor 2.28%
    ganancia  |error| 0.37%   peor 1.01%
    24/25 dentro de +-2%      25/25 dentro de +-5%

Contra 40/40 dentro del +-2% con 6 variables: prácticamente equivalente, con dos
variables menos y **60 coeficientes en vez de 336**. Usando la viabilidad para
deducir `Iex(-)`, quedan 45.

DECISIÓN: `EncoderSpec` trabaja en 4 variables (`Wd, Wl, Ll, L9`), con `Ld` y
`W9` fijos a 1.612 y 0.392 um. Los otros dos vuelven a ser libres solo si se
piden extremos fuera de la región útil.

### 8.5 A qué valores fijar `Ld` y `W9`

Rejilla de 5 x 3 valores, midiendo cobertura de la región útil y, para un pedido
de referencia (100 nA, G=0.35), el área y la `sigma_Vos` alcanzables:

         Ld      W9   cobertura   area min   sigma min   sigma@area min
       1.05    0.28      95.8%     1.40 um2    11.3 mV       26.1 mV
       1.30    0.28      98.1%     1.49        10.9          26.7
       1.61    0.28      99.5%     1.65        10.1          27.2
       2.00    0.28     100.0%     1.92        10.2          26.2
       2.45    0.28      99.1%     2.39         9.6          23.6
       1.61    0.39     100.0%     2.13        10.1          28.1
       2.45    0.50      90.7%     3.63         9.4          24.1

`W9` no aparece ni en la ganancia ni en la desviación: solo cuesta área, así que
conviene pequeño. `V(a)` sale igual en todas las opciones (532-568 mV) y no
restringe. El frente área/apareamiento se mantiene en 2.6-2.7x al fijar las dos,
así que la perilla `tradeoff` conserva su recorrido.

**Corrección sobre `Ld`**: la ley de `sigma_Vos` tiene `+0.289 lgLd`, que sugiere
`Ld` pequeño. Pero eso es una derivada parcial, con todo lo demás quieto. A
ESPECIFICACIÓN CONSTANTE las otras variables se reacomodan y el efecto se
invierte (11.3 -> 9.6 mV al subir `Ld`), aunque solo un 5%.

    ELEGIDOS:  Ld = 1.60 um    W9 = 0.30 um

23% menos área que el 1.61/0.39 inicial, con la misma cobertura y el mismo
margen de saturación. `W9 = 0.30` queda un escalón dentro del borde de la caja
(cuyo mínimo, 0.28, es nuestro, no del proceso: el PDK admite 0.22).

Barrido de confirmación (800 geometrías, `cinco.npz`), cuadrática de 15
términos: lgIa 0.94%, lgIb 0.67%, lgG 0.51%, va 0.25% -- idéntico al de
1.61/0.39. Y los exponentes apenas se mueven entre las dos rebanadas:

    lgIb a 1.61/0.39:  +0.149 lgWd -0.963 lgWl +1.613 lgLl -0.880 lgL9
    lgIb a 1.60/0.30:  +0.142      -0.951      +1.639      -0.905
    lgG  a 1.61/0.39:  +0.470      -0.461      +0.544      +0.027
    lgG  a 1.60/0.30:  +0.453      -0.439      +0.522      +0.033

**Al mover los valores fijos cambia prácticamente solo la constante**, no la
forma de la ley. Si más adelante hacen falta otros valores, basta reajustar el
término independiente con un barrido pequeño.

### 8.6 CORRECCIÓN: el suelo de la caja era un artefacto (2026-09-01)

Al preguntar de dónde salía `W9 = 0.30` apareció que el suelo de 0.28 de la caja
**no era del proceso ni del circuito, era un artefacto de cómo derivé la caja**.
Se ve porque `Wd` sí bajaba a 0.260. Datos del PDK: `wmin = 0.22`,
`lmin = 0.28`. (Nota: los `0.28u` del circuito original del equipo son LARGOS al
`lmin`, no anchos recortados por gLayout.)

**`W9` más pequeño mejora `V(a)` en vez de empeorarlo** (393 mV a 0.22 contra
358 a 0.30): menos ancho es menos corriente de cola, el par de entrada necesita
menos `Vgs` y el nodo `a` se sienta más alto. El ahorro es del 8% del bloque
(M9 pasa de 0.514 a 0.377 um2, pero el total ronda 1.6). Elegido `W9 = 0.26`:
casi todo el beneficio sin sentarse en el mínimo absoluto del proceso.

Revisados los demás suelos, los diseños de área mínima se salían siempre por
`Wl` (a 0.31-0.34, suelo 0.55) y `Ll` (a 0.29-0.39, suelo 0.37) -- las dos
palancas fuertes de la corriente (-0.95 y +1.64). `Wd` y `L9` se quedaban
dentro. Ampliando solo esos dos bordes se captura TODO el ahorro (1.38 um2
contra 1.37 de la extensión completa).

Coste y solución: la cuadrática de 15 términos se degrada de 0.94% a 2.98% en la
caja ampliada, y la curva de aprendizaje es PLANA (3.25% con 100 puntos, 3.22%
con 600) -- no falta dato, falta modelo. Subiendo a cúbica en 4 variables:

    caja        grado 2 (15)  grado 3 (35)  grado 4 (70)
    ORIGINAL       0.94%         0.31%         0.25%
    INTERMEDIA     2.98%         0.65%         0.38%

Con 35 términos la caja ampliada da 0.65%, mejor que la cuadrática en la caja
original, y con 26% menos área. No hay que elegir.

**CONFIGURACIÓN FINAL de EncoderSpec**

    fijos     Ld = 1.60 um     W9 = 0.26 um
    libres    Wd  0.26 - 1.80      Wl  0.30 - 2.70
              Ll  0.28 - 0.62      L9  0.80 - 3.78
    leyes     cúbica en 4 variables, 35 términos por salida
              lgIa 0.65%  lgIb 0.58%  lgG 0.26%  va 0.12%
    barrido   `siete.npz` (800 geometrías)

Lazo cerrado (25 pedidos, geometrías nuevas simuladas -> solver -> ngspice):

    Iex(-)    |error| 0.89%   peor 3.63%
    Iex(+)    |error| 0.71%   peor 2.93%
    ganancia  |error| 0.22%   peor 0.61%
    22/25 dentro de +-2%      25/25 dentro de +-5%

Cubre Iex de 13.9 a 600 nA (antes 43.7-600) con 26% menos área.

**Regla de método**: los límites de una caja de diseño heredada hay que
justificarlos o volver a medirlos. Este arrastró media sesión sin que lo viera,
y venía de mí, no del proceso.

### 8.7 Viabilidad y `sigma_Vos` reajustadas en la caja corregida

Ambas estaban ajustadas en 6 dimensiones y en la caja vieja. Rehechas sobre
`siete.npz` (viabilidad) y un Monte Carlo nuevo, `mcley7.npz` (desviación).

**La superficie sigue siéndolo**: ejes principales 0.6298 / 0.1851 / 0.0219
décadas, razón 0.035 (antes 0.042). La restricción entre los tres objetivos no
era un artefacto de la caja.

**Ley de viabilidad** -- ahora conviene parametrizar desde la corriente MÍNIMA:

    desde (Iex(-), G):  1.26% externo (p95 3.00%)
    desde (Iex(+), G):  2.37% externo

    lg(Iex(+)/Iex(-)) = -2.47104
                        -0.43038 lgIex(-)   +0.00867 lgIex(-)^2
                        -2.30476 lgG        +0.49599 lgG^2
                                            -0.51769 lgIex(-)*lgG

(Coeficientes en `viabilidad7.npy`. En la caja anterior convenía pedir `Iex(+)`
porque `Iex(-)` era la peor de ajustar; con la cúbica las dos leyes directas se
igualan (0.65% y 0.58%) y decide la viabilidad.)

**INTERFAZ: `EncoderSpec` se pide con `(Iex_min, ganancia)`.**

**Ley de la desviación de entrada**, 150 geometrías x 200 tiradas:

    sigma_Vos de 7.7 a 38.8 mV
    lg sigma_Vos = -2.231 -0.436 lgWd -0.026 lgWl -1.068 lgLl -0.028 lgL9
                                    externo 5.6% (potencia) / 4.2% (cuadrática)

Depende solo de **`Wd` y `Ll`**; `Wl` y `L9` están en 0.026 y 0.028.

### 8.8 Comprobación cruzada: las dos leyes se reproducen

Las versiones nueva y vieja salen de barridos INDEPENDIENTES (`caja.npz` con 6
dimensiones libres; `siete.npz`/`mcley7.npz` con 4, en otra caja y con `Ld` y
`W9` en otros valores). Coinciden:

    viabilidad, sobre los 4 pedidos imposibles históricos:
       60-180 G=0.35   nueva 207.4 nA   vieja 208.0 nA
       80-240 G=0.40         286.3            285.0
       40-120 G=0.30         134.2            136.4
      100-300 G=0.45         370.4            367.2

    sigma_Vos, términos compartidos:
       constante  -2.231 vs -2.255
       lgWd       -0.436 vs -0.451
       lgWl       -0.026 vs -0.012
       lgLl       -1.068 vs -1.023
       lgL9       -0.028 vs -0.041

Dos medidas independientes que dan lo mismo describen el circuito, no el
barrido. Es la validación más fuerte que tienen estas dos leyes.

## 9. El bloque de esquinas, en la caja corregida (2026-09-01)

400 geometrías (las MISMAS en las 15 condiciones, para poder restar) x 5
esquinas x 3 temperaturas, sobre la caja de la sección 8.6. 400/400 válidas en
las 15. Datos en `esquinas7.npz`.

### 9.1 La esquina es una corrección, no una ley nueva

Error en `Iex(-)` tras corregir el residuo respecto a `typical|27C`:

    condición      solo un factor   potencia (5)   cuadrática (15)   sin corregir
    typical|-40         8.1%           2.99%           1.01%             9.2%
    ff|27               4.8%           1.15%           0.54%            81.6%
    ss|-40             15.2%           4.18%           1.29%            61.3%
    sf|-40             13.8%           4.80%           1.33%            48.5%

Un solo factor deja 3.3-15.2% (confirma que la esquina NO es escala pura). Una
**cuadrática de 15 coeficientes deja todo por debajo del 1.35%**, encima de la
ley típica que está en 0.65%.

### 9.2 Proceso y temperatura NO se factorizan

Probado `residuo(esquina,T) ~ residuo(esquina,27) + residuo(typical,T)`:
error 7.2 a 17.9%. Interactúan -- la pendiente subumbral va con `kT/q` y la
esquina mueve la `Vth`, así que el efecto de una depende de la otra. Hacen falta
las 14 correcciones, no 4+2.

### 9.3 La viabilidad también necesita sus 15 juegos

    con los coeficientes de typical:   1.35% a 30.72%
    reajustada por condición:          0.98% a  1.71%

Mismo resultado que en la caja anterior (sección 6), así que no era un artefacto
de aquella.

### 9.4 Coste total del bloque

    14 correcciones x 15 coeficientes x 3 salidas     630 números
    15 juegos de viabilidad x 6                        90
    leyes de typical (4x35 + viabilidad 6 + sigma 5)  151
                                                     ----
                                                      871

Error en cualquier esquina: ley típica (0.65%) + corrección (<=1.35%), del orden
del 2%.

SIN MEDIR todavía: `sigma_Vos` entre esquinas (exigiría 15 Monte Carlo) y la
variación global estadística (`sw_stat_global=1`).

### 9.5 Cuánto de esto hace falta de verdad

Contando lo que necesitaría el paquete: 105 (leyes nominales cúbicas, 3 salidas)
+ 6 (viabilidad) + 5 (`sigma_Vos`) + 630 (correcciones de esquina) + 84
(viabilidad por condición) = **830 coeficientes**, de los cuales **725 son solo
para esquinas**.

No se justifican. Lo que un diseñador pregunta en esquinas y lo que cuesta
responderlo:

    cuanto deriva Iex          envolvente 3.3x a 10.7x (mediana 5.0x = 402%)
    sigue M9 saturado?         V(a) minimo 350 mV en las 15 condiciones,
                               se cumple en 6000 de 6000 casos
    cuanto deriva la ganancia  envolvente 1.10x a 1.40x

    un SOLO factor por condicion acierta al  3.3% - 15.2%
    los 725 coeficientes lo bajan al         0.5% -  1.35%

Un 15% de error sobre un efecto del 402% es de sobra: los 725 refinan la tercera
cifra de algo que se mueve un factor 5. Y la restricción de saturación, la otra
razón para modelar esquinas con detalle, nunca se activa (sobra un factor 2.3 en
el peor caso).

**PAQUETE FINAL**

    leyes nominales (3 x 35)              105
    viabilidad típica                       6
    sigma_Vos                               5
    esquinas, un factor por condición      28   (14 para Iex + 14 para G)
                                          ---
                                          144

Del tamaño del `laws.py` del LIF, no de una tabla de datos.

**El bloque fino no se tira**: queda medido aquí (secciones 9.1-9.4, datos en
`esquinas7.npz`). Si el equipo arregla la polarización y la deriva residual baja
al 3-13% de la sección 6.1, entonces un modelo al 1.35% empieza a valer, porque
ya no estaría refinando ruido.

**Y el fondo del asunto**: el problema de las esquinas no es de modelado, es de
circuito. Ninguna cantidad de coeficientes arregla que `Iex` se mueva un factor
5 entre chips; solo lo describe con más decimales. Lo arregla la polarización
(sección 7).

## 10. El motor: `designs/scripts/encoder_design/` (2026-09-01)

Escrito con la estructura de `lif_design`: solo stdlib, entrada determinista,
salida estructurada, y la misma política de prioridades (objetivos mandan,
dimensiones fijadas se ajustan con WARNING, contradicción irresoluble -> ERROR
con la cadena causal).

    spec.py      EncoderSpec / EncoderDesign / Note / Severity
    laws.py      las leyes, con su error medido en el docstring
    coeffs.py    146 números, GENERADO por sch/encoder/tb/scripts/gen_coeffs.py
    solver.py    viabilidad -> objetivos -> grados de libertad sobrantes
    example.py   python -m encoder_design.example
    README.md

Tres cosas que el del LIF no necesita: la capa de viabilidad, la perilla
`tradeoff`, y la esquina como contexto de primera clase.

### 10.1 Validación del motor en ngspice

36 diseños generados por el motor (6 corrientes x 3 ganancias x los dos
extremos de la perilla) y simulados:

    PEDIDO vs NGSPICE
      iex_min    |error| 1.42 %   p90 2.68 %   peor 3.24 %
      ganancia   |error| 0.51 %   p90 0.91 %   peor 2.85 %
      24/36 dentro del +-2 %      36/36 dentro del +-5 %

    MOTOR vs NGSPICE
      iex_min 1.43 %   iex_max 1.27 %   ganancia 0.27 %

Las dos tablas son casi iguales: **el solver acierta a su propio modelo casi
exactamente**, así que el error residual es enteramente de las leyes.

Y ese 1.43 % es peor que el 0.65 % medido fuera de muestra, porque el solver
busca los extremos de la caja (sobre todo con `tradeoff` en 0 o en 1), que es
donde la ley tiene menos apoyo. **La precisión del motor en uso real es 1.4 %,
no 0.65 %** -- es la cifra que hay que citar.

### 10.2 Caminos verificados

    sin objetivos                    -> punto nominal
    (iex_min, gain)                  -> 100.1 nA, 0.3504 pidiendo 100 y 0.35
    los tres, imposible              -> ERROR con el valor que el circuito exige
    los tres, compatible             -> INFO, sigue adelante
    tradeoff 0 -> 1                  -> sigma_Vos 10.0 -> 39.6 mV (factor 4),
                                        area 5.13 -> 1.08 um2, especificación
                                        clavada en los cinco puntos
    esquina                          -> INFO con lo que dará el chip
    dimensión fuera de la caja       -> WARNING + recorte, Y AVISO de que el
                                        objetivo ya no se alcanza (la cadena de
                                        consecuencias, no solo el recorte)

Falta `check.py`: verificación contra ngspice, como el del LIF. Y todo el
bloque de layout (netlist/place/build), que es otro proyecto -- el del LIF son
3700 líneas.

### 10.3 Dimensiones fijadas: la política de prioridades

Primera version del solver solo recortaba a la caja y avisaba al final de que no
habia llegado -- incumplia en silencio la prioridad 1 sobre la 2. Corregido a la
politica que el equipo escribio en `lif_design`: si una dimension fijada impide
alcanzar el objetivo, SE LIBERA, con WARNING y cadena causal.

Orden de liberacion por coste de cambio, deducido de las leyes medidas:

    1. L9   no interviene en ganancia (exp 0.03) ni en desapareamiento (0.03),
            y no es un par apareado
    2. Wl   mueve la ganancia pero NO el desapareamiento (exp 0.03)
    3. Ll   mueve la ganancia Y domina el desapareamiento (exp -1.07)
    4. Wd   par apareado de entrada: ganancia, desapareamiento y layout

Verificado:

    fijada y no estorba          -> se respeta, sin avisos
    fijada y estorba             -> liberada, cadena "85.3 % -> 0.1 %"
    las cuatro fijadas           -> libera L9 (90.8->41.0 %) y Wl (->0.2 %),
                                    PARA, y deja Wd y Ll como el usuario las puso
    objetivo inalcanzable        -> ERROR con lo mas cercano en ambos objetivos

Se libera solo lo necesario y se para al entrar en tolerancia.

## 11. La interfaz con el LIF: `source_ro` (2026-09-01)

`NeuronSpec` acepta `source_ro` como contexto y con el calcula el error
esperado: su ley pide `1.9 / (tol * iex)` GOhm. **El encoder no lo reportaba**,
asi que los dos motores no componian. La impedancia estaba medida (`rox.npz`,
800 geometrias del espejo de salida x 116 puntos de Vmem) pero el resultado
nunca se habia escrito.

    lg10(ro [ohm]) = -0.02720 u^3 -0.59296 u^2 -5.11687 u -7.03754
                     con u = lg10(Iex [A])      medio 0.09 %, peor 0.33 %

La fija el ESPEJO DE SALIDA (M5-M8), no la etapa diferencial. En esta celda ese
espejo es fijo: Wo = 0.93, Lo = 1.86 um, y por eso la ley es de UNA variable.
Para otro espejo hay que volver a medir.

### 11.1 CORRECCION (2026-09-03): la primera ley estaba mal, y la conclusion al reves

La version que estuvo aqui hasta hoy era

    lg10(ro) = -5.576 +1.107 lgWo -0.396 lgLo -2.159 lg10(Iex)      9.4 %

ajustada sobre `rox.npz`. **El barrido no servia para esto**: alli `Wo`, `Lo` y
la corriente estaban ACOPLADOS -- la geometria del espejo era la que fijaba la
corriente, no una variable independiente. Evaluar esa ley en el espejo fijo a
una corriente arbitraria es extrapolar. A 20 nA daba **3.5e-17 ohm**, un
disparate que delato el problema.

Se volvio a medir como toca (`ro_fijo.py`): el espejo real, Wo=0.93 / Lo=1.86, y
una fuente de corriente independiente barriendo Iex. (Primer intento fallido:
`I Vdd kd` inyecta en el nodo en vez de drenar, y todas las corrientes salian
cero; corregido a `I<n> <n>d 0`.)

    iex [nA]      ro [ohm]    el LIF pide (1%)    error real
          5       1.36e+10       3.71e+10            2.8 %
         20       4.18e+09       9.72e+09            2.3 %
        100       1.13e+09       1.90e+09            1.7 %
        400       3.55e+08       4.75e+08            1.3 %

**El espejo no cumple el 1 % en NINGUN punto, y el error es PEOR a corriente
BAJA** -- lo contrario de lo que decia el "cruce en 126 nA". La medida buena
cambia a quien afecta: el estudio de acoplamiento con NeuronSpec (seccion 14)
dice que la demanda se concentra en corrientes bajas, mediana 17.6 nA. Ahi el
error es 2.3 %, no 0.2 % como prometia la ley vieja.

Sigue siendo un problema de circuito, no de modelado, y se arregla en el espejo
(alargar `Lo`, cascodear). Cuanto ayuda cada cosa NO esta medido: la ley nueva
es de una sola variable a proposito, porque es la unica que este barrido
controla de verdad.

### 11.2 Los dos motores compuestos

    ENCODER 100 nA G=0.35 -> entrega 100.1-294.3 nA, ro = 4.6e+08 ohm
       LIF con ese rango  -> f de 494.6 a 1454.1 kHz
       AVISO: a 294 nA el LIF vera 1.4 % de error, no 1 %

`encoder_design.source_ro(iex)` y `iex_para_ro(tol)` estan en `laws.py`, y el
solver lo reporta en `requirements["source_ro para NeuronSpec"]` listo para
pasarlo a `NeuronSpec(source_ro=...)`.

## 12. El punto nominal y la celda original del equipo (2026-09-01)

La primera version del motor usaba como nominal el centro geometrico de la caja
-- arbitrario, y no corresponde a ninguna celda que exista. El nominal de la
neurona no es asi: son las dimensiones de `sch/lif/neurona_input_current.sch`,
simuladas, y sus leyes las predicen al -1.4 %.

La celda original del equipo NO puede servir de nominal: tiene `Ld = 10 um`,
muy fuera del `Ld = 1.60` que fijamos.

Asi que se define uno y se SIMULA.

**Criterio (decision del equipo): el punto mas COMODO DE CARACTERIZAR**, no el
mas util ni el mas barato. En este proyecto eso significa una cosa concreta y
medida: lejos de los bordes de la caja.

    distancia al borde        lgIa      lgIb      lgG
    pegado  (<5 %)           0.79 %    0.74 %    0.24 %
    cerca   (5-15 %)         0.62 %    0.55 %    0.26 %
    medio   (15-30 %)        0.46 %    0.32 %    0.29 %
    centro  (>30 %)          0.44 %    0.50 %    0.25 %

Buscado CON EL PROPIO MOTOR: la peticion cuya solucion cae mas adentro es
`iex_min=80, gain=0.40, tradeoff=0.5`, con los cuatro ejes al 43-53 % del borde.

    NOMINAL = Wd 0.725  Wl 0.947  Ll 0.394  L9 1.811   (Ld 1.60, W9 0.26)

### 12.1 Tabla de validacion, al estilo de la del LIF

    diseño     MOTOR predice                  NGSPICE                    error
    nominal     80.0/286.5 G=0.400 V(a)=582   79.6/285.4 G=0.401 583    -0.5 -0.4 +0.1 %
    rapido     300.2/742.4 G=0.450 V(a)=523  298.1/734.5 G=0.453 524    -0.7 -1.1 +0.5 %
    lento       30.0/101.7 G=0.280 V(a)=543   29.3/ 99.0 G=0.279 543    -2.3 -2.7 -0.4 %

Peor error: 2.7 %. La del LIF tiene 2.5 %.

**El criterio se verifica solo**: el nominal interior es el que mejor valida
(0.5 %) y `lento`, el peor (2.7 %), es precisamente el que tiene `Ll = 0.280`,
pegado al borde de la caja.

### 12.2 La celda original del equipo, simulada

    Wd=0.5  Ld=10  Wl=2  Ll=0.28  Wb=0.5  Lb=0.28
       ->  40.0 / 56.0 nA     G = 0.075     V(a) = 41 mV

Tres problemas a la vez:

  * **Ganancia 0.075**, cuatro veces menor que cualquiera de los tres diseños de
    referencia (0.28-0.45).
  * **Excursion de 1.4x** (40 a 56 nA) en vez de ~3x: el encoder apenas modula.
    Sobre la ley del LIF (16.41 kHz/nA) eso es un rango de disparo de 656 a
    919 kHz, cuando podria cubrir de 490 a 1450 kHz.
  * **`V(a) = 41 mV`**: M9 en TRIODO, no saturado. Muy por debajo del umbral de
    150 mV. Era una de las tres sospechas del principio de la caracterizacion,
    ahora confirmada por simulacion directa.

Es el argumento mas concreto para redimensionar la celda: no es una mejora
marginal, es que la celda actual no funciona como encoder.

### 12.3 El nominal se DERIVA, no se clava

El nominal de la neurona son cuatro numeros en el codigo, y esta bien: el suyo
es una CELDA MEDIDA, un hecho fisico. El del encoder es el resultado de una
busqueda, asi que clavarlo lo congela: si mañana se reajustan las leyes o cambia
la caja, esos numeros dejan de ser el punto mas comodo y nadie se entera.

Lo que se guarda es EL CRITERIO:

    NOMINAL_SPEC = {"iex_min": 80.0, "gain": 0.40, "tradeoff": 0.5}
    nominal()  ->  {'Wd': 0.725, 'Wl': 0.947, 'Ll': 0.394, 'L9': 1.811}

`nominal()` resuelve esa peticion con el propio motor y cachea el resultado. La
validacion en ngspice se anota como comentario, con la fecha y la version de las
leyes con que se hizo.

Es lo que el codigo esta para hacer: si el solver sabe encontrar el punto, el
punto no deberia estar escrito a mano en otro sitio.

## 13. Capacidad de entrada (2026-09-01)

`NeuronSpec` reporta su `C_in` (2.03 fF) y acepta `c_in_max`, y su propio
comentario explica la dualidad: "nuestro `c_load` es el `C_in` de la celda
siguiente, y nuestro `C_in` es el `c_load` de la anterior". El encoder no tenia
esa magnitud: la cadena estaba completa por el lado de la salida (`source_ro`,
seccion 11) pero no por el de la entrada.

En un MOS la impedancia de entrada en continua es practicamente infinita (solo
fuga de puerta), asi que lo que importa es la CAPACIDAD.

Medida con `.ac` a 1 kHz y una fuente por geometria (300 puntos; con una sola
fuente compartida se suman todas las puertas y sale la capacidad total):

    C_in de 0.86 a 5.65 fF   (mediana 2.31)

    lg C_in = -14.4707 +0.9340 lgWd -0.0104 lgWl +0.0120 lgLl -0.0904 lgL9
                                     externo 0.73 % con solo 5 coeficientes
                                     (la cuadratica de 15 da 0.45 %)

**Depende casi solo de `Wd`**, con exponente 0.934 -- cerca de 1, como
corresponde a una capacidad de puerta proporcional al ancho con `Ld` fijo.
`Wl` y `Ll` estan en 0.01: no intervienen.

El 0.934 en vez de 1.0, y el termino de `L9` (-0.09), son el efecto Miller:
`Cgd` se multiplica por (1 + ganancia), y la ganancia si depende de las otras
dimensiones.

### 13.1 La cadena, ya completa por los dos lados

    lo que alimente al encoder debe mover     2.35 fF   (C_in del encoder)
    el encoder debe mover                     2.03 fF   (C_in del LIF)
    el LIF puede mover hasta                132.00 fF

`EncoderSpec` acepta `c_in_max` y avisa si se pasa. La cota rara vez mordera:
bajar `C_in` exige reducir `Wd`, que es justo lo que se paga en apareamiento
(`sigma_Vos` va con `Wd^-0.44`).

## 14. Competicion de formas: por que 35 terminos y no menos (2026-09-02)

Las leyes del encoder mapean 4 dimensiones a un escalar, asi que la competicion
no es entre familias de curvas (como en el integrador) sino entre FORMAS: bases
con distinto grado maximo por variable.

    forma (grado por Wd, Wl, Ll, L9)   terminos   Iex(-)   Iex(+)   ganancia
    potencia pura        (1,1,1,1)            5   12.73%    8.60%    3.51%
    cuadratica completa  (2,2,2,2)           15    2.98%    2.50%    0.77%
    cubica solo en Ll    (1,1,3,1)           20    3.92%    1.16%    1.18%
    cubica en Ll y L9    (1,1,3,3)           25    3.27%    0.87%    1.14%
    cubica Ll + cuad     (2,2,3,2)           32    0.95%    0.82%    0.46%
    cubica completa      (3,3,3,3)           35    0.65%    0.58%    0.26%

`Ll` es la unica que necesita grado alto -- coherente con el ranking de terminos,
donde `Ll^3`, `Ll^2` y `Ll` entran de los primeros. Pero limitar el grado alto a
`Ll` no gana a la cuadratica completa salvo en `Iex(+)`.

**Con el liston de 95 % de precision, la cuadratica de 15 terminos parece bastar
(2.98 / 2.50 / 0.77 %). No basta.** El lazo cerrado sobre los mismos 25 pedidos:

                        |error| Iex(-)    peor    dentro de +-5 %
    cuadratica (15)          2.57 %      8.31 %      21/25
    cubica     (35)          0.63 %      2.72 %      25/25

Los 20 terminos extra compran pasar de 21 a 25 de 25 peticiones dentro del
liston, y bajar el peor caso de 8.31 % a 2.72 %.

**El error de la LEY y el error del MOTOR no son lo mismo**: el solver busca los
extremos de la caja, donde la ley tiene menos apoyo, asi que el 2.98 % de la ley
se convierte en 8.31 % de peor caso en el lazo. Cualquier decision de recortar
terminos hay que tomarla sobre el lazo, no sobre el ajuste.

DECISION: se quedan los 35 terminos por salida.

## 15. Cierre de la caracterizacion (2026-09-02)

### 15.1 `Vcm` es condicion de validez, no variable

40 geometrias x 7 valores de modo comun:

    Vcm [V]    Iex(-)    Iex(+)   ganancia   V(a) [mV]
      1.20     0.668x    0.771x    0.989x       242
      1.40     0.911     0.938     0.996        370
      1.55     0.987     0.990     0.998        477
      1.65     1.000     1.000     1.000        552
      2.10     1.014     1.015     1.006        902

**De 1.55 a 2.10 V la corriente cambia 1.4 % y la ganancia 0.6 %.** Por debajo
cae, porque `V(a)` sigue a `Vcm` y M9 pierde margen.

    LAS LEYES VALEN PARA Vcm >= 1.55 V

Un ataque asimetrico (una sola entrada moviendose) desplaza `Vcm` +-70 mV en
torno a 1.65: cae de lleno en la zona plana.

### 15.2 `I_ref` del bloque de bias: es el mayor consumidor del chip

42 geometrias del divisor M10/M11. `I_ref` va de 5.1 a 169 uA.

    lg I_ref = -4.7543 +0.3476 lgWn -0.3625 lgLn +0.5604 lgWp -0.7865 lgLp
                                        potencia 15.09 %, cuadratica 1.55 %

**Esta ley esta SUPERADA -- ver 15.2.1.** Su barrido llegaba a `Ln <= 3`,
`Lp <= 4`, asi que NO CUBRIA la recomendacion (`Ln = 10, Lp = 20`) que sale
tres parrafos mas abajo. Usarla ahi es extrapolar.

    variante                      uA     net1 (tt)   seguimiento ff->ss
    equipo 0.5/0.28 : 0.5/0.28   43.17     1.311 V         44 mV
    ambos L = 2.0                 5.07     1.258           65
    ambos L = 10                  0.96     1.250           66
    Ln = 10  Lp = 20              0.58     1.112           99
    0.22/20 ambos                 0.25     1.259           59

    para comparar: neurona LIF 14.6 uA, etapa diferencial 2.93, integrador 0.05

**El divisor del equipo consume 43 uA: tres veces la neurona y quince veces la
etapa diferencial que si optimizamos.** Es el mayor consumidor de todo lo
medido, y el arreglo son las longitudes.

**RECOMENDACION: `Ln = 10 um`, `Lp = 20 um`** -> 0.58 uA (74x menos) con
`net1 = 1.112 V` y el doble de seguimiento de esquina (99 mV contra 44). Gana en
consumo Y en seguimiento a la vez.

Sigue sin llegar a los 279 mV que el diferencial necesita (seccion 6.2), asi que
la conclusion de la seccion 7 se mantiene. Pero deja de dominar el consumo.

### 15.2.1 Rehecho: la caja no cubria la propia recomendacion (2026-09-03)

Al meter `I_ref` en el motor salio el problema: la ley de 15.2 se ajusto sobre
72 divisores con `Ln <= 3` y `Lp <= 4 um`, y el punto recomendado (`Ln = 10,
Lp = 20`) esta fuera. Extrapolar -- el mismo error que se acababa de cazar en
`source_ro` (seccion 11.1). Sobre la caja ancha esa forma da **41 % de media y
539 % en el peor caso**.

Barrido nuevo `iref2.npz`: 900 geometrias, `Wn/Wp 0.22-4.0`, `Ln/Lp 0.28-25`,
de 0.198 a 341.8 uA (3.24 decadas).

    forma                     coef   externo    peor
    potencia                     5    41.29%  538.72%
    cuadratica                  15     5.82%   51.27%
    cubica                      35     3.15%   21.17%     <- elegida
    cuartica                    70     1.27%   25.52%

La cuartica baja la media pero **empeora la cola** (25.5 % contra 21.2 %): son
70 coeficientes ajustando los bordes. La curva de aprendizaje de la cubica es
plana (3.07 % con 225 muestras, 3.15 % con 630): limite de MODELO, no de dato,
asi que mas simulacion no ayudaria.

**No colapsa a (Wn/Ln, Wp/Lp).** Probado hasta grado 6: se estanca en 6.7 % y
el residuo correlaciona con `Wp` (-0.62) y `Lp` (-0.41) por separado. El lado
pmos no obedece a la relacion de aspecto sola. Es lo mismo que pasa en el
encoder: la ganancia y `V(a)` colapsan, la corriente no.

Los peores casos son desajustes extremos de forma -- `Wn=0.22/Ln=25` contra
`Wp=2/Lp=0.28`, mil a uno -- que nadie va a dibujar. Y restringir la caja a
consumo bajo no mejora nada: con `I <= 5 uA`, 2.87 % contra 3.15 %. El error no
esta en un rincon, esta repartido: 3.6 / 3.1 / 3.0 / 3.5 % por decada.

Validacion externa POR GEOMETRIA, 12 divisores fuera de la malla:
**2.14 % medio, 3.61 % peor**. Los dos puntos que importan:

    divisor del equipo  0.5/0.28 : 0.5/0.28   ngspice 43.158 uA   ley 42.171
    recomendado         0.5/10   : 0.5/20     ngspice  0.585      ley  0.576

Que confirma por medida directa los dos numeros que llevamos citando.

En el paquete: `i_ref(Wn, Ln, Wp, Lp)` en uA y `en_caja_bias(...)`, con caja
PROPIA (`coeffs.CAJA_BIAS`) porque sus cuatro variables no son ninguna de las
cuatro del resto.

### 15.3 Variacion global estadistica: NO disponible

`sw_stat_global` existe (109 referencias en el modelo) pero requiere las
secciones `statistical` + `nfet_03v3_stat`/`pfet_03v3_stat` y los subcircuitos
`_dss`. Esas secciones **no parsean en esta version de ngspice** ("Syntax error:
letter [$]", sin que haya ningun `$` en la seccion). Los modelos `typical`
llevan `vth0` clavado, asi que con ellos `sw_stat_global` no hace nada.

**Lo que si funciona es el desapareamiento** (`sw_stat_mismatch=1` sobre
`typical`, via `fets_mm`), que es lo que se uso en la seccion 5.

AVISO DE METODO: el primer intento dio **sigma exactamente 0.0 % en 200 tiradas**
-- un fallo silencioso, no un resultado. Corrio limpio, escribio su fichero y
devolvio numeros bien formados, todos identicos. Sin mirar la sigma se habria
reportado "la variacion global es despreciable", que es falso Y tranquilizador.
Misma familia que el pin de jupyter-client que nunca se escribio y el `wrdata`
con el nombre de vector mal: **comprobar que el resultado tiene la FORMA que
deberia antes de interpretarlo.**

Queda como limitacion: las 5 esquinas del PDK (que son extremos, no una
distribucion) es lo que tenemos para proceso.

## 16. Por que 35 coeficientes: la anatomia de las cubicas (2026-09-03)

Pregunta de Euler: se hace raro necesitar 35 parametros para una curva. Medido,
la respuesta es que **la curva no es complicada -- lo complicado es que son
cuatro y se estorban entre si**.

Primero, el numero no es una eleccion: 35 es el TAMAÑO COMPLETO de una cubica
en 4 variables (1 constante + 4 lineales + 10 cuadraticos + 20 cubicos). La
cuenta explota por combinatoria.

### 16.1 Cada curva por separado es casi una parabola

Rodajas 1-D reales (tres variables clavadas en el nominal, 13 puntos a todo el
ancho de la caja, simuladas -- `siete.npz` es muestreo aleatorio y no tiene
rodajas):

           recorre     recta   parabola    cubica
    Wd     0.38 dec     7.8 %     0.4 %     0.3 %
    Wl     0.79         2.5 %     1.1 %     0.3 %
    Ll     0.93        35   %     6.5 %     0.7 %
    L9     1.05         5.6 %     1.4 %     0.5 %

Ninguna pide mas de 3-4 numeros. `Ll` es la unica de verdad curvada; las otras
tres son casi rectas en log-log.

### 16.2 Lo que cuesta son los CRUCES, no la curvatura

Familias anidadas, cada una REAJUSTADA desde cero (nunca podando, trampa 5):

    constante + lineal                        5 coef   11.16 %
    + curvatura propia, SIN cruces           13         6.59 %
    lineal + cruces de 2, SIN curvatura      11         9.55 %
    cuadratica completa                      15         2.97 %
    cuadratica + cruces triples              19         2.75 %
    CUBICA COMPLETA                          35         0.68 %

La segunda fila es la clave: **toda la curvatura propia del mundo, sin cruces,
se queda en 6.59 %**. De los 35 terminos, 13 son de una sola variable y **22 son
cruces**. No describimos una curva retorcida, describimos como se deforman
cuatro curvas suaves unas con otras.

No es sobreajuste, que es la sospecha razonable: con 80 muestras de
entrenamiento y 35 coeficientes ya da 0.87 % FUERA DE MUESTRA, y con 560 da
0.68 %. Curva plana desde el principio -- modelo saturado, no forzado. Son 800
geometrias, 23 datos por coeficiente.

### 16.3 Competencia de familias ESTRUCTURADAS: factorizar no funciona

Idea de Euler: si los cruces son "la pendiente de unas depende de las otras",
eso deberia factorizar. Probado, y no.

    familia                                 coef   externo
    cubica completa (referencia)              35     0.68 %
    cuadratica completa                       15     2.97 %
    P3(Ll) x lineal(Wd,Wl,L9)                 16     6.78 %
    P3(Ll) x [lineal+cruces](Wd,Wl,L9)        28     4.15 %
    P3(Ll)xlin + P2(L9)xlin(Wd,Wl)            22     3.83 %
    P3(Ll)P2(L9) x lineal(Wd,Wl)              36     3.47 %   <- MAS coef, peor
    RANGO 1:  f(Ll) * g(Wd,Wl,L9)              7     6.94 %

Y no es que `Ll` fuera la variable equivocada -- probadas las cuatro como eje de
factorizacion (`P3(v) x lineal(resto)`, 13 coef): Wd 9.95 %, Wl 10.92 %,
Ll 6.81 %, L9 9.33 %.

### 16.4 Por que no factoriza: las interacciones son SUPERADITIVAS

Partiendo de la aditiva (13 coef, 6.59 %) y añadiendo los cruces de UNA pareja,
reajustando todo:

    Wd x L9   -> 4.73 %  (gana 1.86)      Wd x Wl  -> 6.53 %  (gana 0.06)
    Wl x L9   -> 5.86 %  (gana 0.73)      Wd x Ll  -> 6.52 %  (gana 0.07)
    Ll x L9   -> 5.97 %  (gana 0.62)      Wl x Ll  -> 6.57 %  (gana 0.01)
                                          suma de las seis = 3.35
    TODAS a la vez (31 coef)  -> 1.05 %   (gana 5.54)
    + los triples   (35 coef) -> 0.68 %

**Las parejas por separado ganan 3.35 puntos; juntas ganan 5.54.** No hay una
interaccion dominante que aislar: solo funcionan las seis a la vez, y encima
quedan 0.37 puntos que solo dan los terminos de TRES variables.

### 16.5 Conclusion

**35 no es que no lo hayamos intentado, es el resultado de intentarlo.** Todas
las formas estructuradas son peores a igualdad de tamaño, y una de ellas es
peor gastando mas. Lo unico que se acerca es dejar fuera los triples (31 coef,
1.05 %): ahorra 4 numeros y multiplica el error por 1.5, y la seccion 14 ya
enseño que el motor castiga las leyes peores mas de lo que sugiere su error.

**Y esto contesta tambien por que el LIF si tiene ecuaciones cortas**: las suyas
son separables, cada variable por su lado. Aqui la forma aditiva se estanca en
6.59 %. No es que lo hayamos hecho peor -- es que este circuito acopla sus
cuatro dimensiones y el del LIF no.
