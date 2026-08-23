module layer_input (
    avdd,
    avss,
    Iext1,
    vout_1,
    nvout_1,
    Iext2,
    vout_2,
    nvout_2,
    Iext3,
    vout_3,
    nvout_3,
    vout_4,
    Iext4,
    nvout_4
);
 
    inout  avdd;   
    inout  avss;   
    input  Iext1;  
    output vout_1; 
    output nvout_1;
    input  Iext2;  
    output vout_2; 
    output nvout_2;
    input  Iext3;  
    output vout_3; 
    output nvout_3;
    output vout_4; 
    input  Iext4;  
    output nvout_4;

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

    neurona_lvs x3 (
        .Vdd       (avdd),
        .Vss       (avss),
        .Iin       (Iext3),
        .spike     (vout_3),
        .spike_neg (nvout_3)
    );

    neurona_lvs x4 (
        .Vdd       (avdd),
        .Vss       (avss),
        .Iin       (Iext4),
        .spike     (vout_4),
        .spike_neg (nvout_4)
    );

endmodule
