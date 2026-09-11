# Caracterización del integrador (CapiMagics, GF180MCU)

Celda: `integrator_final_mike` — la que tiene layout en `layout/integrator/`.
Medido 2026-09-01/02 con ngspice sobre gf180mcuD.

> **DECIDIDO (2026-09-02, Euler): el circuito es `integrator_final_mike`**, el
> que está en el layout. Los otros dos esquemáticos de `sch/integrator/`
> describen topologías distintas y quedan descartados. Ver sección 1.

## 1. Cuál es el circuito

    integrator_final_mike.sch   <- EL DEL GDS
      M1 pfet 1u/0.28u   diodo, de vm a vg
      M2 nfet 1u/0.28u   espejo, sumidero desde vg
      M3 nfet 1u/0.28u   diodo de la referencia (I_50n)
      M6 nfet 1u/0.28u   inyección del spike
      C3 MIM 2 fF/um2, 17.68 x 17.68 um, m=8  ->  5111 fF (2501 um2)

    tb_integrator.sch           el divisor de lambda del readme
      M2 pfet 10u/0.28u, M4 pfet 10u/2.24u, M1 nfet 1u/0.28u
      + inversor de salida M6/M7 (9u/0.28u), C1 ideal de 1 pF

    integrator-3.sch            variante intermedia, 4 condensadores

El `readme.md` deriva el punto de trabajo de una relación `lambda2/lambda1 =
0.28` entre longitudes de canal. **Esa teoría describe `tb_integrator`, no el
circuito del GDS**: `final_mike` usa un espejo de corriente, no un divisor de
lambda, y por eso todas sus longitudes volvieron al mínimo.

El netlist instancia `cap_mim_2f0fF`, que es el nombre del SÍMBOLO de xschem y
no existe como modelo del PDK (son `cap_mim_2f0_m2m3_noshield` y sus variantes
por par de metales). Tal cual, no simula.

## 2. Qué hace

Filtro paso-bajo no lineal, no un contador de spikes. Cada spike enciende M6
durante 32 ns y empuja `vm` hacia un techo; entre spikes, M1+M2 lo drenan.
Se estabiliza donde la carga que entra por segundo iguala a la que sale, y ese
punto depende de la FRECUENCIA de entrada.

**El spike no inyecta carga fija**: M6 es un nfet con la fuente en `avdd`, así
que conduce mientras `Vext - vm > Vth` y se corta solo. El empujón es
proporcional a lo que falta para el techo, no una cantidad constante.

    partiendo de   salto por spike de 32 ns
      0.50 V            +1241 mV
      1.00 V             +857 mV
      1.50 V             +494 mV
      2.00 V             +166 mV
      2.50 V               -6 mV   <- techo alcanzado

## 3. El método: dos bloques separables

Los dos mecanismos usan transistores distintos, así que se caracterizan por
separado y se componen:

    la FUGA        M1, M2, M3 + Iref     ->  barrido DC, instantáneo
    la INYECCIÓN   M6 + C                ->  un pulso, 1.5 us de transitorio
    en común       solo el condensador

El estado estacionario sale de resolver `salto(vm) = fuga(vm)/(f*C)`, sin
simular trenes largos. Simular el tren directamente costaba >26 min por punto;
así son segundos.

**El modelo compuesto valida al -4.3/+1.2%** contra transitorios directos en el
diseño original, pero se equivocó un +25% en un diseño lejano y un +59% en
sensibilidad en otro. Sirve para explorar, NO para publicar cifras.

## 4. La fuga: la planitud la manda `L_leak` y solo `L_leak`

93 geometrías barridas en DC. Métrica: cuánto varía la corriente dentro de su
rango útil (desde que conduce hasta 3.0 V).

    L_leak (espejo)       0.28 -> 4.8      1.0 -> 1.4      4.0 -> 1.4
    L1 (diodo pfet)   0.28 -> 1.9      1.0 -> 1.9      4.0 -> 1.7
    W_leak                0.5  -> 1.6      1.0 -> 1.7      2.0 -> 1.9
    W_leakpass                0.5  -> 1.4      1.0 -> 1.8      2.0 -> 1.9
    Iref              10n  -> 2.0     200n -> 1.4

