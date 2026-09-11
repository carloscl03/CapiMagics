"""Ejemplos de uso del motor de la sinapsis STDP."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stdp_design import StdpSpec, design

print("=" * 62)
print("1. Lo minimo: una ventana, y que compruebe el acoplo con la neurona")
print("=" * 62)
d = design(StdpSpec(tau_us=5.5, f_min_kHz=12.8, f_max_kHz=4500))
print(d.report())

print("\n" + "=" * 62)
print("2. La ventana que SI cubre a la neurona entera")
print("=" * 62)
d = design(StdpSpec(tau_us=33.9, f_min_kHz=12.8, f_max_kHz=4500))
for k in ("tau- [us]", "f cubierta al 10 % [kHz]", "A- por evento [mV]"):
    print("  %-28s %s" % (k, d.predicted[k]))
print("  itd_nA = %.3f  <- por debajo del falso suelo de 0.4 nA que se reporto"
      % d.params["itd_nA"])

print("\n" + "=" * 62)
print("3. Pedir asimetria: el motor dice cuando NO se puede")
print("=" * 62)
for a in (0.7, 1.0, 1.4):
    d = design(StdpSpec(tau_us=5.5, asimetria=a))
    if d.ok:
        print("  A+/A- = %.1f  ->  W_trrd_dep = %.3f, A- = %s mV"
              % (a, d.params["W_trrd_dep"], d.predicted["A- por evento [mV]"]))
    else:
        print("  A+/A- = %.1f  ->  %s" % (a, d.errors[0].message))

print("\n" + "=" * 62)
print("4. Lo que hay que pasarle a los bloques vecinos")
print("=" * 62)
d = design(StdpSpec(tau_us=5.5, n_sinapsis_pre=2, n_sinapsis_post=4))
for k, v in d.requirements.items():
    print("  %s:\n      %s" % (k, v))
