"""Barrido del integrador sobre la banda que impone la cadena.

BANDA: 74 - 4500 kHz, deducida de EncoderSpec -> NeuronSpec.
  suelo <- Iex 15 nA, el pedido mas bajo que el encoder resuelve
  techo <- F_MAX del LIF (el reset no completa por debajo de 215 ns).
          NO es un borde de barrido: es un limite medido del circuito.

Cada punto trae `vm`, rizado, corriente de fuga (por AMPERIMETRO) y dos
controles de validez: deriva entre dos ventanas consecutivas, y balance de
carga entre lo que entra por M6 y lo que sale por M2.

Los casos que no asientan a la primera se REINTENTAN con 4x asentamiento, en
vez de descartarlos: son los que la ley de composicion predice peor, o sea los
que mas informacion nueva traen.
"""
import itertools, sys, time
import numpy as np
import banco

L2S  = [0.28, 0.50, 1.00, 2.00]
IREF = [12e-9, 25e-9, 50e-9, 100e-9]
W6S  = [0.25, 0.50, 1.00]
L6S  = [0.28, 0.50, 1.00, 2.00]
CS   = [2000.0, 5111.0, 12000.0]
FS   = [74, 150, 300, 600, 1200, 2400, 4500]

rng = np.random.default_rng(11)
todas = list(itertools.product(L2S, IREF, W6S, L6S, CS))
rng.shuffle(todas)
GEOS = [(1.0, 0.28, 1.0, l2, ir, w6, l6, c) for l2, ir, w6, l6, c in todas[:60]]

print('=== barrido: %d geometrias x %d frecuencias = %d puntos ==='
      % (len(GEOS), len(FS), len(GEOS) * len(FS)))
print('   banda %d - %d kHz' % (FS[0], FS[-1]))
sys.stdout.flush()

RES = []
t00 = time.time()
for f in FS:
    t0 = time.time()
    lote = [(g, f) for g in GEOS]
    out = []
    for k in range(0, len(lote), 20):                 # 20 por netlist
        out += banco.mide(lote[k:k + 20], tag='b%d_%d' % (f, k))
    # reintento de los que no asentaron
    mal = [i for i, r in enumerate(out)
           if not np.isfinite(r['vm']) or abs(r['deriva']) > 2.0 or abs(r['bal']) > 5.0]
    if mal:
        re = []
        for k in range(0, len(mal), 20):
            sub = [(GEOS[i], f) for i in mal[k:k + 20]]
            re += banco.mide(sub, nset=24, nmed=8, tag='r%d_%d' % (f, k))
        for i, r in zip(mal, re):
            out[i] = r
    ok = sum(1 for r in out
             if np.isfinite(r['vm']) and abs(r['deriva']) <= 2.0 and abs(r['bal']) <= 5.0)
    for g, r in zip(GEOS, out):
        RES.append(dict(g=g, f=f, **r))
    print('   %5d kHz  %3d/%d validos  (%d reintentos)  %5.0f s'
          % (f, ok, len(GEOS), len(mal), time.time() - t0))
    sys.stdout.flush()
    np.save('barrido_banda.npy', np.array(RES, dtype=object))

print()
print('   total %.0f min' % ((time.time() - t00) / 60))
np.save('barrido_banda.npy', np.array(RES, dtype=object))
print('   guardado en barrido_banda.npy: %d puntos' % len(RES))
