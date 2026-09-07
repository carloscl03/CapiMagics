#!/usr/bin/env python3
import re
import sys

def parse_verilog_header(v_file, target_module):
    pins = {'input': [], 'output': [], 'inout': []}
    buses = {'input': [], 'output': [], 'inout': []}
    
    with open(v_file, 'r') as f:
        content = f.read()

    # Limpiar comentarios
    content = re.sub(r'//.*', '', content)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)

    # Buscar definición del módulo
    pattern = rf"module\s+{re.escape(target_module)}\s*\((.*?)\)\s*;(.*?)endmodule"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        raise ValueError(f"Módulo '{target_module}' no encontrado en {v_file}")

    header_args = match.group(1)
    body_args = match.group(2)
    full_text = header_args + "\n" + body_args

    for direction in ['input', 'output', 'inout']:
        # Detectar buses
        bus_matches = re.findall(rf'\b{direction}\s+\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*(\w+)', full_text)
        for hi, lo, name in bus_matches:
            buses[direction].append((name, int(hi), int(lo)))

        # Detectar escalares
        scalar_matches = re.findall(rf'\b{direction}\s+(?!\[)\s*(\w+)', full_text)
        for name in scalar_matches:
            if not any(name == b[0] for b in buses[direction]):
                pins[direction].append(name)

    return pins, buses

def generate_lib(module_name, pins, buses, output_file, tran=2.5, cap=0.001):
    with open(output_file, 'w') as f:
        f.write(f"library({module_name}) {{\n")
        f.write('  time_unit : "1ns";\n')
        f.write('  voltage_unit : "1V";\n')
        f.write('  current_unit : "1uA";\n')
        f.write('  pulling_resistance_unit : "1kohm";\n')
        f.write('  leakage_power_unit : "1nW";\n')
        f.write("  capacitive_load_unit(1,pf);\n\n")

        # Umbrales obligatorios para OpenROAD / STA
        f.write("  slew_derate_from_library : 1.0;\n")
        f.write("  slew_lower_threshold_pct_fall : 20.0;\n")
        f.write("  slew_upper_threshold_pct_fall : 80.0;\n")
        f.write("  slew_lower_threshold_pct_rise : 20.0;\n")
        f.write("  slew_upper_threshold_pct_rise : 80.0;\n")
        f.write("  input_threshold_pct_fall : 50.0;\n")
        f.write("  input_threshold_pct_rise : 50.0;\n")
        f.write("  output_threshold_pct_fall : 50.0;\n")
        f.write("  output_threshold_pct_rise : 50.0;\n\n")

        # Declarar tipos de bus
        created_types = set()
        for direction in buses:
            for name, hi, lo in buses[direction]:
                type_name = f"bus_{hi}_{lo}"
                if type_name not in created_types:
                    width = abs(hi - lo) + 1
                    f.write(f"  type ({type_name}) {{\n")
                    f.write("    base_type : array ;\n")
                    f.write("    data_type : bit ;\n")
                    f.write(f"    bit_width : {width} ;\n")
                    f.write(f"    bit_from : {hi} ;\n")
                    f.write(f"    bit_to : {lo} ;\n")
                    f.write("    downto : true ;\n")
                    f.write("  }\n\n")
                    created_types.add(type_name)

        f.write(f"  cell({module_name}) {{\n")

        # Escribir puertos escalares
        for direction, pin_list in pins.items():
            for pin in pin_list:
                f.write(f"    pin({pin}) {{\n")
                if pin.lower() in ['vdd', 'vss', 'vdda', 'vssa']:
                    f.write(f"      direction : inout ;\n")
                    f.write(f"      pg_type : {'primary_power' if 'vdd' in pin.lower() else 'primary_ground'} ;\n")
                else:
                    f.write(f"      direction : {direction} ;\n")
                    if direction == "input":
                        f.write(f"      max_transition : {tran};\n")
                    f.write(f"      capacitance : {cap}; \n")
                f.write("    }\n")

        # Escribir buses
        for direction, bus_list in buses.items():
            for name, hi, lo in bus_list:
                type_name = f"bus_{hi}_{lo}"
                f.write(f"    bus({name}) {{\n")
                f.write(f"      bus_type : {type_name} ;\n")
                f.write(f"      direction : {direction} ;\n")
                if direction == "input":
                    f.write(f"      max_transition : {tran};\n")
                for bit in range(min(lo, hi), max(lo, hi) + 1):
                    f.write(f"      pin({name}[{bit}]) {{\n")
                    f.write(f"        capacitance : {cap};\n")
                    f.write("      }\n")
                f.write("    }\n")

        f.write("  }\n")
        f.write("}\n")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 gen_lib.py <netlist.v> <nombre_modulo> [tran] [cap]")
        sys.exit(1)

    v_file = sys.argv[1]
    mod_name = sys.argv[2]
    tran = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5
    cap = float(sys.argv[4]) if len(sys.argv) > 4 else 0.001

    pins, buses = parse_verilog_header(v_file, mod_name)
    generate_lib(mod_name, pins, buses, f"{mod_name}.lib", tran, cap)
    print(f"Generado {mod_name}.lib con umbrales STA exitosamente.")
