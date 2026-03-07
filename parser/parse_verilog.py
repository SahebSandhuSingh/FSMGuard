"""
FSMGuard - Stage 1: Verilog FSM Extraction Pipeline
====================================================

This module parses a Verilog RTL design using PyVerilog and extracts
FSM structure information including states, transitions, and reset state.

The output is a structured dictionary that integrates directly with Stage 2.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import json
from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import (
    ModuleDef, Parameter, Decl, Always, CaseStatement, 
    Case, IfStatement, NonblockingSubstitution, BlockingSubstitution,
    Identifier, Rvalue, Lvalue, IntConst, StringConst
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_node_name(node):
    """
    Extract the name/value from various AST node types.
    Handles Identifier, IntConst, StringConst, etc.
    """
    if node is None:
        return None
    
    if isinstance(node, Identifier):
        return node.name
    elif isinstance(node, IntConst):
        return node.value
    elif isinstance(node, StringConst):
        return node.value
    elif isinstance(node, Rvalue):
        return get_node_name(node.var)
    elif isinstance(node, Lvalue):
        return get_node_name(node.var)
    elif hasattr(node, 'name'):
        return node.name
    elif hasattr(node, 'value'):
        return node.value
    
    return str(node)


def traverse_ast(node, node_list, node_type):
    """
    Recursively traverse AST and collect nodes of specific type.
    
    Args:
        node: Current AST node
        node_list: List to append matching nodes
        node_type: Type of node to collect
    """
    if node is None:
        return
    
    if isinstance(node, node_type):
        node_list.append(node)
    
    # Traverse children
    for child in node.children():
        traverse_ast(child, node_list, node_type)


def extract_condition_string(cond_node):
    """
    Convert condition AST node to a readable string.
    
    Args:
        cond_node: AST node representing condition
        
    Returns:
        String representation of condition
    """
    if cond_node is None:
        return "always"
    
    # Try to get a meaningful condition string
    cond_str = get_node_name(cond_node)
    if cond_str:
        return str(cond_str)
    
    # For complex conditions, try to extract meaningful info
    if hasattr(cond_node, '__class__'):
        class_name = cond_node.__class__.__name__
        if class_name in ['Eq', 'NotEq', 'And', 'Or', 'LessThan', 'GreaterThan']:
            # Try to extract left and right operands
            left = get_node_name(cond_node.left) if hasattr(cond_node, 'left') else ""
            right = get_node_name(cond_node.right) if hasattr(cond_node, 'right') else ""
            return f"{left}_{class_name}_{right}" if left or right else "condition"
    
    return "condition"


# ============================================================================
# STAGE 1 PIPELINE FUNCTIONS
# ============================================================================

def parse_verilog_file(filepath):
    """
    Parse Verilog file and return the AST.
    
    Args:
        filepath: Path to Verilog file
        
    Returns:
        PyVerilog AST object
        
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If parsing fails
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Verilog file not found: {filepath}")
    
    try:
        # Read Verilog file content
        with open(filepath, 'r') as f:
            verilog_code = f.read()
        
        # Parse using VerilogParser (avoids iverilog dependency)
        parser = VerilogParser()
        ast = parser.parse(verilog_code, debug=0)
        return ast
    except Exception as e:
        raise Exception(f"Failed to parse Verilog file: {str(e)}")


def extract_states(ast):
    """
    Extract FSM states from Verilog AST.
    
    Looks for states in:
    1. Parameter declarations
    2. Case statement labels
    
    Args:
        ast: PyVerilog AST
        
    Returns:
        List of unique state names (strings)
    """
    states = set()
    
    # Extract states from parameter/localparam declarations
    for definition in ast.description.definitions:
        if isinstance(definition, ModuleDef):
            for item in definition.items:
                # Check for direct parameter declarations
                if isinstance(item, Parameter):
                    # Parameter has name attribute directly
                    state_name = get_node_name(item.name)
                    if state_name:
                        states.add(state_name)
                
                # Check for decl with parameters
                if isinstance(item, Decl):
                    for decl_item in item.list:
                        if isinstance(decl_item, Parameter):
                            # Parameter has name attribute directly
                            state_name = get_node_name(decl_item.name)
                            if state_name:
                                states.add(state_name)
    
    # Extract states from case statement labels
    case_statements = []
    traverse_ast(ast, case_statements, CaseStatement)
    
    for case_stmt in case_statements:
        if case_stmt.caselist:
            for case_item in case_stmt.caselist:
                if isinstance(case_item, Case):
                    # Extract state from case condition
                    if case_item.cond:
                        for cond in case_item.cond:
                            state_name = get_node_name(cond)
                            if state_name and state_name != 'default':
                                states.add(state_name)
    
    return sorted(list(states))


