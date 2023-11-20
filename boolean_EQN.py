import sympy
import numpy as np
import math
import queue


class Node:

    def __init__(self, term, level) -> None:
        self.level = level 
        self.term = term 
        self.covered = False

    def one_num(self):
        return self.term.count('1')

    def compare(self, node1):
        res = []
        for i in range(len(self.term)):
            if self.term[i] == node1.term[i]:
                continue
            elif self.term[i] == '-' or node1.term[i] == "-":
                return (False, None)
            else:
                res.append(i)
        if len(res) == 1:
            return (True, res[0])
        return (False, None)

    def term2logic(self):
        logic_term = ''
        count=0
        for i in range(len(self.term)):
            if self.term[i] == "-":
                count+=1
            elif self.term[i] == "1":
                if count == 0:
                    logic_term += 'A'
                elif count==1:
                    logic_term += 'B'
                elif count==2:
                    logic_term += 'C'
                elif count==3:
                    logic_term += 'D'
                elif count==4:
                    logic_term += 'E'
                count+=1    
            else:
                if count == 0:
                    logic_term += "A'"
                elif count==1:
                    logic_term += "B'"
                elif count==2:
                    logic_term += "C'"
                elif count==3:
                    logic_term += "D'"
                elif count==4:
                    logic_term += "E'"
                count+=1    
        if len(logic_term) == 0:
            logic_term = '1'
        return logic_term


class QM:

    def __init__(self, num, lst) -> None:
        self.max_bits = num
        self.minterm_list = sorted(lst) 
        if len(self.minterm_list) == 0:
            print(0)
            exit()
        if self.minterm_list[-1] >= 2**self.max_bits:
            raise ValueError('input wrong！')
        self.node_list = []
        self.PI = []

    def num2str(self, num):
        str = format(num, "b").zfill(self.max_bits)
        return str

    def _comp_binary_same(self, term, number):
        for i in range(len(term)):
            if term[i] != '-':
                if term[i] != number[i]:
                    return False
        return True

    def _initial(self):
        flag = True 
        groups = [[] for i in range(self.max_bits + 1)]
        for minterm in self.minterm_list:
            tmp_node = Node(term=self.num2str(minterm), level=0)
            groups[tmp_node.one_num()].append(tmp_node)
            flag = True
        self.node_list.append(groups)
        return flag

    def merge(self, level):
        flag = False                                        
        if level == 0:
            flag = self._initial()
        else:
            groups = self.node_list[level - 1]
            new_groups = [[] for i in range(self.max_bits + 1)]
            term_set = set()                                
            for i in range(len(groups) - 1):
                for node0 in groups[i]:
                    for node1 in groups[i + 1]:
                        cmp_res = node0.compare(node1)
                        if cmp_res[0]:
                            node0.covered = True
                            node1.covered = True
                            new_term = '{}-{}'.format(
                                node0.term[:cmp_res[1]],
                                node0.term[cmp_res[1] + 1:]
                            )
                            tmp_node = Node(term=new_term, level=level)
                            if tmp_node.term not in term_set:
                                new_groups[tmp_node.one_num()].append(tmp_node)
                                term_set.add(tmp_node.term)
                                flag = True
            self.node_list.append(new_groups)
        if flag:
            self.merge(level + 1)

    def backtracking(self):
        for groups in self.node_list:
            for group in groups:
                for node in group:
                    if not node.covered:
                        self.PI.append(node)
        return self.PI

    def find_essential_prime(self, Chart):
        pos = np.argwhere(Chart.sum(axis=0) == 1)
        essential_prime = []
        for i in range(len(self.PI)):
            for j in range(len(pos)):
                if Chart[i][pos[j][0]] == 1:
                    essential_prime.append(i)
        essential_prime = list(set(essential_prime)) 
        return essential_prime

    def cover_left(self, Chart):
        list_result = []
        max_len = len(Chart)                          
        myQueue = queue.Queue(math.factorial(max_len)) 
        for i in range(max_len):
            myQueue.put([i])

        stop_flag = False                        
        while not myQueue.empty():
            minterm_mark = np.zeros(len(Chart[0])) 
            choice = myQueue.get()
            if stop_flag and len(list_result[-1]) < len(choice):
                break

            for row in choice:
                minterm_mark += Chart[row]

            if all(minterm_mark): 
                list_result.append(choice)
                stop_flag = True  

            for row in range(choice[-1] + 1, max_len):
                myQueue.put(choice + [row]) 
        return list_result

    def find_minimum_cost(self, Chart):
        QM_final = []
        essential_prime = self.find_essential_prime(Chart)
        for i in range(len(essential_prime)):
            for j in range(len(Chart[0])):
                if Chart[essential_prime[i]][j] == 1:
                    for row in range(len(Chart)):
                        Chart[row][j] = 0

        if not np.sum(Chart):
            QM_final = [essential_prime]
        else:
            pos_col_left = np.argwhere(Chart.sum(axis=0) > 0) 
            pos_row_left = np.argwhere(Chart.sum(axis=1) > 0) 

            new_Chart = np.zeros([len(pos_row_left), len(pos_col_left)])
            for i in range(len(pos_row_left)):
                for j in range(len(pos_col_left)):
                    if Chart[pos_row_left[i][0]][pos_col_left[j][0]] == 1:
                        new_Chart[i][j] = 1

            list_result = self.cover_left(new_Chart)
            for lst in list_result:
                final_solution = essential_prime + list(
                    map(lambda x: pos_row_left[x], lst)
                )
                QM_final.append(final_solution)
        return QM_final

    def select(self):
        Chart = np.zeros([len(self.PI), len(self.minterm_list)])
        for i in range(len(self.PI)):
            for j in range(len(self.minterm_list)):
                if self._comp_binary_same(
                    self.PI[i].term, self.num2str(self.minterm_list[j])
                ):
                    Chart[i][j] = 1

        primes = self.find_minimum_cost(Chart)
        count=0
        for prime in primes:
            str = ''
            for i in range(len(self.PI)):
                for j in prime:
                    if i == j:
                        str = str + self.PI[i].term2logic() + ', '
                        count+=1
            if str[-2] == ',':
                str = str[:-2]
        return str,count

    def run(self):
        self.merge(0)
        self.backtracking()
    
    def get_prime_implicants(self):
        prime_implicants = ", ".join([pi.term2logic() for pi in self.PI])
        count = len(self.PI)
        return prime_implicants, count
    


