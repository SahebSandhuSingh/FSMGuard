from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import Always, CaseStatement, Case

with open('input/sample_fsm.v', 'r') as f:
    code = f.read()

parser = VerilogParser()
ast = parser.parse(code, debug=0)

print("Exploring case statement details...")

def find_cases(node):
    if isinstance(node, CaseStatement):
        print(f"\n▶ Found CaseStatement")
        print(f"  caselist: {node.caselist}")
        
        for idx, case_item in enumerate(node.caselist):
            print(f"\n  Case {idx}:")
            print(f"    Type: {type(case_item).__name__}")
            
            if isinstance(case_item, Case):
                print(f"    cond: {case_item.cond}")
                if case_item.cond:
                    for c in case_item.cond:
                        print(f"      cond item: {c} (type: {type(c).__name__})")
                        if hasattr(c, 'name'):
                            print(f"        name: {c.name}")
                
                print(f"    statement: {case_item.statement}")
                print(f"    statement type: {type(case_item.statement).__name__}")
    
    if hasattr(node, 'children'):
        for child in node.children():
            find_cases(child)

find_cases(ast)
