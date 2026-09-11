# Todas las ecuaciones (CapiMagics, GF180MCU)

Generado desde los ajustes. Procedencia y metodo: los knowledge base de
`sch/encoder/results/` y `sch/integrator/results/`.

---

## ENCODER

Dimensiones fijas: `Ld = 1.60 um`, `W9 = 0.26 um`, espejo `Wo = 0.93`, `Lo = 1.86 um`.
Variables libres: `Wd`, `Wl`, `Ll`, `L9` en um.
Validas para `Vbias = 1.2 V`, `Vcm >= 1.55 V`, y dentro de la caja
`Wd 0.26-1.80  Wl 0.30-2.70  Ll 0.28-0.62  L9 0.80-3.78`.

En todas: **a = lg10(Wd), b = lg10(Wl), d = lg10(Ll), e = lg10(L9)**

## Forma corta, para leer

Las cuatro leyes de abajo son cubicas de 35 terminos. Eso NO significa que la
curva sea complicada: cada variable por su cuenta es casi una parabola, y 22 de
los 35 terminos son cruces (seccion 16 del knowledge base). Pero para leerlas y
citarlas hay una escritura mucho mas corta.

Desarrollando el MISMO polinomio alrededor del nominal (cambio de base exacto,
residuo 2e-14), la constante pasa a ser el valor nominal y los coeficientes
lineales pasan a ser los exponentes locales. Es decir, una ley de potencia:

```
  Iex(-)  =  80.1 nA  x  (Wd/0.725)^-0.468  (Wl/0.947)^-0.865
                         (Ll/0.394)^+2.510  (L9/1.811)^-1.609

  G       =  0.400    x  (Wd/0.725)^+0.452  (Wl/0.947)^-0.436
                         (Ll/0.394)^+0.533  (L9/1.811)^+0.024

  V(a)    =  0.582 V  +  0.189 lg10(Wd/0.725)  +  0.234 lg10(L9/1.811)
```

Con eso se lee el circuito de un vistazo: **`Ll` manda en la corriente**
(exponente +2.5), `L9` va detras (-1.6), y `Wd` casi no interviene (-0.47). En
la ganancia los cuatro pesan parecido salvo `L9`, que sale en **+0.024**: la
ganancia no depende de la cola, medido dos veces en barridos independientes. Y
`V(a)` solo ve `Wd` y `L9` -- `Wl` y `Ll` salen exactamente en cero.

**Esto es para LEER, no para calcular.** En media caja alrededor del nominal esa
forma de potencia da 5.8 % en `Iex`, 0.92 % en la ganancia y 2.1 mV en `V(a)`;
el motor usa las cubicas completas, que dan 0.65 / 0.26 / 0.12 % en toda la
caja. Y los exponentes son DERIVADAS PARCIALES: a especificacion constante las
otras variables se reacomodan y el efecto neto puede invertirse (paso con `Ld`
en sigma_Vos).

Ojo tambien con lo contrario: **truncar la version SIN centrar es catastrofico**
-- quedarse en grado 2 da 5300 % de error medio, porque los terminos que se van
estaban compensando a los que quedan. Centrada, truncar a grado 2 si tiene
sentido (5.2 % en toda la caja, 0.63 % cerca del nominal). Es la misma trampa de
siempre, y el centrado es lo que la desactiva.

Reproducible con `sch/encoder/tb/scripts/forma_legible.py`, que ademas escribe
otras dos reagrupaciones exactas: agrupada por (Wd, Wl) con coeficientes que son
polinomios en (Ll, L9), y anidada en Horner.

---

### Iex a Vdif = -0.14 V

```
lg10( Iex(-) [A] ) =
    +14.96059·d^3 +12.38461·d^2 -5.81538 +4.94997·d -3.39257·d^2e 
    -1.61856·de -1.55106·e -1.43047·bd^2 -1.04579·b -0.84960·bd 
    -0.79106·ad^2 -0.73845·bde -0.68606·e^2 -0.58556·ae +0.54977·e^3 
    -0.42168·a +0.34915·ae^2 -0.33700·ad -0.27317·a^2 -0.19508·abd 
    -0.18913·b^2d +0.15210·a^2d -0.15077·de^2 +0.14529·b^3 +0.12954·a^2e 
    -0.12871·b^2e +0.10243·abe -0.07333·b^2 +0.06787·ade +0.06042·be^2 
    +0.04883·a^2b -0.02990·ab^2 -0.00649·a^3 +0.00562·be -0.00515·ab 

   35 terminos.  Error externo 0.65 %
```

