"""
Stage-1: Verilog FSM Analysis Pipeline
--------------------------------------
This script parses a Verilog file using PyVerilog, generates the AST,
and extracts basic FSM-related information:
    - Module names
    - Register declarations (possible FSM state registers)
    - Case statements (FSM transitions)

Input file: ../input/sample_fsm.v
"""

from pyverilog.vparser.parser import parse
from pyverilog.vparser.ast import ModuleDef, Decl, Reg, CaseStatement

# -------------------------------
# Function: Parse Verilog File
# -------------------------------
def parse_verilog_file(filepath):
    """
    Parse the Verilog file and return the AST.
    """
    ast, _ = parse([filepath])
    return ast

# -------------------------------
# Function: Extract Modules
# -------------------------------
def extract_modules(ast):
    """
    Traverse AST and collect module names.
    """
    modules = []
    for item in ast.description.definitions:
        if isinstance(item, ModuleDef):
            modules.append(item.name)
    return modules

# -------------------------------
# Function: Extract Registers
# -------------------------------
def extract_registers(ast):
    """
    Traverse AST and collect register declarations.
    These may represent FSM state registers.
    """
    registers = []
    for item in ast.description.definitions:
        if isinstance(item, ModuleDef):
            for element in item.items:
                if isinstance(element, Decl):
                    for decl in element.list:
                        if isinstance(decl, Reg):
                            registers.append(decl.name)
    return registers

# -------------------------------
# Function: Detect Case Statements
# -------------------------------
def detect_case_statements(ast):
    """
    Traverse AST and detect case statements.
    These often represent FSM transitions.
    """
    case_statements = []

    def traverse(node):
        # Recursively traverse AST
        for child in node.children():
            if isinstance(child, CaseStatement):
                case_statements.append(child)
            traverse(child)

    traverse(ast)
    return case_statements

# -------------------------------
# Main Execution
# -------------------------------
if __name__ == "__main__":
    filepath = "../input/sample_fsm.v"

    # Step 1: Parse Verilog file
    ast = parse_verilog_file(filepath)

    # Step 2: Extract module names
    modules = extract_modules(ast)
    print("Modules Found:")
    for m in modules:
        print(f"  - {m}")

    # Step 3: Extract registers
    registers = extract_registers(ast)
    print("\nRegisters Found (possible FSM state registers):")
    for r in registers:
        print(f"  - {r}")

    # Step 4: Detect case statements
    cases = detect_case_statements(ast)
    print("\nCase Statements Found (FSM transitions):")
    for idx, c in enumerate(cases, 1):
        print(f"  - Case {idx}: expression = {c.comp}")