def extract_transitions(ast):
    """
    Extract FSM transitions from case statements.
    
    Looks for state assignments (state <= next_state) within case blocks.
    
    Args:
        ast: PyVerilog AST
        
    Returns:
        List of transition dictionaries:
        [{"src": "STATE1", "dst": "STATE2", "condition": "cond"}, ...]
    """
    transitions = []
    transitions_set = set()  # To avoid duplicates
    
    # Find all case statements
    case_statements = []
    traverse_ast(ast, case_statements, CaseStatement)
    
    for case_stmt in case_statements:
        if not case_stmt.caselist:
            continue
        
        # Iterate through each case branch
        for case_item in case_stmt.caselist:
            if not isinstance(case_item, Case):
                continue
            
            # Get source state from case condition
            src_state = None
            if case_item.cond:
                for cond in case_item.cond:
                    src_state = get_node_name(cond)
                    if src_state and src_state != 'default':
                        break
            
            if not src_state:
                continue
            
            # Extract transitions from case body
            if case_item.statement:
                extract_transitions_from_statement(
                    case_item.statement, 
                    src_state, 
                    transitions,
                    transitions_set,
                    condition=None
                )
    
    return transitions


def extract_transitions_from_statement(stmt, src_state, transitions, transitions_set, condition):
    """
    Recursively extract state transitions from a statement.
    
    Args:
        stmt: AST statement node
        src_state: Source state name
        transitions: List to append transitions
        transitions_set: Set to track duplicates
        condition: Current condition (for nested if statements)
    """
    if stmt is None:
        return
    
    # Handle if-else statements
    if isinstance(stmt, IfStatement):
        # Extract condition
        if_condition = extract_condition_string(stmt.cond)
        
        # Process true branch
        if stmt.true_statement:
            extract_transitions_from_statement(
                stmt.true_statement,
                src_state,
                transitions,
                transitions_set,
                if_condition
            )
        
        # Process false branch
        if stmt.false_statement:
            # For else clause, condition might be negation or just "else"
            else_condition = f"not_{if_condition}" if if_condition != "always" else "else"
            extract_transitions_from_statement(
                stmt.false_statement,
                src_state,
                transitions,
                transitions_set,
                else_condition
            )
    
    # Handle non-blocking assignments (state <= next_state)
    elif isinstance(stmt, NonblockingSubstitution):
        left_name = get_node_name(stmt.left)
        right_name = get_node_name(stmt.right)
        
        # Check if this is a state assignment
        if left_name == 'state' and right_name:
            dst_state = right_name
            trans_condition = condition if condition else "always"
            
            # Create transition tuple for duplicate checking
            trans_key = (src_state, dst_state, trans_condition)
            
            if trans_key not in transitions_set:
                transitions_set.add(trans_key)
                transitions.append({
                    "src": src_state,
                    "dst": dst_state,
                    "condition": trans_condition
                })
    
    # Handle blocking assignments (state = next_state)
    elif isinstance(stmt, BlockingSubstitution):
        left_name = get_node_name(stmt.left)
        right_name = get_node_name(stmt.right)
        
        if left_name == 'state' and right_name:
            dst_state = right_name
            trans_condition = condition if condition else "always"
            
            trans_key = (src_state, dst_state, trans_condition)
            
            if trans_key not in transitions_set:
                transitions_set.add(trans_key)
                transitions.append({
                    "src": src_state,
                    "dst": dst_state,
                    "condition": trans_condition
                })
    
    # Handle block statements (begin-end)
    elif hasattr(stmt, 'statement'):
        # Single statement in block
        extract_transitions_from_statement(
            stmt.statement,
            src_state,
            transitions,
            transitions_set,
            condition
        )
    
    # Recursively process children
    for child in stmt.children():
        extract_transitions_from_statement(
            child,
            src_state,
            transitions,
            transitions_set,
            condition
        )


def detect_reset_state(ast):
    """
    Detect the reset state from reset logic.
    
    Looks for patterns like:
        if(reset) state <= STATE;
    
    Args:
        ast: PyVerilog AST
        
    Returns:
        Reset state name (string) or None if not found
    """
    # Find all always blocks
    always_blocks = []
    traverse_ast(ast, always_blocks, Always)
    
    for always in always_blocks:
        if always.statement:
            reset_state = find_reset_in_statement(always.statement)
            if reset_state:
                return reset_state
    
    return None