### Iex a Vdif = +0.14 V

```
lg10( Iex(+) [A] ) =
    +12.43460·d^3 +10.91225·d^2 -5.38055 +4.64131·d -2.82093·d^2e 
    -2.10910·bd^2 -1.55140·de -1.19069·bd -1.15272·b -1.07277·e 
    +0.43901·ad^2 -0.33901·bde +0.29363·e^3 -0.24891·b^2d -0.24869·e^2 
    +0.22388·ad +0.19559·a +0.17267·b^3 +0.14236·de^2 -0.11666·b^2 
    -0.11608·ae +0.09500·be^2 +0.08029·ade -0.06968·a^2e +0.05702·b^2e 
    -0.04287·a^3 +0.04012·abd +0.03676·ae^2 +0.02847·a^2d -0.01403·be 
    -0.01199·ab +0.01158·abe -0.00441·ab^2 -0.00198·a^2 -0.00130·a^2b 

   35 terminos.  Error externo 0.58 %
```

### dV(x)/dVdif en el centro

```
lg10( ganancia ) =
    +0.78299·d -0.52274·b +0.50544·d^2 +0.49031·a +0.44001·d^3 
    +0.40378·d^2e +0.39314·bd^2 -0.36084·bde -0.24495·b^2d -0.20417·de^2 
    -0.20052·ae +0.13165·de +0.12757·b^2e -0.11984·a^2e +0.11793·b^3 
    +0.11603·be^2 -0.10163·ae^2 +0.10135·bd -0.09021·a^3 +0.08463·be 
    -0.08019 -0.05671·e^2 -0.04802·ad^2 -0.03771·ad -0.03523·a^2 
    -0.03161·b^2 -0.02724·e +0.01355·abe +0.00617·abd -0.00481·ab^2 
    -0.00476·e^3 -0.00383·a^2d -0.00353·ab +0.00343·a^2b +0.00177·ade 

   35 terminos.  Error externo 0.26 %
```

### margen de saturacion de M9

```
V(a) [V] =
    +0.54886 -0.24714·ae +0.24438·e +0.23849·a +0.09058·ae^2 +0.08733·a^2e 
    -0.06496·a^3 -0.06151·a^2 -0.05524·e^3 -0.05127·e^2 +0.01416·de 
    +0.01192·d^2e -0.00937·ad^2 -0.00808·ade -0.00799·b^2d -0.00710·de^2 
    -0.00569·ad -0.00512·d -0.00361·d^2 -0.00308·be^2 -0.00306·b^2 
    +0.00245·d^3 +0.00199·bd^2 +0.00185·bd -0.00176·abd -0.00106·a^2d 
    +0.00079·b +0.00074·a^2b +0.00071·be -0.00071·bde -0.00069·ab 
    -0.00055·b^3 -0.00051·b^2e +0.00036·ab^2 +0.00021·abe 

   35 terminos.  Error externo 0.12 %
```

### Viabilidad: los tres objetivos no son independientes

```
lg10( Iex(+) / Iex(-) )  =   con  A = lg10(Iex(-) [A]),  Gg = lg10(ganancia)
    -2.47104  -0.43038·A  -2.30476·Gg  +0.00867·A²  +0.49599·Gg²  -0.51769·A·Gg

   Error externo 1.26 %.  Reproducida por dos barridos independientes.
```

### Desviacion de entrada por desapareamiento

```
lg10( sigma_Vos [V] ) = -2.2307 -0.4362·a -0.0258·b -1.0681·d -0.0276·e

   Error externo 5.6 %.  Manda `Ll`; `Wl` y `L9` no intervienen.
```

### Impedancia de salida (la que NeuronSpec pide como `source_ro`)

