from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import (
    CaseStatement, Case, IfStatement, NonblockingSubstitution, Identifier
)

def get_identifier_name(node):
    if isinstance(node, Identifier):
        return node.name
    elif hasattr(node, 'name'):
        return node.name
    else:
        return str(node)

def extract_condition_string(cond_node):
    if cond_node is None:
        return ""
    cond_str = str(cond_node).strip()
    return cond_str

def extract_transitions_from_statement(stmt, src_state, parent_conditions):
    transitions = []
    
    print(f"    extract_transitions_from_statement called:")
    print(f"      stmt type: {type(stmt).__name__}")
    print(f"      src_state: {src_state}")
    print(f"      parent_conditions: {parent_conditions}")
    
    if stmt is None:
        return transitions
    
    # Handle IfStatement
    if isinstance(stmt, IfStatement):
        print(f"      -> This is an IfStatement")
        condition_str = extract_condition_string(stmt.cond)
        all_conditions = parent_conditions + [condition_str]
        
        if stmt.true_statement:
            transitions.extend(
                extract_transitions_from_statement(
                    stmt.true_statement,
                    src_state,
                    all_conditions
                )
            )
    
    # Handle NonblockingSubstitution
    elif isinstance(stmt, NonblockingSubstitution):
        print(f"      -> This is NonblockingSubstitution!")
        left_side = get_identifier_name(stmt.left)
        print(f"         left_side: {left_side}")
        
        if 'state' in left_side.lower():
            dst_state = get_identifier_name(stmt.right)
            print(f"         dst_state: {dst_state}")
            
            if parent_conditions:
                condition = " && ".join(parent_conditions)
            else:
                condition = "always"
            
            print(f"         condition: {condition}")
            
            transitions.append({
                "src": src_state,
                "dst": dst_state,
                "condition": condition
            })
            print(f"         ✓ Added transition!")
    
    return transitions

with open('input/sample_fsm.v', 'r') as f:
    code = f.read()

parser = VerilogParser()
ast = parser.parse(code, debug=0)

print("Manual transition extraction test...\n")

def find_and_process_cases(node):
    if isinstance(node, CaseStatement):
        print("Found CaseStatement!\n")
        
        for idx, case_item in enumerate(node.caselist):
            if isinstance(case_item, Case):
                src_state = get_identifier_name(case_item.cond[0])
                print(f"Case {idx}: src_state = {src_state}")
                
                if case_item.statement:
                    transitions = extract_transitions_from_statement(
                        case_item.statement,
                        src_state,
                        []
                    )
                    print(f"  Extracted {len(transitions)} transitions\n")
    
    if hasattr(node, 'children'):
        for child in node.children():
            find_and_process_cases(child)

find_and_process_cases(ast)
