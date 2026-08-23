v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
N 10 -30 10 30 {lab=#net1}
N -30 -60 -30 0 {lab=#net1}
N -30 0 10 0 {lab=#net1}
N 10 -60 90 -60 {lab=avdd}
N 10 90 10 150 {lab=ifwd}
N -30 60 -30 120 {lab=ifwd}
N -30 120 10 120 {lab=ifwd}
N 10 60 90 60 {lab=avdd}
N 10 -130 10 -90 {lab=i_SUM}
C {symbols/pfet_03v3.sym} -10 -60 0 0 {name=M4
L=5u
W=0.5u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X
}
C {symbols/pfet_03v3.sym} -10 60 0 0 {name=M6
L=5u
W=0.5u
nf=1
m=1
ad="'int((nf+1)/2) * W/nf * 0.18u'"
pd="'2*int((nf+1)/2) * (W/nf + 0.18u)'"
as="'int((nf+2)/2) * W/nf * 0.18u'"
ps="'2*int((nf+2)/2) * (W/nf + 0.18u)'"
nrd="'0.18u / W'" nrs="'0.18u / W'"
sa=0 sb=0 sd=0
model=pfet_03v3
spiceprefix=X
}
C {lab_pin.sym} 90 60 0 1 {name=p117 sig_type=std_logic lab=avdd}
C {iopin.sym} 90 -60 0 0 {name=p1 lab=avdd}
C {iopin.sym} 10 150 0 0 {name=p2 lab=ifwd}
C {iopin.sym} 10 -130 0 0 {name=p3 lab=i_SUM}