def extract_variables(expression):
    return sorted(set(filter(lambda x: x.isalpha(), expression)))

def get_minterms(expression, variables):
    minterms = []
    symbols = {var: sympy.symbols(var) for var in variables}
    for var in variables:
        expression = expression.replace(f"{var}!S", f"~{var}")

    expr = sympy.sympify(expression, locals=symbols)
    total_vars = len(variables)
    for i in range(2**total_vars):
        assignments = {symbols[var]: (i >> j) & 1 for j, var in enumerate(reversed(variables))}
        if expr.subs(assignments):
            minterms.append(i)
    return minterms

def get_maxterms(expression, variables):
    maxterms = []
    symbols = {var: sympy.symbols(var) for var in variables}
    for var in variables:
        expression = expression.replace(f"{var}!S", f"~{var}")

    expr = sympy.sympify(expression, locals=symbols)
    total_vars = len(variables)
    for i in range(2**total_vars):
        assignments = {symbols[var]: (i >> j) & 1 for j, var in enumerate(reversed(variables))}
        if not expr.subs(assignments):
            maxterms.append(i)
    return maxterms

def minterms_to_SOP(minterms, variables):
    sop_expressions = []
    for minterm in minterms:
        terms = []
        for idx, var in enumerate(variables):
            if (minterm >> idx) & 1:
                terms.append(var)
            else:
                terms.append(f"~{var}")
        sop_expressions.append(f"({' & '.join(terms)})")
    return " | ".join(sop_expressions)

def maxterms_to_POS(maxterms, variables):
    pos_expressions = []
    for maxterm in maxterms:
        terms = []
        for idx, var in enumerate(variables):
            if (maxterm >> idx) & 1:
                terms.append(f"~{var}")
            else:
                terms.append(var)
        pos_expressions.append(f"({' | '.join(terms)})")
    return " & ".join(pos_expressions)

def minimized_SOP(expression, variables):
    symbols = {var: sympy.symbols(var) for var in variables}
    
    for var in variables:
        expression = expression.replace(f"{var}'", f"~{var}")

    expr = sympy.sympify(expression, locals=symbols)

    minimized_expr = sympy.simplify_logic(expr, form='dnf')

    return str(minimized_expr)

def extract_literals(expression):
    """Returns a set of all literals in the expression."""
    literals = set()
    for char in expression:
        if char.isalpha(): 
            literals.add(char)
    return literals

