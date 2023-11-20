import json
import re

class LUT:
    def __init__(self, id, num_inputs, function=None, max_variables=None):
        self.id = id
        self.num_inputs = num_inputs
        self.function = function
        self.input_connections = set()  # LUTs that provide input to this LUT
        self.output_connections = set()  # LUTs that receive output from this LUT
        self.variables = set()
        self.max_variables = max_variables

    def assign_function(self, function):
        self.function = function
        self.extract_variables(function)

    def extract_variables(self, function):
        # Filter variables based on the maximum number of input ports
        if self.max_variables:
            valid_variables = set(self.max_variables)
            self.variables = set(filter(lambda x: x in valid_variables, function))
        else:
            self.variables = set(filter(str.isalpha, function))

    def add_input_connection(self, lut_id):
        self.input_connections.add(lut_id)

    def add_output_connection(self, lut_id):
        self.output_connections.add(lut_id)

    def display(self):
        input_connections_info = f"Input from: LUT(s) {', '.join(map(str, self.input_connections))}" if self.input_connections else ""
        output_connections_info = f"Output to: LUT(s) {', '.join(map(str, self.output_connections))}" if self.output_connections else ""
        connections_info = (input_connections_info + " | " + output_connections_info).strip(' | ')
        return f"LUT {self.id} ({self.num_inputs}-input): Function: {self.function if self.function else 'Not assigned'} | {connections_info}"

