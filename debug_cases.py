from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import Always, CaseStatement

with open('input/sample_fsm.v', 'r') as f:
    code = f.read()

parser = VerilogParser()
ast = parser.parse(code, debug=0)

print("Looking for case statements...")

def find_cases(node, depth=0):
    indent = "  " * depth
    node_type = type(node).__name__
    
    if isinstance(node, CaseStatement):
        print(f"{indent}▶ FOUND CaseStatement!")
        print(f"{indent}  comp: {node.comp}")
        print(f"{indent}  caselist length: {len(node.caselist) if node.caselist else 0}")
    
    if hasattr(node, 'children'):
        for child in node.children():
            find_cases(child, depth + 1)

find_cases(ast)