def saved_literals(original, minimized):
    original_literals = extract_literals(original)
    minimized_literals = extract_literals(minimized)
    return len(original_literals - minimized_literals)

def minimized_POS(expression, variables):
    symbols = {var: sympy.symbols(var) for var in variables}
    
    for var in variables:
        expression = expression.replace(f"{var}'", f"~{var}")

    expr = sympy.sympify(expression, locals=symbols)

    minimized_expr = sympy.simplify_logic(expr, form='cnf')

    return str(minimized_expr)

def get_minimized_expressions_from_file(input_filename):
    minimized_expressions = []
    with open(input_filename, 'r') as infile:
        for line in infile:
            expression = line.strip()
            variables = extract_variables(expression)
            minimized_expression = minimized_SOP(expression, variables)
            minimized_expressions.append(minimized_expression)
    return minimized_expressions

def get_variables_from_file(input_filename):
    variables = []
    with open(input_filename, 'r') as infile:
        for line in infile:
            expression = line.strip()
            variables = extract_variables(expression)
    return variables

def parse_sop_formulas(input_lines):
    formulas = {}
    for line in input_lines:
        key, expression = line.split(" = ")
        formulas[key.strip()] = expression.strip()
    return formulas


def write_to_file(filename, data):
    with open(filename, 'a') as f: 
        f.write(data + '\n')

def main(input_filename, output_filename):
    output_data = []

    with open(input_filename, 'r') as infile:
        for line in infile:
            expression = line.strip()
            variables = extract_variables(expression)


            # SOP
            minterms = get_minterms(expression, variables)
            sop_expression = minterms_to_SOP(minterms, variables)
            output_data.append(f"SOP: {sop_expression}")

            # POS
            maxterms = get_maxterms(expression, variables)
            pos_expression = maxterms_to_POS(maxterms, variables)
            output_data.append(f"POS: {pos_expression}")

            # Inverse SOP
            inverse_expr = f"~({expression})"
            inverse_minterms = get_minterms(inverse_expr, variables)
            inverse_sop_expression = minterms_to_SOP(inverse_minterms, variables)
            output_data.append(f"Inverse SOP: {inverse_sop_expression}")

            # Inverse POS
            inverse_maxterms = get_maxterms(inverse_expr, variables)
            inverse_pos_expression = maxterms_to_POS(inverse_maxterms, variables)
            output_data.append(f"Inverse POS: {inverse_pos_expression}")

            # Minimized SOP
            minimized_sop_expression = minimized_SOP(expression, variables)
            output_data.append(f"Minimized SOP: {minimized_sop_expression}")

            literal_savings = saved_literals(sop_expression, minimized_sop_expression)
            output_data.append(f"Saved literals (vs canonical SOP): {literal_savings}")

            # Minimized POS
            minimized_pos_expression = minimized_POS(expression, variables)
            output_data.append(f"Minimized POS: {minimized_pos_expression}")

            literal_savings_pos = saved_literals(pos_expression, minimized_pos_expression)
            output_data.append(f"Saved literals (vs canonical POS): {literal_savings_pos}")

            # Extract prime implicants and Essential prime implicants and their count and add to output data
            minterms_list = get_minterms(expression, variables)
            qm = QM(len(variables), minterms_list)
            qm.run()
            epi,epi_count=qm.select()
            prime_implicants, pi_count = qm.get_prime_implicants()
            output_data.append(f"Prime Implicants: {prime_implicants}")
            output_data.append(f"Number of Prime Implicants: {pi_count}")
            output_data.append(f"Essential Prime Implicants: {epi}")
            output_data.append(f"Number of Essential Prime Implicants: {epi_count}")

            # ON-Set minterms and their number
            minterms = get_minterms(expression, variables)
            output_data.append(f"ON-Set minterms: {minterms}")
            output_data.append(f"Number of ON-Set minterms: {len(minterms)}")

            # ON-Set maxterms and their number
            maxterms  = get_maxterms(expression, variables)
            output_data.append(f"ON-Set maxterms: {maxterms}")
            output_data.append(f"Number of ON-Set maxterms: {len(maxterms)}")



            output_data.append("\n")  

    with open(output_filename, 'w') as outfile:
        for line in output_data:
            outfile.write(line + "\n")


if __name__ == "__main__":
    main("input.eqn", "output_ENQ.txt")