En el original (todo a 0.28) la fuga va de 6.8 nA a 195 nA según dónde esté
`vm`: los 50 nA nominales solo se cumplen en un punto, a 1.5 V. Alargando el
espejo a 1.0 um la variación baja a 1.4x. Alargarlo más no aporta.

`L1` conviene dejarlo CORTO: alargarlo sube el punto de arranque de 1.10 a
1.50 V y estrecha el rango útil.

## 5. La inyección: `W_inj` importa según el régimen

30 geometrías x 5 tensiones de partida.

Con C pequeño (1 pF) M6 equilibra el condensador dentro de los 32 ns pase lo que
pase, y `W_inj` casi no importa (1051 vs 1425 mV entre W_inj=0.25 y 4.0). Con C grande
(20 pF) la inyección queda limitada por corriente y `W_inj` manda (factor 7).

`L_inj = 1.0` baja el techo de ~2.6 a ~2.2 V, por el aumento de Vth.

## 6. Resultado: 5.9x de resolución, a igual área

La métrica correcta NO es la sensibilidad sola sino **sensibilidad / rizado**:
el rizado es el propio salto por spike, y una señal con más rizado que
excursión por década no sirve aunque su media responda bien.

Medido con transitorios directos (no con el modelo compuesto):

    diseño                          sensibilidad   rizado   RESOLUCIÓN
    ORIGINAL  W_inj=1.0/0.28 Iref=50n    180 mV/dec    71 mV       2.5
    MEJOR     W_inj=0.25/1.0 Iref=25n    280 mV/dec    19 mV      15.0
              L_leak=1.0u, C sin cambiar                            5.9x

Gana en las dos cosas: más sensibilidad Y un tercio del rizado, con el MISMO
condensador y por tanto la misma área. Son tres dimensiones:

    L_leak (y L3, apareado)   0.28 -> 1.00 um     aplana la fuga
    W_inj / L_inj               1.0/0.28 -> 0.25/1.0   suaviza la inyección
    Iref                  50 -> 25 nA

## 7. Tres correcciones que me hice durante el trabajo

Valen más que los aciertos, y las tres son del mismo tipo:

1. **"El original satura antes de 1.5 MHz"** — falso. Era el techo de mi
   ventana de cálculo (limité `vm` a 2.40 V), no del circuito.
2. **"El condensador de 5 pF es desproporcionado"** — falso. Es lo que compra
   la resolución. Bajarlo a 1 pF dispara el rizado a 739 mV y el circuito deja
   de servir. El equipo eligió un punto del compromiso área/resolución, no
   cometió un error.
3. **Optimicé sobre una métrica incompleta.** El modelo compuesto solo predice
   la media y no sabe nada del rizado, así que la búsqueda se fue directa a
   quitar condensador — justo lo que el modelo no podía penalizar.

## 8. Inmunidad al riel: aqui el integrador le da una leccion al encoder

Medido con la fuga en `vm = 2.0 V`, barriendo cada riel:

                          dI/dVdd     dI/dVss    con 8 mV de rebote en Vss
    INTEGRADOR original    -0.013      -0.079 %/mV        0.6 %
    INTEGRADOR mejorado    -0.001      -0.008 %/mV        0.1 %
    ENCODER                 0.001       0.487 %/mV        3.8 %

**El integrador es 6-60x mas inmune que el encoder**, y es arquitectura, no
suerte:

  * El integrador copia una CORRIENTE. M3 en diodo genera la referencia y M2 la
    copia; si `Vss` se mueve, las fuentes de ambos se mueven juntas y la `Vgs`
    del espejo se conserva. Autorreferido.
  * El encoder copia una TENSION. La puerta de M9 esta en `Vbias`, que viene de
    otro sitio, y su fuente en el `Vss` local. La diferencia entre los dos
    suelos se convierte en corriente de cola.

**MEDIDO (2026-09-02)**, no interpretado. La primera version de esta seccion
decia "el integrador copia una corriente y el encoder una tension, por eso uno
es inmune" -- eso era una explicacion encima del dato, no algo que saliera de
el, y encima sostenia una recomendacion de diseño. Convertido en medida:

