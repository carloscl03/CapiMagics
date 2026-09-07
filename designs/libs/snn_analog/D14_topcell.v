// celda con encoder y layer_input
module D14_topcell (
    // Entradas del encoder
    input Vin,
    input Vin_neg,
   

    // Salidas del layer_input
    output vout_1,
    output nvout_1,
    output vout_2,
    output nvout_2,
    output vout_3,
    output nvout_3,
    output vout_4,
    output nvout_4,
    inout avdd,
    inout avss
);

    // Nets internos entre encoder y layer_input
    wire net3;
    wire net4;
    wire net5;
    wire net6;

    // Instancia del encoder
    encoder u_encoder (
        .vdd(avdd),
        .vss(avss),
        .Vin(Vin),
        .Vin_neg(Vin_neg),
        .Iex_1_i(net3),
        .Iex_2_i(net4),
        .Iex_3_i(net5),
        .Iex_4_i(net6)
    );

    // Instancia del layer_input
    layer_input u_layer_input (
        .vdd(avdd),
        .vss(avss),
        .Iext1(net3),
        .vout_1(vout_1),
        .nvout_1(nvout_1),
        .Iext2(net4),
        .vout_2(vout_2),
        .nvout_2(nvout_2),
        .Iext3(net5),
        .vout_3(vout_3),
        .nvout_3(nvout_3),
        .vout_4(vout_4),
        .Iext4(net6),
        .nvout_4(nvout_4)

    );

endmodule
