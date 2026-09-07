module layer_output (Iext1,
    Iext2,
    nvout_1,
    nvout_2,
    vdd,
    vout_1,
    vout_2,
    vss,
    VSS,
    VDD);
 input Iext1;
 input Iext2;
 output nvout_1;
 output nvout_2;
 inout vdd;
 output vout_1;
 output vout_2;
 inout vss;
 inout VSS;
 inout VDD;


 neurona_lvs x1 (.vss(vss),
    .vdd(vdd),
    .spike(vout_1),
    .spike_neg(nvout_1),
    .Iin(Iext1));
 neurona_lvs x2 (.vss(vss),
    .vdd(vdd),
    .spike(vout_2),
    .spike_neg(nvout_2),
    .Iin(Iext2));
endmodule