Misma etapa diferencial del encoder, mismo Iex (79.6 nA), cambiando SOLO como se
fija la puerta de M9:

    puerta a una tension fija (Vb = 1.2 V)          dIex/dVss = -0.487 %/mV
    puerta a un diodo alimentado por corriente      dIex/dVss = -0.005 %/mV

**Factor 97.** Con 8 mV de rebote: -3.9 % contra -0.0 %.

(El primer intento de medirlo estaba MAL PLANTEADO: comparaba a puntos de
trabajo distintos, 79.6 nA contra 0.5 nA. Hubo que buscar la referencia que
iguala el Iex antes de que la comparacion significara algo.)

**Lo que la interpretacion ocultaba**: la referencia necesita **2800 nA** para
dar 79.6 nA de Iex. Coincide con la corriente de cola que ya se habia medido,
asi que no es sobrecoste -- pero significa generar y distribuir 2800 nA en vez
de una tension. Un espejo de relacion distinta partiria de una referencia mas
pequeña, y eso hay que medirlo aparte.

Por que importa el rebote: la neurona tira picos de **43 uA** en cada disparo
(cortocircuito de su inversor de entrada). Sobre un riel de 2 um x 500 um
(22.5 ohm), 8 neuronas sincronizadas dan 7.7 mV y 32 dan 31 mV. En una red
neuronal la actividad correlacionada es la norma.

Y `L_leak = 1.0` resulta arreglar TRES cosas por el mismo motivo fisico (mejor
impedancia de salida del espejo):

    planitud de la fuga    4.8x  -> 1.4x
    resolucion             2.5   -> 15.0
    inmunidad al riel      0.079 -> 0.008 %/mV

## 9. Ruido intrinseco: no es el limite

    kT/C con 5111 fF                     28.5 uV RMS
    ruido de disparo de la fuga         125.2 uV RMS  (INDEPENDIENTE de Iref:
                                        menos corriente da menos ruido pero mas
                                        constante de tiempo, y se cancelan)
    ------------------------------------------------
    el rizado del mejor diseño        19000 uV
    la excursion util                350000 uV/decada

El ruido esta 150x por debajo del rizado. El limite es determinista (el diente
de sierra del propio muestreo), no aleatorio.

## 10. Corriente minima

Con el espejo ya alargado, la RESOLUCION es plana de 0.5 a 18 nA: la señal y el
rizado escalan los dos con `Iref` y su cociente no se mueve. Lo que fija el
minimo NO es el circuito sino cuanta excursion necesita la etapa siguiente:

    450 mV/decada -> 25 nA        240 mV/decada -> 12 nA
    350 mV/decada -> 18 nA        100 mV/decada ->  5 nA

Frente a los 50 nA del original hay 2-10x de ahorro, y con MEJOR resolucion en
todos los casos. Pero en escala de chip no mueve la aguja: la neurona consume
14.6 uA, asi que bajar el integrador de 50 a 12 nA ahorra el 0.26 % de una
neurona. Merece la pena por la resolucion y porque una polarizacion mas pequeña
es mas facil de generar y distribuir con precision, no por el consumo.

## 11. Como LECTOR: anchura de la ventana

El integrador es el lector de la tasa de disparo (spikes -> tension), no una
etapa que realimente a otro encoder.

**Cubre todo lo que la neurona puede producir.** El motor del LIF abarca 8.2 a
4500 kHz (2.74 decadas, con `F_MAX` como techo). Midiendo la banda donde la
pendiente supera 100 mV/decada:

    ORIGINAL              3.59 decadas   (1 - 3866 kHz)   resolucion 0.5
    el propuesto por
    resolucion            3.24 decadas   (2 - 2717 kHz)   resolucion 2.6

El original ya sobra: 3.59 > 2.74. Solo se queda corto en el extremo superior
(3866 contra 4500 kHz, un 14 %).

### 11.1 Anchura y resolucion COMPITEN

    L_inj corto (0.28)   techo alto (2.26 V)  -> mas anchura, peor rizado
    L_inj largo (1.00)   techo bajo (1.89 V)  -> menos anchura, mejor rizado

Los limites FISICOS de la ventana de `vm`:

    SUELO   0.925 V   la fuga se anula; por debajo nada baja vm
    TECHO   2.26 V con L_inj=0.28   /   1.89 V con L_inj=1.00