```
Medida CON EL ESPEJO FIJO (Wo = 0.93, Lo = 1.86) y la corriente controlada de
forma independiente.  Con u = lg10( Iex [A] ):

lg10( ro [ohm] ) = -0.02720·u^3 -0.59296·u^2 -5.11687·u -7.03754

   Error medio 0.09 %, peor 0.33 %.  Ley de UNA sola variable: para otro
   espejo hay que volver a medir.

   El LIF pide 1.9 / (tol · Iex) GOhm.  Lo que sale:

        Iex        ro          error que ve el LIF
          5 nA   1.36e+10             2.8 %
         20      4.18e+09             2.3 %
        100      1.13e+09             1.7 %
        400      3.55e+08             1.3 %

   EL ESPEJO NO CUMPLE EL 1 % EN NINGUN PUNTO, y el error es PEOR a corriente
   BAJA.  Importa porque el estudio de acoplamiento con NeuronSpec dice que la
   demanda se concentra ahi (mediana 17.6 nA).

   CORRECCION (2026-09-03).  La version anterior era
     lg10(ro) = -5.5756 +1.1066·lg10(Wo) -0.3963·lg10(Lo) -2.1588·lg10(Iex)
   con 9.4 % de error y la conclusion de que el cruce del 1 % estaba en 126 nA.
   Estaba mal: se ajusto sobre un barrido donde Wo, Lo y la corriente estaban
   ACOPLADOS -- la geometria fijaba la corriente, no era una variable libre --
   asi que evaluarla en el espejo fijo a corriente arbitraria era extrapolar.
   A 20 nA daba 3.5e-17 ohm.
```

### Capacidad de entrada

```
lg10( C_in [F] ) = -14.4707 +0.9340·a -0.0104·b +0.0120·d -0.0904·e

   Error externo 0.73 %.  Depende casi solo de `Wd`.
```

### Corriente del bloque de bias (divisor M10/M11)

Es una ley del DIVISOR, no de la etapa diferencial: sus variables son las
dimensiones de M10 (nmos) y M11 (pmos), y tiene caja propia
`Wn 0.22-4.00  Ln 0.28-25.0  Wp 0.22-4.00  Lp 0.28-25.0` (um).

Aqui: **f = lg10(Wn), g = lg10(Ln), h = lg10(Wp), k = lg10(Lp)**

```
lg10( I_ref [A] ) =
    -4.70578 -0.73342·k +0.65793·h +0.35369·f -0.33760·g -0.23975·fk 
    +0.23425·hk +0.23203·fg +0.22658·fh +0.20487·gk -0.19494·gh 
    -0.11629·h^3 -0.08748·g^2 -0.07752·f^3 -0.07518·fhk +0.06844·h^2k 
    -0.06189·fgk -0.06068·k^2 -0.05821·f^2 +0.05408·ghk +0.05331·fh^2 
    -0.04613·hk^2 -0.04290·gh^2 +0.04190·fgh +0.04018·fk^2 +0.03935·g^2k 
    -0.03422·h^2 -0.02995·g^2h +0.02937·fg^2 -0.02635·f^2g -0.02591·gk^2 
    -0.02072·g^3 +0.01512·f^2k -0.00597·f^2h -0.00573·k^3 

   35 terminos.  Externo 3.15 %; validada POR GEOMETRIA en 12 puntos ajenos
   a la malla al 2.14 % medio, 3.61 % peor.  Barrido `iref2.npz`, 900
   geometrias, de 0.198 a 341.8 uA (3.24 decadas).

   Contra ngspice en los dos puntos que importan:
        divisor del equipo  0.5/0.28 : 0.5/0.28  ->  43.16 uA  (ley 42.17)
        recomendado         0.5/10   : 0.5/20    ->   0.585    (ley 0.576)

   EL DIVISOR DEL EQUIPO CONSUME 43 uA: el MAYOR consumidor de todo lo medido
   (neurona 14.6, diferencial 2.93, integrador 0.05).  Con Ln=10, Lp=20 baja a
   0.58 uA (74x menos) Y DUPLICA el seguimiento de esquina (99 mV contra 44).
   Gana en las dos cosas.

   CORRECCION (2026-09-03).  Hasta hoy esto era una ley de potencia de 5
   coeficientes con 15.1 % de error.  Sobre la caja ancha da 41 % de media y
   539 % en el peor caso: no servia.  Y su barrido llegaba a Ln <= 3, Lp <= 4,
   asi que NO CUBRIA el punto recomendado (Ln=10, Lp=20) que la propia
   caracterizacion aconsejaba.  Rehecho el barrido y subida a cubica.

   No colapsa a (Wn/Ln, Wp/Lp): probado hasta grado 6, se estanca en 6.7 % y
   el residuo correlaciona con `Wp` (-0.62) y `Lp` (-0.41) por separado.
```

