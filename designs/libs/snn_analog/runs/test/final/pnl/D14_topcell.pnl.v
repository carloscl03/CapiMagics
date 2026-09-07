module D14_topcell (Vin,
    Vin_neg,
    avdd,
    avss,
    nvout_1,
    nvout_2,
    nvout_3,
    nvout_4,
    vout_1,
    vout_2,
    vout_3,
    vout_4);
 input Vin;
 input Vin_neg;
 inout avdd;
 inout avss;
 output nvout_1;
 output nvout_2;
 output nvout_3;
 output nvout_4;
 output vout_1;
 output vout_2;
 output vout_3;
 output vout_4;

 wire net3;
 wire net4;
 wire net5;
 wire net6;
 wire vdd;
 wire vss;

 encoder u_encoder (.vss(avss),
    .vdd(avdd),
    .Vin(Vin),
    .Vin_neg(Vin_neg),
    .Iex_1_i(net3),
    .Iex_2_i(net4),
    .Iex_3_i(net5),
    .Iex_4_i(net6));
 layer_input u_layer_input (.Iext1(net3),
    .Iext2(net4),
    .Iext3(net5),
    .Iext4(net6),
    .nvout_1(nvout_1),
    .nvout_2(nvout_2),
    .nvout_3(nvout_3),
    .nvout_4(nvout_4),
    .vdd(avdd),
    .vout_1(vout_1),
    .vout_2(vout_2),
    .vout_3(vout_3),
    .vout_4(vout_4),
    .vss(avss));
endmodule