class FPGA:
    def __init__(self, num_luts, lut_type, num_inputs, num_outputs):
        self.luts = [LUT(id, lut_type) for id in range(num_luts)]
        self.num_inputs = num_inputs
        self.system_inputs = [None] * num_inputs
        self.num_outputs = num_outputs
        self.system_outputs = [None] * num_outputs
        self.input_variable_map = {}
        self.final_or_lut_ids = []  # Track LUTs with final OR operations
        # Define variable names based on the number of inputs (e.g., 'A', 'B', 'C', ...)
        variable_names = [chr(i) for i in range(65, 65 + num_inputs)]  # ASCII 65 is 'A'
        self.luts = [LUT(id, lut_type, max_variables=variable_names) for id in range(num_luts)]

    def split_and_assign_functions(self, sop_expressions):
        lut_id = 0
        lut_output_map = {}  # Map to keep track of LUT outputs (e.g., F1 -> Output of LUT 0)

        for idx, expression in enumerate(sop_expressions):
            # Replace formula references (e.g., F1, F2) with actual LUT outputs
            for formula_ref, lut_output in lut_output_map.items():
                expression = expression.replace(formula_ref, lut_output)

            # Split expression into terms and assign to LUTs
            terms = expression.split('|')
            term_outputs = []

            for term in terms:
                # Check if the term is complex and needs its own LUT
                if '&' in term or '|' in term:
                    if lut_id >= len(self.luts):
                        raise Exception("Not enough LUTs available.")
                    self.luts[lut_id].assign_function(term.strip())
                    term_outputs.append(f"Output of LUT {lut_id}")
                    lut_id += 1
                else:
                    # Directly use the term (which could be an output from a previous LUT)
                    term_outputs.append(term.strip())

            # Combine term outputs with an OR operation in a new LUT, if there are multiple terms
            if len(term_outputs) > 1:
                if lut_id >= len(self.luts):
                    raise Exception("Not enough LUTs available.")
                combined_expression = ' | '.join(term_outputs)
                self.luts[lut_id].assign_function(combined_expression)
                lut_output_map[f'F{idx+1}'] = f"Output of LUT {lut_id}"
                lut_id += 1
            elif term_outputs:
                # If there's only one term output, use it as the output for this SOP expression
                lut_output_map[f'F{idx+1}'] = term_outputs[0]

    def assign_term_to_lut(self, term, lut_id):
        if lut_id < len(self.luts):
            self.luts[lut_id].assign_function(term)
            return f"Output of LUT {lut_id}"
        return term

    def split_and_combine_complex_term(self, variables, start_lut_id):
        split_outputs = []
        lut_used = 0
        i = 0
        while i < len(variables):
            num_vars_for_lut = min(len(variables) - i, self.luts[start_lut_id].num_inputs)
            sub_term = ' & '.join(variables[i:i + num_vars_for_lut])
            if start_lut_id + lut_used < len(self.luts):
                self.luts[start_lut_id + lut_used].assign_function(sub_term)
                split_outputs.append(f"Output of LUT {start_lut_id + lut_used}")
                lut_used += 1
            else:
                print("Not enough LUTs to implement the logic")
                break
            i += num_vars_for_lut
        return split_outputs, lut_used

    def extract_referenced_luts(self, function):
        referenced_luts = []
        if function:
            parts = function.split('|')
            for part in parts:
                part = part.strip()
                if "Output of LUT" in part:
                    matches = re.findall(r'Output of LUT (\d+)', part)
                    for match in matches:
                        try:
                            lut_id = int(match)
                            referenced_luts.append(lut_id)
                        except ValueError:
                            print(f"Warning: Unable to extract LUT ID from '{match}'.")
        return referenced_luts

    def update_lut_connections(self):
        # Reset existing connections
        for lut in self.luts:
            lut.input_connections.clear()
            lut.output_connections.clear()

        # Update connections based on current functions
        for lut in self.luts:
            if lut.function:
                referenced_luts = self.extract_referenced_luts(lut.function)
                for ref_lut_id in referenced_luts:
                    lut.add_input_connection(ref_lut_id)
                    if ref_lut_id < len(self.luts):
                        self.luts[ref_lut_id].add_output_connection(lut.id)
    
    def assign_or_luts_to_outputs(self):
        for i, lut_id in enumerate(self.final_or_lut_ids):
            if i < self.num_outputs:
                self.system_outputs[i] = self.luts[lut_id]
            else:
                print(f"Not enough output ports for LUT {lut_id}")

    def display_all_lut_assignments(self):
        self.update_lut_connections()
        for lut in self.luts:
            print(lut.display())
        self.display_output_assignments()

    def display_output_assignments(self):
        print("Output Port Assignments:")
        for i, lut in enumerate(self.system_outputs):
            if lut is not None:
                print(f"Output port {i} is assigned to LUT {lut.id}")
            else:
                print(f"Output port {i} is unassigned")

    def calculate_resource_allocation(self):
        # Calculate the percentage of LUTs used
        luts_used = sum(1 for lut in self.luts if lut.function is not None)
        percent_luts_used = (luts_used / len(self.luts)) * 100

        # Calculate the percentage of connections used
        total_possible_connections = len(self.luts) * (len(self.luts) - 1)
        connections_used = sum(len(lut.input_connections) + len(lut.output_connections) for lut in self.luts)
        percent_connections_used = (connections_used / total_possible_connections) * 100 if total_possible_connections else 0

        # Estimate total memory required (example calculation)
        memory_per_lut = 64  # Assuming each LUT requires 64 bytes (for example)
        memory_per_connection = 8  # Assuming each connection requires 8 bytes (for example)
        total_memory = (luts_used * memory_per_lut) + (connections_used * memory_per_connection)

        return percent_luts_used, percent_connections_used, total_memory

    def display_resource_allocation_summary(self):
        percent_luts_used, percent_connections_used, total_memory = self.calculate_resource_allocation()
        print(f"Resource Allocation Summary:")
        print(f"  % of LUTs Used: {percent_luts_used:.2f}%")
        print(f"  % of Connections Used: {percent_connections_used:.2f}%")
        print(f"  Total Memory Required: {total_memory} bytes")

    def map_variables_to_luts(self):
        var_to_lut_map = {}
        for lut in self.luts:
            for var in lut.variables:
                if var not in var_to_lut_map:
                    var_to_lut_map[var] = []
                var_to_lut_map[var].append(lut.id)
        return var_to_lut_map

    def display_input_assignments(self):
        var_to_lut_map = self.map_variables_to_luts()
        print("Input Port Assignments:")
        for var, lut_ids in var_to_lut_map.items():
            luts_str = ', '.join(map(str, lut_ids))
            print(f"Variable '{var}' is assigned to LUT {luts_str}")
    def generate_lut_configurations(self):
        self.update_lut_connections()
        lut_configs = []
        for lut in self.luts:
            input_conn = ','.join(map(str, sorted(lut.input_connections)))
            output_conn = ','.join(map(str, sorted(lut.output_connections)))
            lut_config = f"LUT{lut.id};Inputs:{input_conn};Function:{lut.function};Outputs:{output_conn}"
            lut_configs.append(lut_config)
        return ';'.join(lut_configs)
    def generate_io_assignments(self):
        input_assignments = ';'.join([f"Input{idx}->{var}" for idx, var in enumerate(self.input_variable_map)])
        output_assignments = ';'.join([f"Output{idx}->LUT{lut.id}" for idx, lut in enumerate(self.system_outputs) if lut is not None])
        return f"{input_assignments};{output_assignments}"
    def generate_bitstream(self):
        lut_configurations = self.generate_lut_configurations()
        io_assignments = self.generate_io_assignments()
        return f"{lut_configurations};{io_assignments}"

def read_connections_from_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


from boolean_EQN import get_minimized_expressions_from_file
from boolean_EQN import get_variables_from_file


# Example usage
if __name__ == "__main__":
    num_luts = int(input("Enter the number of LUTs: "))
    lut_type = int(input("Enter the number of inputs for LUTs (4 or 6): "))
    num_system_inputs = int(input("Enter the number of system inputs: "))
    num_system_outputs = int(input("Enter the number of system outputs: "))

    fpga = FPGA(num_luts, lut_type, num_system_inputs, num_system_outputs)

    minimized_expressions = get_minimized_expressions_from_file("input.eqn")
    fpga.split_and_assign_functions(minimized_expressions)

    variables = get_variables_from_file("input.eqn")

    fpga.assign_or_luts_to_outputs()  # Assign final OR LUTs to output ports

    fpga.display_all_lut_assignments()
    
    fpga.display_input_assignments()

    fpga.display_resource_allocation_summary()
    bitstream = fpga.generate_bitstream()
    print("Generated Bitstream:")
    print(bitstream)