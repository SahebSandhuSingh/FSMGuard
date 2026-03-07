"""
FSMGuard - Stage 1: Verilog FSM Extraction Pipeline (Enhanced)
===============================================================

This module parses Verilog RTL designs using PyVerilog and extracts
complete FSM information including:
- States from parameters/localparams
- Transitions with nested condition handling
- Reset state detection
- Multiple FSM support
- Self-loop detection
- Default case handling

Output: Python dictionary ready for Stage 2 graph construction

Author: FSMGuard Team
Date: 2026-03-07
Version: 2.0 (Enhanced with nested conditions, validation, JSON output)
"""

import os
import json
import re
from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import (
    ModuleDef, Always, IfStatement, CaseStatement, Case,
    NonblockingSubstitution, Identifier, Parameter, Localparam, Decl
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def clean_condition(condition_str):
    """
    Clean and normalize condition strings using regex.
    
    Args:
        condition_str: Raw condition string from AST
    
    Returns:
        Cleaned condition string
    """
    if not condition_str:
        return ""
    
    # Remove excessive whitespace
    condition_str = re.sub(r'\s+', ' ', condition_str.strip())
    
    # Remove parentheses around simple identifiers
    condition_str = re.sub(r'^\(([\w_]+)\)$', r'\1', condition_str)
    
    return condition_str


def get_identifier_name(node):
    """
    Extract identifier name from AST node.
    
    Args:
        node: AST node
    
    Returns:
        String name or representation
    """
    if node is None:
        return ""
    
    if isinstance(node, Identifier):
        return node.name
    elif hasattr(node, 'var'):
        # Handle Lvalue/Rvalue nodes that have .var attribute
        return get_identifier_name(node.var)
    elif hasattr(node, 'name'):
        return node.name
    else:
        return str(node)


def extract_condition_string(cond_node):
    """
    Convert condition AST node to string representation.
    
    Args:
        cond_node: Condition AST node
    
    Returns:
        String representation of condition
    """
    if cond_node is None:
        return ""
    
    # Simple conversion to string and clean
    cond_str = str(cond_node).strip()
    return clean_condition(cond_str)


# ============================================================================
# CORE EXTRACTION FUNCTIONS
# ============================================================================

def parse_verilog_file(filepath):
    """
    Parse Verilog file and return AST.
    
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
        raise Exception(f"Failed to parse Verilog file: {e}")


def extract_states(ast):
    """
    Extract all FSM state names from parameter/localparam declarations.
    
    Looks for:
    - parameter STATE = value;
    - localparam STATE = value;
    
    Args:
        ast: PyVerilog AST
    
    Returns:
        List of state names (strings), duplicates removed
    """
    states = []
    
    # Traverse all module definitions
    for item in ast.description.definitions:
        if not isinstance(item, ModuleDef):
            continue
        
        # Look through module items for parameters
        for element in item.items:
            # Handle direct Parameter nodes (less common)
            if isinstance(element, Parameter):
                if hasattr(element, 'name'):
                    states.append(element.name)
            
            # Handle direct Localparam nodes (less common)
            elif isinstance(element, Localparam):
                if hasattr(element, 'name'):
                    states.append(element.name)
            
            # Handle Decl nodes that contain Parameters (most common case)
            elif isinstance(element, Decl):
                for decl_item in element.list:
                    if isinstance(decl_item, (Parameter, Localparam)):
                        if hasattr(decl_item, 'name'):
                            states.append(decl_item.name)
    
    # Remove duplicates while preserving order (requirement #4)
    states = list(dict.fromkeys(states))
    
    return states


def extract_transitions_from_statement(stmt, src_state, parent_conditions):
    """
    Recursively extract transitions from a statement.
    
    Handles:
    - Nested if statements (combines conditions with &&)
    - State assignments
    - Self-loops
    
    Args:
        stmt: Statement AST node
        src_state: Source state name
        parent_conditions: List of parent condition strings
    
    Returns:
        List of transition dictionaries
    """
    transitions = []
    
    if stmt is None:
        return transitions
    
    # Handle IfStatement - NESTED CONDITIONS REQUIREMENT
    if isinstance(stmt, IfStatement):
        # Extract this level's condition
        condition_str = extract_condition_string(stmt.cond)
        
        # Combine with parent conditions using && (requirement)
        all_conditions = parent_conditions + [condition_str]
        
        # Process true branch
        if stmt.true_statement:
            transitions.extend(
                extract_transitions_from_statement(
                    stmt.true_statement,
                    src_state,
                    all_conditions
                )
            )
        
        # Process else branch
        if stmt.false_statement:
            transitions.extend(
                extract_transitions_from_statement(
                    stmt.false_statement,
                    src_state,
                    parent_conditions
                )
            )
    
    # Handle NonblockingSubstitution - state assignment
    elif isinstance(stmt, NonblockingSubstitution):
        # Check if this is a state assignment
        left_side = get_identifier_name(stmt.left)
        
        if 'state' in left_side.lower():
            # Extract destination state
            dst_state = get_identifier_name(stmt.right)
            
            # Combine all parent conditions with &&
            if parent_conditions:
                condition = " && ".join(parent_conditions)
            else:
                condition = "always"
            
            # Clean condition
            condition = clean_condition(condition)
            
            # Add transition (includes self-loops - requirement #6)
            transitions.append({
                "src": src_state,
                "dst": dst_state,
                "condition": condition
            })
    
    # Handle statement blocks
    elif hasattr(stmt, 'statements'):
        for sub_stmt in stmt.statements:
            transitions.extend(
                extract_transitions_from_statement(
                    sub_stmt,
                    src_state,
                    parent_conditions
                )
            )
    
    return transitions


def extract_transitions(ast):
    """
    Extract all FSM transitions from AST.
    
    Handles:
    - Multiple FSMs (merges all transitions - requirement #3)
    - Case statements
    - Default cases (requirement #7)
    - Self-loops (requirement #6)
    
    Args:
        ast: PyVerilog AST
    
    Returns:
        List of transition dictionaries, duplicates removed (requirement #5)
    """
    all_transitions = []
    
    def process_case_statement(case_stmt):
        """Process a single case statement and extract transitions."""
        transitions = []
        
        # Process each case branch
        for case_item in case_stmt.caselist:
            if not isinstance(case_item, Case):
                continue
            
            # Get source state from case label
            src_state = None
            is_default = False
            
            if case_item.cond and len(case_item.cond) > 0:
                cond_val = case_item.cond[0]
                
                # Check for default case (requirement #7)
                cond_str = str(cond_val).strip().lower()
                if 'default' in cond_str:
                    src_state = "ANY"
                    is_default = True
                else:
                    src_state = get_identifier_name(cond_val)
            
            if not src_state:
                continue
            
            # Extract transitions from case body
            if case_item.statement:
                case_transitions = extract_transitions_from_statement(
                    case_item.statement,
                    src_state,
                    []  # No parent conditions at case level
                )
                
                # Mark default transitions (requirement #7)
                if is_default:
                    for trans in case_transitions:
                        if trans["condition"] == "always":
                            trans["condition"] = "default"
                
                transitions.extend(case_transitions)
        
        return transitions
    
    def traverse_for_cases(node):
        """Recursively find all case statements (handles multiple FSMs)."""
        if isinstance(node, CaseStatement):
            # Extract transitions from this case statement
            case_transitions = process_case_statement(node)
            all_transitions.extend(case_transitions)
        
        # Traverse children
        if hasattr(node, 'children'):
            for child in node.children():
                traverse_for_cases(child)
    
    # Start traversal from root (finds all FSMs - requirement #3)
    traverse_for_cases(ast)
    
    # Remove duplicate transitions (requirement #5)
    # Use (src, dst, condition) as unique key
    unique_transitions = []
    seen = set()
    
    for trans in all_transitions:
        key = (trans["src"], trans["dst"], trans["condition"])
        if key not in seen:
            seen.add(key)
            unique_transitions.append(trans)
    
    return unique_transitions


def detect_reset_state(ast, states):
    """
    Detect the reset state from reset logic.
    
    Looks for patterns like:
        if(reset) state <= IDLE;
        if(rst) state <= S0;
    
    Args:
        ast: PyVerilog AST
        states: List of known states
    
    Returns:
        Reset state name (string) or first state if not found
    """
    reset_state = None
    
    def find_reset_assignment(node):
        """Recursively find reset assignment."""
        nonlocal reset_state
        
        if isinstance(node, IfStatement):
            cond_str = str(node.cond).lower()
            
            # Check if this is a reset condition
            if 'reset' in cond_str or 'rst' in cond_str:
                # Look for state assignment in true branch
                if isinstance(node.true_statement, NonblockingSubstitution):
                    left = get_identifier_name(node.true_statement.left)
                    if 'state' in left.lower():
                        reset_state = get_identifier_name(node.true_statement.right)
                        return True
                
                # Check for block statements
                elif hasattr(node.true_statement, 'statements'):
                    for stmt in node.true_statement.statements:
                        if isinstance(stmt, NonblockingSubstitution):
                            left = get_identifier_name(stmt.left)
                            if 'state' in left.lower():
                                reset_state = get_identifier_name(stmt.right)
                                return True
        
        # Traverse children
        if hasattr(node, 'children'):
            for child in node.children():
                if find_reset_assignment(child):
                    return True
        
        return False
    
    # Search for reset state
    find_reset_assignment(ast)
    
    # If not found, use first state (fallback)
    if not reset_state and states:
        reset_state = states[0]
    
    return reset_state


def build_fsm_data(states, transitions, reset_state):
    """
    Build the final FSM data dictionary.
    
    Args:
        states: List of state names
        transitions: List of transition dictionaries
        reset_state: Reset state name
    
    Returns:
        FSM data dictionary in Stage 2 format
    """
    return {
        "states": states,
        "transitions": transitions,
        "reset_state": reset_state
    }


# ============================================================================
# VALIDATION AND OUTPUT (NEW REQUIREMENTS)
# ============================================================================

def validate_fsm_data(fsm_data):
    """
    Validate FSM data before returning (requirement #5).
    
    Checks:
    1. States list must not be empty
    2. Transitions list must not be empty (warning only)
    3. Reset state must exist in states list
    4. No duplicate states
    5. No duplicate transitions
    
    Args:
        fsm_data: FSM data dictionary
    
    Returns:
        Validated FSM data dictionary
    """
    # Check 1: States list must not be empty
    if not fsm_data.get("states"):
        print("⚠️  WARNING: No states found in FSM. Returning empty FSM data.")
        return {
            "states": [],
            "transitions": [],
            "reset_state": ""
        }
    
    # Check 4: Remove duplicate states
    fsm_data["states"] = list(dict.fromkeys(fsm_data["states"]))
    
    # Check 2: Transitions list warning
    if not fsm_data.get("transitions"):
        print("⚠️  WARNING: No transitions found in FSM")
        fsm_data["transitions"] = []
    
    # Check 3: Reset state must exist in states list
    reset_state = fsm_data.get("reset_state", "")
    if reset_state and reset_state not in fsm_data["states"]:
        print(f"⚠️  WARNING: Reset state '{reset_state}' not in states list")
        print(f"           Setting reset_state to '{fsm_data['states'][0]}'")
        fsm_data["reset_state"] = fsm_data["states"][0]
    elif not reset_state and fsm_data["states"]:
        fsm_data["reset_state"] = fsm_data["states"][0]
    
    # Check 5: Remove duplicate transitions (already done in extract_transitions)
    
    return fsm_data


def save_fsm_data(fsm_data, output_path="output/stage1_output.json"):
    """
    Save FSM data to JSON file (requirement #4).
    
    Creates output/ directory if it doesn't exist.
    
    Args:
        fsm_data: FSM data dictionary
        output_path: Path to output JSON file
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save to JSON with pretty printing
    with open(output_path, 'w') as f:
        json.dump(fsm_data, f, indent=2)
    
    # Print confirmation (requirement #4)
    print(f"Stage 01 complete. FSM data saved to: {output_path}")


def test_against_example(fsm_data):
    """
    Test implementation against the example FSM (requirement #8).
    
    Expected:
    - states: IDLE, AUTH, ACCESS
    - transitions: IDLE→AUTH(login_req), AUTH→ACCESS(password_ok)
    - reset_state: IDLE
    
    Args:
        fsm_data: FSM data to validate
    
    Returns:
        Boolean indicating if test passed
    """
    print("\n" + "=" * 70)
    print("Running Validation Tests (Requirement #8)")
    print("=" * 70)
    
    all_passed = True
    
    # Test 1: Check if states contain expected values
    expected_states = {"IDLE", "AUTH", "ACCESS"}
    actual_states = set(fsm_data.get("states", []))
    
    if expected_states.issubset(actual_states):
        print("✓ Test 1 PASSED: States contain IDLE, AUTH, ACCESS")
    else:
        print(f"✗ Test 1 FAILED: Expected states {expected_states}, got {actual_states}")
        all_passed = False
    
    # Test 2: Check transitions
    transitions = fsm_data.get("transitions", [])
    
    # Check for IDLE → AUTH with login_req
    idle_auth = any(
        t["src"] == "IDLE" and t["dst"] == "AUTH" and "login_req" in t["condition"]
        for t in transitions
    )
    
    if idle_auth:
        print("✓ Test 2 PASSED: IDLE → AUTH transition with login_req found")
    else:
        print("✗ Test 2 FAILED: IDLE → AUTH transition with login_req not found")
        all_passed = False
    
    # Check for AUTH → ACCESS with password_ok
    auth_access = any(
        t["src"] == "AUTH" and t["dst"] == "ACCESS" and "password_ok" in t["condition"]
        for t in transitions
    )
    
    if auth_access:
        print("✓ Test 3 PASSED: AUTH → ACCESS transition with password_ok found")
    else:
        print("✗ Test 3 FAILED: AUTH → ACCESS transition with password_ok not found")
        all_passed = False
    
    # Test 3: Check reset state
    if fsm_data.get("reset_state") == "IDLE":
        print("✓ Test 4 PASSED: Reset state is IDLE")
    else:
        print(f"✗ Test 4 FAILED: Reset state is '{fsm_data.get('reset_state')}', expected 'IDLE'")
        all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("🎉 All validation tests PASSED!")
    else:
        print("⚠️  Some validation tests FAILED")
    
    return all_passed


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def stage1_pipeline(filepath, output_path="output/stage1_output.json"):
    """
    Complete Stage 1 pipeline: Parse Verilog and extract FSM data.
    
    This is the main entry point for Stage 1.
    
    Pipeline:
    1. Parse Verilog file using PyVerilog
    2. Extract FSM states from parameters
    3. Extract transitions from case statements (with nested condition support)
    4. Detect reset state from reset logic
    5. Validate FSM data
    6. Save to JSON file
    7. Return FSM data dictionary
    
    Args:
        filepath: Path to Verilog file
        output_path: Path to save JSON output (default: output/stage1_output.json)
    
    Returns:
        FSM data dictionary ready for Stage 2
    
    Example:
        >>> fsm_data = stage1_pipeline("../input/sample_fsm.v")
        >>> print(fsm_data["states"])
        ['IDLE', 'AUTH', 'ACCESS']
    """
    print("=" * 70)
    print("FSMGuard - Stage 1: Verilog FSM Extraction (Enhanced)")
    print("=" * 70)
    
    try:
        # Step 1: Parse Verilog file
        print(f"\n[1/6] Parsing Verilog file: {filepath}")
        ast = parse_verilog_file(filepath)
        print("      ✓ AST generated successfully")
        
        # Step 2: Extract states
        print("\n[2/6] Extracting FSM states...")
        states = extract_states(ast)
        print(f"      ✓ Found {len(states)} states: {states}")
        
        # Step 3: Extract transitions (with nested condition support)
        print("\n[3/6] Extracting FSM transitions...")
        print("      (Handling nested conditions, multiple FSMs, self-loops)")
        transitions = extract_transitions(ast)
        print(f"      ✓ Found {len(transitions)} transitions")
        
        # Step 4: Detect reset state
        print("\n[4/6] Detecting reset state...")
        reset_state = detect_reset_state(ast, states)
        print(f"      ✓ Reset state: {reset_state}")
        
        # Step 5: Build and validate FSM data
        print("\n[5/6] Building and validating FSM data...")
        fsm_data = build_fsm_data(states, transitions, reset_state)
        fsm_data = validate_fsm_data(fsm_data)
        print("      ✓ FSM data validated")
        
        # Step 6: Save to JSON file (requirement #4)
        print(f"\n[6/6] Saving FSM data to JSON...")
        save_fsm_data(fsm_data, output_path)
        
        print("\n" + "=" * 70)
        
        return fsm_data
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("Returning empty FSM data")
        return {
            "states": [],
            "transitions": [],
            "reset_state": ""
        }


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run Stage 1 pipeline
    filepath = "../input/sample_fsm.v"
    
    # Adjust path if running from different directory
    if not os.path.exists(filepath):
        filepath = "input/sample_fsm.v"
    
    fsm_data = stage1_pipeline(filepath)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 FSM Data Summary")
    print("=" * 70)
    print(f"States ({len(fsm_data['states'])}): {fsm_data['states']}")
    print(f"Reset State: {fsm_data['reset_state']}")
    print(f"\nTransitions ({len(fsm_data['transitions'])}):")
    for trans in fsm_data['transitions']:
        src = trans['src']
        dst = trans['dst']
        cond = trans['condition']
        # Highlight self-loops
        self_loop = " [SELF-LOOP]" if src == dst else ""
        print(f"  {src:10} → {dst:10}  [{cond}]{self_loop}")
