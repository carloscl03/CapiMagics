module layer_input (Iext1,
    Iext2,
    Iext3,
    Iext4,
    nvout_1,
    nvout_2,
    nvout_3,
    nvout_4,
    vdd,
    vout_1,
    vout_2,
    vout_3,
    vout_4,
    vss);
 input Iext1;
 input Iext2;
 input Iext3;
 input Iext4;
 output nvout_1;
 output nvout_2;
 output nvout_3;
 output nvout_4;
 inout vdd;
 output vout_1;
 output vout_2;
 output vout_3;
 output vout_4;
 inout vss;


 neurona_lvs x1 (.vss(vss),
    .vdd(vdd),
    .Iin(Iext1),
    .spike_neg(nvout_1),
    .spike(vout_1));
 neurona_lvs x2 (.vss(vss),
    .vdd(vdd),
    .Iin(Iext2),
    .spike_neg(nvout_2),
    .spike(vout_2));
 neurona_lvs x3 (.vss(vss),
    .vdd(vdd),
    .Iin(Iext3),
    .spike_neg(nvout_3),
    .spike(vout_3));
 neurona_lvs x4 (.vss(vss),
    .vdd(vdd),
    .Iin(Iext4),
    .spike_neg(nvout_4),
    .spike(vout_4));
endmodule
