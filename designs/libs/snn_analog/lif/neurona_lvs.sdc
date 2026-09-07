# Reloj virtual de 2 MHz
create_clock -name virtual_clk -period 500

# Entradas de datos
set_input_delay 0 \
    -clock virtual_clk \
    [get_ports {Iext1 Iext2 Iext3 Iext4}]

# Salidas de datos
set_output_delay 0 \
    -clock virtual_clk \
    [get_ports {vout_1 nvout_1 vout_2 nvout_2 vout_3 nvout_3 vout_4 nvout_4}]
