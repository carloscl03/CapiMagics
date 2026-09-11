.param Wd=0.5u
.param Ld=10u
.param Wl=2u
.param Ll=0.28u
.param Wo=0.93u
.param Lo=1.86u
.param Wb=0.5u
.param Lb=0.28u
.subckt encoder Vdd Vss Vin Vin_neg Iex_1 Iex_2 Iex_3 Iex_4

* -- par diferencial. L larga y W estrecha (W/L = 0.05) -> subumbral, que es
*    lo que da el rango de entrada amplio.
XM1 x1 Vin     a Vss nfet_03v3 L={Ld} W={Wd} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM2 y1 Vin_neg a Vss nfet_03v3 L={Ld} W={Wd} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0

* -- cargas en diodo: cierran el par y son el lado de referencia del espejo
XM3 x x Vdd Vdd pfet_03v3 L={Ll} W={Wl} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM4 y y Vdd Vdd pfet_03v3 L={Ll} W={Wl} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0

* -- espejos de salida. Iex_1/Iex_2 copian la rama x, Iex_3/Iex_4 la rama y:
*    cuatro pines, pero solo DOS corrientes independientes, duplicadas.
XM8 o1 x Vdd Vdd pfet_03v3 L={Lo} W={Wo} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM5 o2 x Vdd Vdd pfet_03v3 L={Lo} W={Wo} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM7 o3 y Vdd Vdd pfet_03v3 L={Lo} W={Wo} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM6 o4 y Vdd Vdd pfet_03v3 L={Lo} W={Wo} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0

* -- cola y referencia autopolarizada: M11 (pfet) y M10 (nfet) en diodo
*    fijan net1, y net1 fija la corriente de cola de M9.
XM9  a1   net1 Vss Vss nfet_03v3 L={Lb} W={Wb} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM10 nref net1 Vss Vss nfet_03v3 L={Lb} W={Wb} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0
XM11 net1 net1 Vdd Vdd pfet_03v3 L={Lb} W={Wb} nf=1 ad='int((nf+1)/2) * W/nf * 0.18u' as='int((nf+2)/2) * W/nf * 0.18u'
+ pd='2*int((nf+1)/2) * (W/nf + 0.18u)' ps='2*int((nf+2)/2) * (W/nf + 0.18u)' nrd='0.18u / W' nrs='0.18u / W' sa=0 sb=0 sd=0

* -- amperimetros. 0 V: no cargan, solo dan nombre a la corriente.
*    Rama del par: entre el drenador del nfet y el nodo x/y, que asi conserva
*    su conexion al diodo y a las puertas de los espejos.
VAM_X    x1   x    0
VAM_Y    y1   y    0
* Cola: entre las fuentes del par y el drenador de M9. Ninguna puerta en medio.
VAM_TAIL a    a1   0
* Referencia: la corriente que fija net1, y con ella la cola.
VAM_REF  net1 nref 0
* Salidas: entre el drenador del espejo y el pin. Ninguna puerta en medio.
VAM_1    o1 Iex_1 0
VAM_2    o2 Iex_2 0
VAM_3    o3 Iex_3 0
VAM_4    o4 Iex_4 0
.ends
