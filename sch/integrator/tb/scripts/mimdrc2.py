"""MIM pelado, con la version de glayout que USAN los notebooks."""
import sys, inspect
from glayout.pdk.gf180_mapped import gf180_mapped_pdk as gf180
from glayout.primitives.mimcap import mimcap
print('glayout usado:', inspect.getfile(mimcap)); sys.stdout.flush()
for lado in (5.0, 10.0):
    try:
        c = mimcap(gf180, size=(lado, lado))
        c.name = 'mimtest_%g' % lado
        r = gf180.drc_magic(c, c.name)
        print('  MIM %gx%g  ->  %s' % (lado, lado, r))
    except Exception as e:
        print('  MIM %gx%g  ->  fallo: %s' % (lado, lado, str(e)[:150]))
    sys.stdout.flush()
