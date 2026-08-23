v {xschem version=3.4.8RC file_version=1.3}
G {}
K {}
V {}
S {}
F {}
E {}
T {A current mirror is added to provide the voltage biases 
needed for internal nodes in  the stdp array. 

} 370 530 0 0 0.2 0.2 {}
T {4 presynaptic neurons} -290 -460 0 0 0.4 0.4 {}
T {two post synaptic neurons} 520 -270 0 0 0.4 0.4 {}
T {An input signal for testing purposes 
and its complement signal, to be processed 
by the encoder, providing exitation current 
for the input neurons} -1080 -205 0 0 0.4 0.4 {}
T {The spikes of the first layer and 
the second layer are processed by
a 4x2 matrix with stdp synapses} 50 -210 0 0 0.4 0.4 {}
N -20 40 -20 130 {lab=vpre3}
N -20 40 90 40 {lab=vpre3}
N -10 60 90 60 {lab=nvpre3}
N -10 60 -10 160 {lab=nvpre3}
N 0 80 90 80 {lab=vpre4}
N 0 80 0 350 {lab=vpre4}
N 10 100 90 100 {lab=nvpre4}
N 10 100 10 380 {lab=nvpre4}
N -20 20 90 20 {lab=nvpre2}
N -10 -0 90 -0 {lab=vpre2}
N 0 -20 90 -20 {lab=nvpre1}
N 0 -270 0 -20 {lab=nvpre1}
N -100 -270 0 -270 {lab=nvpre1}
N 10 -40 90 -40 {lab=vpre1}
N 10 -300 10 -40 {lab=vpre1}
N -100 -300 10 -300 {lab=vpre1}
N 810 -190 810 -70 {lab=vpost1}
N 420 -170 420 -20 {lab=vpost1}
N 390 -20 420 -20 {lab=vpost1}
N 390 0 440 0 {lab=nvpost1}
N 440 -160 440 0 {lab=nvpost1}
N 820 -180 820 -40 {lab=nvpost1}
N 390 100 440 100 {lab=nvpost2}
N -10 160 -10 210 {lab=nvpre3}
N -100 210 -10 210 {lab=nvpre3}
N -100 180 -20 180 {lab=vpre3}
N -20 130 -20 180 {lab=vpre3}
N -100 -20 -20 -20 {lab=nvpre2}
N -20 -20 -20 20 {lab=nvpre2}
N -100 -50 -10 -50 {lab=vpre2}
N -10 -50 -10 -0 {lab=vpre2}
N 10 380 10 450 {lab=nvpre4}
N -100 450 10 450 {lab=nvpre4}
N -100 420 -0 420 {lab=vpre4}
N 0 350 0 420 {lab=vpre4}
N 440 -200 440 -160 {lab=nvpost1}
N 440 -200 820 -200 {lab=nvpost1}
N 820 -200 820 -180 {lab=nvpost1}
N 810 -210 810 -190 {lab=vpost1}
N 420 -210 810 -210 {lab=vpost1}
N 420 -210 420 -170 {lab=vpost1}
N 390 80 430 80 {lab=vpost2}
N -880 35 -860 35 {lab=Vin}
N -880 85 -860 85 {lab=Vin_neg}
N 390 120 460 120 {lab=#net1}
N 390 20 470 20 {lab=#net2}
N 450 380 480 380 {lab=avdd}
N 450 400 480 400 {lab=B}
N 450 420 480 420 {lab=A}
N 450 440 480 440 {lab=avss}
N -290 65 -200 65 {lab=vpre1}
N -200 -300 -200 65 {lab=vpre1}
N -200 -300 -100 -300 {lab=vpre1}
N -190 -270 -100 -270 {lab=nvpre1}
N -190 -270 -190 80 {lab=nvpre1}
N -290 85 -190 85 {lab=nvpre1}
N -190 80 -190 85 {lab=nvpre1}
N -180 -50 -100 -50 {lab=vpre2}
N -180 -50 -180 105 {lab=vpre2}
N -290 105 -180 105 {lab=vpre2}
N -170 -20 -100 -20 {lab=nvpre2}
N -170 -20 -170 125 {lab=nvpre2}
N -290 125 -170 125 {lab=nvpre2}
N -170 180 -100 180 {lab=vpre3}
N -170 145 -170 180 {lab=vpre3}
N -290 145 -170 145 {lab=vpre3}
N -180 210 -100 210 {lab=nvpre3}
N -180 165 -180 210 {lab=nvpre3}
N -290 165 -180 165 {lab=nvpre3}
N -290 185 -190 185 {lab=vpre4}
N -190 185 -190 420 {lab=vpre4}
N -190 420 -100 420 {lab=vpre4}
N -200 450 -100 450 {lab=nvpre4}
N -200 210 -200 450 {lab=nvpre4}
N -290 205 -200 205 {lab=nvpre4}
N -200 205 -200 210 {lab=nvpre4}
N -620 15 -590 25 {lab=#net3}
N -620 45 -590 45 {lab=#net4}
N -620 75 -590 65 {lab=#net5}
N -620 105 -590 85 {lab=#net6}
N 460 40 460 120 {lab=#net1}
N 460 40 470 40 {lab=#net1}
N 430 80 450 80 {lab=vpost2}
N 450 80 450 140 {lab=vpost2}
N 450 140 815 140 {lab=vpost2}
N 815 100 815 140 {lab=vpost2}
N 770 100 815 100 {lab=vpost2}
N 770 120 805 120 {lab=nvpost2}
N 805 120 805 145 {lab=nvpost2}
N 440 100 440 145 {lab=nvpost2}
N 440 145 440 155 {lab=nvpost2}
N 440 155 805 155 {lab=nvpost2}
N 805 145 805 155 {lab=nvpost2}
N 810 -70 810 60 {lab=vpost1}
N 770 60 810 60 {lab=vpost1}
N 820 -45 820 80 {lab=nvpost1}
N 770 80 820 80 {lab=nvpost1}
C {stdp/stdp_4x2_lvs.sym} 240 50 0 0 {name=x1}
C {encoder/encoder.sym} -740 55 0 0 {name=x8}
C {lab_pin.sym} -740 -15 0 0 {name=p23 lab=avdd}
C {lab_pin.sym} 90 120 0 0 {name=p1 sig_type=std_logic lab=A}
C {lab_pin.sym} 90 140 0 0 {name=p2 sig_type=std_logic lab=B}
C {lab_pin.sym} 10 -290 0 1 {name=p3 sig_type=std_logic lab=vpre1}
C {lab_pin.sym} 0 -170 0 0 {name=p4 sig_type=std_logic lab=nvpre1}
C {lab_pin.sym} -30 -50 3 1 {name=p5 sig_type=std_logic lab=vpre2}
C {lab_pin.sym} -50 -20 1 1 {name=p8 sig_type=std_logic lab=nvpre2}
C {lab_pin.sym} -40 180 3 1 {name=p9 sig_type=std_logic lab=vpre3}
C {lab_pin.sym} -40 210 1 1 {name=p10 sig_type=std_logic lab=nvpre3}
C {lab_pin.sym} -30 420 3 1 {name=p11 sig_type=std_logic lab=vpre4}
C {lab_pin.sym} -30 450 1 1 {name=p12 sig_type=std_logic lab=nvpre4}
C {lab_pin.sym} -880 35 0 0 {name=p15 sig_type=std_logic lab=Vin}
C {lab_pin.sym} -880 85 0 0 {name=p16 sig_type=std_logic lab=Vin_neg}
C {lab_pin.sym} 810 -150 0 0 {name=p17 sig_type=std_logic lab=vpost1}
C {lab_pin.sym} 820 -140 0 1 {name=p18 sig_type=std_logic lab=nvpost1}
C {lab_pin.sym} 815 100 0 1 {name=p19 sig_type=std_logic lab=vpost2}
C {lab_pin.sym} 805 155 0 1 {name=p20 sig_type=std_logic lab=nvpost2}
C {current_mirror/current_mirror.sym} 300 410 0 0 {name=x9}
C {lab_pin.sym} 480 400 0 1 {name=p21 sig_type=std_logic lab=B}
C {lab_pin.sym} 480 420 0 1 {name=p22 sig_type=std_logic lab=A}
C {lif/layer_input.sym} -440 115 0 0 {name=x10}
C {lif/layer_output.sym} 620 70 0 0 {name=x2}
C {iopin.sym} -530 -370 0 0 {name=p6 lab=avdd}
C {iopin.sym} -535 -340 0 0 {name=p7 lab=avss}
C {lab_pin.sym} -740 135 0 0 {name=p24 lab=avss}
C {lab_pin.sym} -290 45 0 1 {name=p25 lab=avss}
C {lab_pin.sym} -290 25 0 1 {name=p26 lab=avdd}
C {lab_pin.sym} 240 -70 0 1 {name=p27 lab=avdd}
C {lab_pin.sym} 240 170 0 1 {name=p28 lab=avss}
C {lab_pin.sym} 770 20 0 1 {name=p29 lab=avdd}
C {lab_pin.sym} 770 40 0 1 {name=p30 lab=avss}
C {lab_pin.sym} 480 380 0 1 {name=p31 lab=avdd}
C {lab_pin.sym} 480 440 0 1 {name=p32 lab=avss}
C {ipin.sym} -495 -290 0 0 {name=p13 lab=Vin}
C {ipin.sym} -495 -260 0 0 {name=p14 lab=Vin_neg}
C {opin.sym} -515 -230 0 0 {name=p33 lab=vpre1}
C {opin.sym} -515 -190 0 0 {name=p34 lab=vpre2}
C {opin.sym} -515 -90 0 0 {name=p35 lab=vpost1}
C {opin.sym} -515 -60 0 0 {name=p36 lab=vpost2}
C {opin.sym} -515 -160 0 0 {name=p37 lab=vw11}
C {opin.sym} -515 -120 0 0 {name=p38 lab=vw42}
C {lab_pin.sym} 390 40 0 1 {name=p39 lab=vw11}
C {lab_pin.sym} 390 60 0 1 {name=p40 lab=vw42}