Frente de Pareto A IGUAL CONDENSADOR (5111 fF), con el rizado medido en el PEOR
punto de la banda (el extremo de baja frecuencia, donde cada spike es una
fraccion grande de la excursion):

    decadas   resol |    L_leak    Iref |    W_inj    L_inj |   banda [kHz]
       4.59     1.0 |  0.28    200n |  0.25  0.28 |    1 - 24447
       4.13     2.6 |  0.28    200n |  0.25  1.00 |    2 - 24447
       3.97     3.6 |  0.28     50n |  0.25  1.00 |    1 -  6472
       3.68     3.7 |  1.00     50n |  0.25  1.00 |    1 -  5070
    ------------------------------------------------------------
    ORIGINAL  3.59     0.5 |  0.28     50n |  1.00  0.28

**Se puede tener MAS anchura y 7x mas resolucion que el original, sin tocar el
area.** El cambio que manda es `W_inj` de 1.0/0.28 a 0.25/1.00.

Con C = 20000 fF se llega a 4.69 decadas, pero la anchura tambien se paga en
area, igual que la resolucion.

### 11.2 Lo que esto implica para IntegradorSpec

    pides      la banda a leer (f_min, f_max) y donde caer entre
               resolucion y holgura
    compruebo  si esa banda cabe en las decadas disponibles (3.2 a 4.7 segun
               cuanta resolucion se sacrifique)
    devuelvo   L_leak, W_inj, L_inj, Iref, C
    reporto    pendiente, rizado, impedancia de salida y C_in

`Iref` es una ENTRADA, no un parametro fijo: desplaza la ventana en frecuencia
sin cambiar su anchura. Es el analogo del `Vbias` del encoder.

### 11.3 Impedancias medidas

    C_in (puerta de M6)   0.124 - 1.99 fF segun W_inj/L_inj; 0.295 con el recomendado
                          la neurona mueve hasta 300 fF: no es restriccion
    R_out en vm           1.74-1.82 GOhm a Iref=5 nA
                          0.37-0.40 GOhm a Iref=25 nA
                          plana con vm (5 % de variacion) gracias al espejo largo

**`vm` no puede mover nada**: hace falta un bufer entre el integrador y el
exterior, y su consumo se sumaria al del integrador (25 nA), asi que podria
comerse el ahorro. El inversor M6/M7 de `tb_integrator` NO sirve: es un
comparador, convierte a nivel digital y pierde la tasa.

## 12. CUATRO correcciones mias, todas de la misma forma

Merece la pena listarlas juntas porque el patron es identico: **puse un limite a
la ventana de analisis, el resultado cayo en ese limite, y confundi mi limite
con el del circuito.**

    "satura antes de 1.5 MHz"           mi barrido de vm acababa en 2.40 V
    "el condensador es desproporcionado" mi metrica no incluia el rizado
    "cubre solo 1.78 decadas"            mi ventana de vm era 1.1-2.15, a ojo
    "no cubre ni una sola neurona"       lo mismo

Es la misma familia que los artefactos de borde del encoder (seccion 6 de aquel
documento), pero aqui pasa mas facil porque en el integrador **casi todo lo
interesante vive cerca de un limite**: el techo donde M6 se corta y el suelo
donde la fuga se anula.

**Disciplina**: medir primero donde estan los limites FISICOS, y solo despues
definir la metrica. No al reves.

## 13. LAS LEYES (2026-09-02)

Las curvas interpoladas de la seccion 3 se convirtieron en leyes ajustadas, con
validacion externa POR GEOMETRIA (particion 70/30 de geometrias enteras: si se
parte por punto, las 66 muestras de una misma geometria caen a los dos lados y
el error sale falsamente bajo).

### 13.1 Ley de la fuga

    I_fuga = Iref * P3(lgW1, lgL1, lgW2, lgL2, vm)      56 coeficientes
    dominio: I_fuga > 0.7 * Iref  (~0.99 V de los 1.33 de ventana fisica)
    error externo 2.49 %