def find_reset_in_statement(stmt):
    """
    Recursively search for reset state assignment in a statement.
    
    Args:
        stmt: AST statement node
        
    Returns:
        Reset state name or None
    """
    if stmt is None:
        return None
    
    # Check if this is an if statement with reset condition
    if isinstance(stmt, IfStatement):
        # Check if condition contains 'reset'
        cond_str = extract_condition_string(stmt.cond)
        if cond_str and 'reset' in cond_str.lower():
            # Look for state assignment in true branch
            if stmt.true_statement:
                reset_state = find_state_assignment(stmt.true_statement)
                if reset_state:
                    return reset_state
    
    # Recursively check children
    for child in stmt.children():
        reset_state = find_reset_in_statement(child)
        if reset_state:
            return reset_state
    
    return None


def find_state_assignment(stmt):
    """
    Find state assignment in a statement.
    
    Args:
        stmt: AST statement node
        
    Returns:
        State name being assigned or None
    """
    if stmt is None:
        return None
    
    # Check for non-blocking assignment
    if isinstance(stmt, NonblockingSubstitution):
        left_name = get_node_name(stmt.left)
        if left_name == 'state':
            return get_node_name(stmt.right)
    
    # Check for blocking assignment
    if isinstance(stmt, BlockingSubstitution):
        left_name = get_node_name(stmt.left)
        if left_name == 'state':
            return get_node_name(stmt.right)
    
    # Recursively check children
    for child in stmt.children():
        result = find_state_assignment(child)
        if result:
            return result
    
    return None


def build_fsm_data(states, transitions, reset_state):
    """
    Build the final FSM data dictionary.
    
    Args:
        states: List of state names
        transitions: List of transition dicts
        reset_state: Reset state name
        
    Returns:
        Dictionary in format required by Stage 2:
        {
            "states": [...],
            "transitions": [...],
            "reset_state": "..."
        }
    """
    # If no reset state detected, use first state
    if not reset_state and states:
        reset_state = states[0]
    
    fsm_data = {
        "states": states,
        "transitions": transitions,
        "reset_state": reset_state
    }
    
    return fsm_data


def stage1_pipeline(filepath):
    """
    Complete Stage 1 pipeline: Parse Verilog and extract FSM data.
    
    This is the main entry point that orchestrates:
    1. Verilog parsing
    2. State extraction
    3. Transition extraction
    4. Reset state detection
    5. FSM data dictionary construction
    
    Args:
        filepath: Path to Verilog file
        
    Returns:
        fsm_data dictionary ready for Stage 2
        
    Example:
        >>> fsm_data = stage1_pipeline("../input/sample_fsm.v")
        >>> print(fsm_data["states"])
        ['S0', 'S1', 'S2']
    """
    try:
        # Step 1: Parse Verilog file
        print(f"[Stage 1] Parsing Verilog file: {filepath}")
        ast = parse_verilog_file(filepath)
        
        # Step 2: Extract states
        print("[Stage 1] Extracting FSM states...")
        states = extract_states(ast)
        print(f"  Found {len(states)} states: {states}")
        
        # Step 3: Extract transitions
        print("[Stage 1] Extracting transitions...")
        transitions = extract_transitions(ast)
        print(f"  Found {len(transitions)} transitions")
        
        # Step 4: Detect reset state
        print("[Stage 1] Detecting reset state...")
        reset_state = detect_reset_state(ast)
        print(f"  Reset state: {reset_state}")
        
        # Step 5: Build FSM data
        fsm_data = build_fsm_data(states, transitions, reset_state)
        
        print("[Stage 1] ✓ FSM extraction complete")
        return fsm_data
        
    except Exception as e:
        print(f"[Stage 1] ✗ Error: {str(e)}")
        # Return empty FSM data on error
        return {
            "states": [],
            "transitions": [],
            "reset_state": None
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    filepath = "../input/sample_fsm.v"
    
    # If running from FSMGuard root directory, adjust path
    if not os.path.exists(filepath):
        filepath = "input/sample_fsm.v"
    
    print("=" * 70)
    print("FSMGuard - Stage 1: Verilog FSM Extraction")
    print("=" * 70)
    
    # Run Stage 1 pipeline
    fsm_data = stage1_pipeline(filepath)
    
    # Display results
    print("\n" + "=" * 70)
    print("FSM Data (Stage 1 Output)")
    print("=" * 70)
    print(json.dumps(fsm_data, indent=2))
    print("=" * 70)