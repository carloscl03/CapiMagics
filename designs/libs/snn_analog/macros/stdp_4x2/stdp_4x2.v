module stdp_4x2 (
    inout  avdd,
    inout  avss,
    inout  A,
    inout  B,
        
    input  nvpre1,
    input  vpre1,
    input  vpre2,
    input  nvpre2,
    input  vpre3,
    input  nvpre3,
    input  vpre4,
    input  nvpre4,
    
    input  vpost1,
    input  nvpost1,
    input  vpost2,
    input  nvpost2,

    output ifwd1,
    output ifwd2,
    inout  vw11,
    inout  vw42
);

    wire net7, net8;

    // ---- Bloques de limitacion de corriente ----
    Current_limit x9 (
        .i_SUM (net7),
        .avdd  (avdd),
        .ifwd  (ifwd1)
    );

    Current_limit x10 (
        .i_SUM (net8),
        .avdd  (avdd),
        .ifwd  (ifwd2)
    );

    // ---- Arreglo de sinapsis STDP 4x2 ----
    stdp x1 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre1),
        .nvpost  (nvpost1),
        .vpre    (vpre1),
        .vpost   (vpost1),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (vw11),
        .Iout    (net7)
    );

    stdp x2 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre2),
        .nvpost  (nvpost1),
        .vpre    (vpre2),
        .vpost   (vpost1),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net7)
    );

    stdp x3 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre3),
        .nvpost  (nvpost1),
        .vpre    (vpre3),
        .vpost   (vpost1),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net7)
    );

    stdp x4 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre4),
        .nvpost  (nvpost1),
        .vpre    (vpre4),
        .vpost   (vpost1),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net7)
    );

    stdp x5 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre1),
        .nvpost  (nvpost2),
        .vpre    (vpre1),
        .vpost   (vpost2),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net8)
    );

    stdp x6 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre2),
        .nvpost  (nvpost2),
        .vpre    (vpre2),
        .vpost   (vpost2),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net8)
    );

    stdp x7 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre3),
        .nvpost  (nvpost2),
        .vpre    (vpre3),
        .vpost   (vpost2),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (),
        .Iout    (net8)
    );

    stdp x8 (
        .avdd    (avdd),
        .avss    (avss),
        .nvpre   (nvpre4),
        .nvpost  (nvpost2),
        .vpre    (vpre4),
        .vpost   (vpost2),
        .vb_itd  (A),
        .vb_idep (B),
        .vb_itp  (B),
        .vb_pot  (A),
        .vw      (vw42),
        .Iout    (net8)
    );

endmodule