**El escalado con Iref es EXACTO por construccion**: se ajusta el COCIENTE
I/Iref, no la corriente. El primer intento, ajustando la corriente directamente,
dio 1554 % de error Y el exponente de Iref con el signo invertido -- señal
inequivoca de que el ajuste estaba dominado por otra cosa (el codo de encendido).

Precision contra cobertura, eligiendo donde cortar el codo:

    umbral      vm cubierto     error externo
      0.3          1.07 V           6.06 %
      0.5          1.03             3.84
      0.7          0.99             2.49   <- el punto util
      0.9          0.90             2.02
      1.0          0.64             2.54   <- peor: se queda sin muestras

### 13.2 Ley de la inyeccion

    dV = P5(lgW6, lgL6, lgC, vm)                       126 coeficientes
    error externo 4.14 %  (3.74 % donde dV > 20 mV, 7.9 mV absolutos)

Hizo falta un barrido de 200 geometrias muestreadas al azar. Con las 60 en
rejilla el error era del 22 % Y LA CURVA DE APRENDIZAJE SEGUIA BAJANDO: faltaba
DATO, no modelo. Distinguir las dos cosas antes de tocar nada ahorra horas -- en
la caja ampliada del encoder la curva era plana y la respuesta fue justo la
contraria (subir el grado, no barrer mas).

El techo, medido con cuatro valores de L_inj:

    L_inj = 0.28 um -> 2.323 +- 0.064 V
    L_inj = 0.50    -> 2.037 +- 0.053
    L_inj = 1.00    -> 1.953 +- 0.062
    L_inj = 2.00    -> 1.916 +- 0.067

**No es ley de potencia, es asintotico**: casi toda la caida ocurre entre 0.28 y
0.5. Con solo dos valores se habria ajustado una recta y salido mal.

### 13.3 La composicion, validada

    dV(vm) = I_fuga(vm) / (f * C)   ->   vm de equilibrio

    diseño          f [kHz]      LEYES      ngspice    error
    ORIGINAL            268     2.194 V     2.208 V    -14 mV
    ORIGINAL           1500     2.337       2.343       -6
    mejorado 25n        268     1.800       1.794       +6
    mejorado 25n       1500     2.000       2.004       -4
    mejorado 12n        268     1.908       1.904       +4
    mejorado 12n       1500     2.048       2.055       -7

    error medio 7 mV, peor 14 mV  =  0.6 % sobre 2.2 V

La version interpolada daba +-4 % cerca del punto conocido y 25-59 % lejos.
Coeficientes en `leyes.npz`.

### 13.4 Que dijo el metodo del colapso

