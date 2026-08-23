module layer_output (
    avdd,
    avss,
    Iext1, vout_1, nvout_1,
    Iext2, vout_2, nvout_2
);

    inout  avdd;      // alimentacion
    inout  avss;      // tierra

    input  Iext1;     // corriente de entrada neurona 1
    output vout_1;    // salida de disparo neurona 1
    output nvout_1;   // salida de disparo negada neurona 1

    input  Iext2;     // corriente de entrada neurona 2
    output vout_2;    // salida de disparo neurona 2
    output nvout_2;   // salida de disparo negada neurona 2

    // --- Instancias de la macro 
    neurona_lvs x1 (
        .Vdd       (avdd),
        .Vss       (avss),
        .Iin       (Iext1),
        .spike     (vout_1),
        .spike_neg (nvout_1)
    );

    neurona_lvs x2 (
        .Vdd       (avdd),
        .Vss       (avss),
        .Iin       (Iext2),
        .spike     (vout_2),
        .spike_neg (nvout_2)
    );

endmodule
