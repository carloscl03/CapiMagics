module stdp_lvs (
    input  avdd,     // alimentacion
    input  avss,     // tierra
    input  nvpre,    // pre-sinaptico negado
    input  nvpost,   // post-sinaptico negado
    input  vpre,     // pre-sinaptico
    input  vpost,    // post-sinaptico
    input  vb_itd,   // polarizacion (bias) itd
    input  vb_idep,  // polarizacion (bias) idep
    input  vb_itp,   // polarizacion (bias) itp
    input  vb_pot,   // polarizacion (bias) potenciacion
    input  vw,       // peso sinaptico (nodo de almacenamiento)
    output iout      // corriente de salida
);

endmodule
