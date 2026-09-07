###############################################################################
# Created by write_sdc
###############################################################################
current_design stdp_4x2
###############################################################################
# Timing Constraints
###############################################################################
create_clock -name __VIRTUAL_CLK__ -period 10.0000 
set_clock_uncertainty 0.2500 __VIRTUAL_CLK__
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {A}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {B}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpost1}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpost2}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpre1}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpre2}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpre3}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {nvpre4}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpost1}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpost2}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpre1}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpre2}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpre3}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vpre4}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vw11}]
set_input_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vw42}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {A}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {B}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {ifwd1}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {ifwd2}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vw11}]
set_output_delay 2.0000 -clock [get_clocks {__VIRTUAL_CLK__}] -add_delay [get_ports {vw42}]
###############################################################################
# Environment
###############################################################################
set_load -pin_load 0.0729 [get_ports {A}]
set_load -pin_load 0.0729 [get_ports {B}]
set_load -pin_load 0.0729 [get_ports {ifwd1}]
set_load -pin_load 0.0729 [get_ports {ifwd2}]
set_load -pin_load 0.0729 [get_ports {vw11}]
set_load -pin_load 0.0729 [get_ports {vw42}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {A}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {B}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpost1}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpost2}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpre1}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpre2}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpre3}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {nvpre4}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpost1}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpost2}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpre1}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpre2}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpre3}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vpre4}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vw11}]
set_driving_cell -lib_cell gf180mcu_fd_sc_mcu7t5v0__inv_1 -pin {ZN} -input_transition_rise 0.0000 -input_transition_fall 0.0000 [get_ports {vw42}]
###############################################################################
# Design Rules
###############################################################################
set_max_transition 3.0000 [current_design]
set_max_capacitance 0.2000 [current_design]
set_max_fanout 10.0000 [current_design]