### Esquinas: un factor por condicion

```
Iex y ganancia se multiplican por estos factores respecto de typical/27C.
Error del factor unico: 15 % en el peor caso, sobre una deriva real de 5x.

condicion             Iex   ganancia
ff         -40 C     1.874x     1.038x
ff          27 C     1.821x     0.989x
ff         125 C     1.731x     0.945x
fs         -40 C     1.549x     1.115x
fs          27 C     1.540x     1.060x
fs         125 C     1.517x     1.014x
sf         -40 C     0.513x     0.976x
sf          27 C     0.612x     0.953x
sf         125 C     0.702x     0.935x
ss         -40 C     0.376x     1.044x
ss          27 C     0.480x     1.015x
ss         125 C     0.586x     0.998x
typical    -40 C     0.936x     1.041x
typical     27 C     1.000x     1.000x
typical    125 C     1.051x     0.970x
```

---

## INTEGRADOR

Variables: W1, L1, W2, L2 (fuga) y W6, L6, C (inyeccion), mas Iref.
En la fuga: **p = lg10(W1), q = lg10(L1), r = lg10(W2), s = lg10(L2)**

### La fuga: lo que descarga el condensador entre spikes

```
FORMA EN FAMILIA (legible, 4.97 % externo):

  I_fuga / Iref  =  A + B*vm
    A =-2.70348*s^2 +1.83979*s +0.65637 +0.27552*q^2 -0.23976*p^2 
       +0.23447*qs +0.21461*rs -0.20707*q +0.14164*ps -0.11880*pr 
       +0.10076*r^2 -0.07186*r +0.06973*pq +0.03432*qr +0.02272*p 
    B =+1.63500*s^2 -1.09248*s +0.15809 -0.15731*rs +0.11963*p^2 
       -0.11418*ps +0.06475*qs +0.06262*pr -0.06189*q^2 +0.06079*r 
       -0.03425*r^2 -0.03050*qr +0.01587*q -0.01564*pq +0.00952*p 

POLINOMIO CONJUNTO (el que usa el motor, 2.49 % externo):
  I_fuga = Iref * P3(p, q, r, s, vm)     56 terminos, en leyes.npz
  Valida donde I_fuga > 0.7*Iref.
```

### La inyeccion: lo que sube vm con cada spike

```
  dV = P5( lg10(W6), lg10(L6), lg10(C), vm )    126 terminos (90 bastan)
  Error externo 4.14 %.  Coeficientes en leyes.npz.

  NO tiene forma corta: la competicion de familias dio 11.36 % en el mejor
  caso, y el colapso fallo (54 %). Son dos regimenes que no se superponen:
  con C pequeno M6 equilibra dentro de los 32 ns y W6 no importa; con C
  grande la inyeccion queda limitada por corriente y W6 manda.

  El techo (donde dV se anula), medido:
     L6 = 0.28 um -> 2.323 V      L6 = 1.00 -> 1.953 V
     L6 = 0.50    -> 2.037        L6 = 2.00 -> 1.916
```

### La composicion

```
  El equilibrio esta donde la carga que entra iguala a la que sale:

      dV(vm)  =  I_fuga(vm) / (f * C)

  Resolviendo en vm sale la tension de reposo para cada frecuencia de
  entrada. Validado contra ngspice: 7 mV de error medio, 14 mV peor,
  sobre tres diseños muy distintos. Eso es 0.6 % sobre 2.2 V.
```

---

## Lo que NO se puede hacer con estas ecuaciones

**Truncarlas.** Anular los coeficientes pequenos de un polinomio da errores
de 10^66: los terminos que quedan estaban compensando a los que se van. Una
version reducida hay que REAJUSTARLA desde los barridos (`siete.npz`,
`iny3.npz`, `fuga_bar.npz`), no recortarla.

**Usarlas fuera de su caja.** Los rangos de validez estan arriba y no son
decorativos: fuera de ellos no hay medida que las respalde.

**Leer sus exponentes como consejo de diseno.** Son derivadas parciales, con
todo lo demas quieto. A especificacion constante las otras variables se
reacomodan y el efecto neto puede invertirse -- paso con `Ld` en sigma_Vos.