Se busco colapso en los dos bloques, SIN imponer forma (Euler: "no uses
electronica para caracterizar, usa los datos en si mismos"). Resultados
distintos y los dos utiles:

  * **Fuga**: colapsa parcialmente (8.2 % de dispersion) y los exponentes salen
    `W_leakpass +0.01, L1 -0.09, W_leak +0.00, L_leak +0.63`. **Los datos dicen por su cuenta
    que solo `L_leak` interviene.** En prediccion empata con el polinomio (6.58 vs
    6.06 %), asi que no gana en precision, pero SI en diagnostico.
  * **Inyeccion**: NO colapsa (54 %). Son dos regimenes -- con C pequeño M6
    equilibra en los 32 ns y `W_inj` no importa; con C grande la inyeccion queda
    limitada por corriente y `W_inj` manda. Dos escalados distintos no se
    superponen con un solo reescalado.

**Imponer la fisica fallo dos veces**: el cociente `W/L` en el encoder y la
forma de Early (`I/Iref = B(vm-v0)`) aqui, que dio `v0 = -17.9 V` -- un numero
sin sentido -- y 32 % de error. Cuando se conoce la teoria del bloque, se tiende
a usarla de atajo y a saltarse los datos.

## 14. Competicion de familias: local no basta (2026-09-02)

Euler señalo que en el LIF se compitieron FAMILIAS de curvas localmente, con un
liston de ~95 % de precision, y que aqui se fue directo al polinomio. Hecha la
competicion (ajustando cada curva por separado):

    FUGA, ajuste local de cada una de las 93 curvas
      potencia   A*(vm-v0)^n        3 par    0.23 %   <- gana
      cuadratica a+b*vm+c*vm^2      3        0.69 %
      exponencial A*(1-e^-(vm-v0)/w) 3       0.98 %
      lineal     A+B*vm             2        1.71 %
      saturante  A*vm/(vm+b)        2        2.26 %

    INYECCION, 186 curvas
      potencia   A*(T-vm)^n         3       11.36 %   <- la mejor, y no llega
      cuadratica local              3       21.12 %
      exponencial                   3       29.92 %
      lineal / saturante            2       83.19 %

**En la inyeccion ninguna familia llega al liston**: la mejor da 11.36 % con
tres parametros LIBRES por curva, contra 4.69 % del polinomio global. Coherente
con que el colapso fallara al 54 %: la forma cambia con la geometria.

### 14.1 El hallazgo: local no basta, hay que poder MODELAR los parametros

En la fuga la familia ganadora ajusta al **0.23 %** -- cuatro veces por encima
del liston. Y aun asi es inservible:

    familia                                 local    compuesta   coef
    potencia A*(vm-v0)^n, n libre           0.23 %     722 %      45
    la misma con n = 2 fijo                 0.99 %     193 %      31
    lineal A + B*vm, ajustada directa       1.71 %       4.97 %   30
    polinomio conjunto (el que se usa)        --         2.49 %   56

Los parametros de la ganadora son DEGENERADOS: `n` recorre de 0.006 a 5.8 y
`v0` llega a -48 V. Muchas ternas distintas describen la misma curva, el ajuste
local encuentra una cualquiera, y esos parametros no son funciones suaves de la
geometria -- asi que la segunda etapa explota.

**El criterio correcto es local Y MODELABLE.** Con solo el primero, la
competicion de familias premia justo a las peores. La forma de Early
(`I = B(vm-v0)`, seccion 13.4) es un caso particular de esto: fallaba por
degeneracion, no por ser mala fisica.

### 14.2 Decision

Se queda el **polinomio conjunto**: 2.49 % con 56 coeficientes, contra 4.97 %
con 30 de la mejor familia modelable. Si en algun momento el tamaño del paquete
importara mas que la precision, la familia lineal es la alternativa medida.

## 15. Abierto

- El condensador domina el área (2501 de 5210 um2 de celda; el 96% con su
  ruteo). El compromiso resolución/área está medido pero no elegido.
- Floorplan: el pfet M1 está arriba y los nfets abajo, con el array de
  condensadores en medio. `vg`, un nodo de alta impedancia, cruza 55 um por
  encima de las placas.
- `fusetop` y `mim_l_mk` salen con 0 polígonos en el GDS.
- Esquinas y temperatura: nada medido.
- Y sin resolver: cuál de los tres esquemáticos es el que va al chip.

## 15. Por que el LIF admite leyes de potencia y estos bloques no (2026-09-02)

Pregunta de Euler. Tiene respuesta MEDIBLE, y no es la intuitiva.

Prueba: si `log(respuesta) = a(geometria) + b(estimulo)`, la respuesta SE SEPARA
y basta una ley de potencia por geometria mas una curva. Se mide con doble
centrado de la matriz `respuesta[geometria, estimulo]`: lo que queda tras quitar
medias de fila y de columna es la parte NO separable.

    bloque                            separa      residuo
    LIF        f(geom, Iex)           100.0 %      0.0 %   <- dato real
    INTEGRADOR inyeccion(geom, vm)     94.8 %      5.2 %
    ENCODER    Iex(geom, Vdif)         91.1 %      8.9 %
    INTEGRADOR fuga(geom, vm)          70.3 %     29.7 %

Pero eso NO significa que el circuito del LIF sea mas simple. Estrechando el
dominio del encoder:

    ventana Vdif      rango de Iex        separa
      +-0.04 V             54x            99.7 %
      +-0.08               85x            99.2 %
      +-0.15              205x            97.6 %
      +-0.30             7606x            91.1 %
      +-0.60          1522701x            87.6 %

**El encoder separa al 99.7 % si se le da un dominio comparable.** El dato real
del LIF con el que salio 100 % abarcaba solo 3.3x de corriente (60-200 nA).

Y su propio `laws.py` lo reconoce: "`k` tiene curvatura -- la pendiente cae al
subir la corriente (13.33 -> 10.47 kHz/nA)". Ese 57 % de variacion de `k` con
`Iex` ES el termino cruzado que rompe la separabilidad. Su ley de dos exponentes
convive con ese sesgo documentado; aqui se paga en terminos de polinomio en vez
de en sesgo.

**Es la misma ley que gobierna todo el proyecto**: el error de una ley no
depende de la calidad del ajuste sino de cuanto espacio pretende cubrir. Aparecio
al acotar la region del encoder (+-21 % -> +-2 %), al reducir de 6 variables a 4,
al decidir no modelar las esquinas en fino, y ahora explica por que unos bloques
admiten ecuaciones cortas y otros no.

### 15.1 Nota sobre la primera version de esta medida

El primer intento uso la varianza explicada por el primer valor singular tras
centrar por la media GLOBAL, y dio 77.8 % para el LIF -- peor que la inyeccion
del integrador (80.2 %), lo cual era absurdo porque la ley del LIF es separable
por construccion. El fallo: una estructura aditiva en logaritmos es de rango 2
con ese centrado. La prueba correcta es el doble centrado.


---

## Matriz de acoplo

`d(ln salida)/d(ln perilla)` en el punto que devuelve el motor para
`f_min=74, f_max=4500`, **calculada de las leyes**.

```
  dim      resol  sensib  rizado  techo   C_in   R_out  t_resp    vm
  W_leakpass          ~0      ~0      ~0     ~0     ~0   -0.03      ~0     ~0
  W_leak          ~0      ~0      ~0     ~0     ~0   -0.05      ~0     ~0
  L_leak          ~0      ~0   +0.02     ~0     ~0   +0.47   -0.02     ~0
  Iref     -0.71   +0.31   +1.02     ~0     ~0   -0.79   -1.08   -0.06
  W_inj       -0.26   -0.28      ~0     ~0  +1.00   -0.03   +0.05  +0.03
  L_inj       +0.25   +0.28   +0.03     ~0  +0.77   +0.08   -0.13  -0.09
  C        +0.98   -0.02   -1.00     ~0     ~0      ~0   +1.00     ~0
```

**`W_leakpass` y `W_leak` son practicamente INERTES**, y `L_leak` solo mueve `R_out` (+0.47).
Pero la ley de fuga tiene **35 coeficientes en cuatro variables**, tres de las
cuales no hacen nada en el punto de trabajo. Concuerda con el cribado que se
hizo entonces ("W_leakpass, L1 y W_leak se pueden fijar") pero nunca se cuantifico, y la
ley se ajusto igual con las cuatro.

**`C` es la perilla limpia de resolucion**: +0.98 en resolucion, -1.00 en
rizado, ~0 en sensibilidad, +1.00 en tiempo de respuesta. **Toda la resolucion
se paga exactamente en velocidad**, nada mas.

**`Iref` es la sucia**: mueve las siete salidas a la vez (-0.71, +0.31, +1.02,
-0.79, -1.08).

**`C_in` lo fijan `W_inj` y `L_inj`** (+1.00 y +0.77), que son tambien las de la
inyeccion: no se puede ajustar el acoplo con la neurona sin tocar la senal.

### Aviso: el `~0` del techo es LOCAL

El techo sale `~0` para las siete perillas, y sin embargo va de 2.32 a 2.69 V
en la caja. La razon es que casi todo el cambio ocurre entre `L_inj` = 0.28 y
0.50, y el punto nominal tiene `L_inj` = 1.0, ya en la zona plana:

```
  techo(W_inj=0.5, L_inj)   0.30 -> 2.666    1.00 -> 2.342
                      0.50 -> 2.413    1.99 -> 2.317
```

Una matriz de acoplo es una derivada **local** y puede esconder una no
linealidad fuerte a dos pasos. Vale para saber que tocar, no para extrapolar.

**Nota**: el `1.92-2.73 V` que decia este documento era un borde de barrido --
la malla de `V0` acababa en 2.45 V, asi que no se midio el techo sino el final
del escaneo. El rango real es **2.32-2.73**. `laws.py` ya lo corregia; la
correccion no habia llegado ni aqui ni a `spec.py`.
