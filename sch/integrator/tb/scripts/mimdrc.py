"""Un MIM pelado de gLayout, con DRC. Decide de quien es el fallo.

MIMTM.2 = "MiM bottom plate surrounds contact < 0.4um". En layer_output salen 6
violaciones (2 reales, una por neurona) y las coordenadas dibujan una tira de
0.28 um -- el ancho minimo de metal -- donde hacen falta 0.4.

Si el MIM violado SOLO ya viola  -> es del generador de gLayout
Si sale limpio                   -> es de como lo conecta el notebook del equipo
"""
import sys
from glayout.pdk.gf180_mapped import gf180_mapped_pdk as gf180
from glayout.primitives.mimcap import mimcap

for lado in (5.0, 10.0, 20.0):
    for op in ('A', 'B'):
        try:
            c = mimcap(gf180, size=(lado, lado), option=op)
            c.name = 'mim_%s_%g' % (op, lado)
            r = gf180.drc_magic(c, c.name)
            print('  MIM %s  %gx%g um  ->  %s' % (op, lado, lado, r))
        except Exception as e:
            print('  MIM %s  %gx%g um  ->  fallo: %s' % (op, lado, lado, str(e)[:120]))
        sys.stdout.flush()
