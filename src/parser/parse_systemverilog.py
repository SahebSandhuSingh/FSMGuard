"""
FSMGuard - SystemVerilog Enhanced Parser
=========================================

This module extends the Verilog parser to support SystemVerilog constructs:
- enum types for FSM states
- typedef declarations
- unique case / priority case
- logic data types
- always_ff / always_comb
- Enhanced state extraction from enum definitions

Author: FSMGuard Team
Date: 2026-03-08
Version: 3.0 (SystemVerilog support)
"""

import re
import json
from typing import Dict, List, Tuple, Optional
from parse_verilog_v2 import (
    parse_verilog_file,
    extract_states as extract_verilog_states,
    extract_transitions as extract_verilog_transitions,
    detect_reset_state
)


# ============================================================================
# SYSTEMVERILOG ENUM PARSING
# ============================================================================

def extract_enum_states(verilog_code: str) -> List[str]:
    """
    Extract FSM states from SystemVerilog enum declarations.
    
    Supports:
        typedef enum logic [2:0] {
            IDLE, FETCH, DECODE, EXECUTE
        } state_t;
        
        enum {RESET, IDLE, RUN} current_state;
    
    Args:
        verilog_code: Raw Verilog/SystemVerilog code string
    
    Returns:
        List of state names extracted from enum declarations
    """
    states = []
    
    # Pattern 1: typedef enum with type
    # typedef enum logic [WIDTH] { STATES } name_t;
    typedef_pattern = r'typedef\s+enum\s+(?:logic|bit|int|reg)?\s*(?:\[[^\]]+\])?\s*\{([^}]+)\}\s*(\w+)\s*;'
    
    for match in re.finditer(typedef_pattern, verilog_code, re.IGNORECASE):
        enum_body = match.group(1)
        states.extend(parse_enum_body(enum_body))
    
    # Pattern 2: Direct enum declaration
    # enum {STATES} variable_name;
    direct_pattern = r'enum\s+(?:logic|bit|int|reg)?\s*(?:\[[^\]]+\])?\s*\{([^}]+)\}\s*\w+\s*(?:,\s*\w+)*\s*;'
    
    for match in re.finditer(direct_pattern, verilog_code, re.IGNORECASE):
        enum_body = match.group(1)
        states.extend(parse_enum_body(enum_body))
    
    # Pattern 3: enum inside module with assignments
    # enum logic [2:0] {IDLE=0, FETCH=1} state;
    inline_pattern = r'enum\s+(?:\w+\s*(?:\[[^\]]+\])?\s*)?\{([^}]+)\}'
    
    for match in re.finditer(inline_pattern, verilog_code, re.IGNORECASE):
        enum_body = match.group(1)
        states.extend(parse_enum_body(enum_body))
    
    return states


def parse_enum_body(enum_body: str) -> List[str]:
    """
    Parse the body of an enum declaration to extract state names.
    
    Handles:
        IDLE, FETCH, DECODE
        IDLE=0, FETCH=1, DECODE=2
        RESET = 3'b000, IDLE = 3'b001
    
    Args:
        enum_body: String content between enum braces
    
    Returns:
        List of state names
    """
    states = []
    
    # Split by comma
    items = enum_body.split(',')
    
    for item in items:
        item = item.strip()
        if not item:
            continue
        
        # Handle assignment: STATE = value
        if '=' in item:
            state_name = item.split('=')[0].strip()
        else:
            state_name = item.strip()
        
        # Remove any bracketed suffixes or bitwidth specifiers
        state_name = re.sub(r'\[.*?\]', '', state_name).strip()
        
        if state_name and state_name.isidentifier():
            states.append(state_name)
    
    return states


# ============================================================================
# TYPEDEF HANDLING
# ============================================================================

def extract_typedefs(verilog_code: str) -> Dict[str, str]:
    """
    Extract typedef declarations mapping type names to their definitions.
    
    Example:
        typedef enum {IDLE, RUN} state_t;
        -> {'state_t': 'enum {IDLE, RUN}'}
    
    Args:
        verilog_code: Raw Verilog/SystemVerilog code
    
    Returns:
        Dictionary mapping typedef names to their definitions
    """
    typedefs = {}
    
    # Pattern: typedef <type_def> <name>;
    pattern = r'typedef\s+(.*?)\s+(\w+)\s*;'
    
    for match in re.finditer(pattern, verilog_code, re.DOTALL):
        type_def = match.group(1).strip()
        type_name = match.group(2).strip()
        typedefs[type_name] = type_def
    
    return typedefs


def resolve_typedef_states(verilog_code: str, typedefs: Dict[str, str]) -> List[str]:
    """
    Find state variables declared with typedef types and extract their states.
    
    Example:
        state_t current_state, next_state;
        where state_t is typedef enum {IDLE, RUN}
    
    Args:
        verilog_code: Raw code
        typedefs: Dictionary of typedef mappings
    
    Returns:
        List of state names
    """
    states = []
    
    for typedef_name, typedef_def in typedefs.items():
        # Check if this typedef contains an enum
        if 'enum' in typedef_def:
            # Extract states from the enum definition
            enum_match = re.search(r'\{([^}]+)\}', typedef_def)
            if enum_match:
                enum_body = enum_match.group(1)
                states.extend(parse_enum_body(enum_body))
    
    return states


# ============================================================================
# UNIQUE/PRIORITY CASE HANDLING
# ============================================================================

def preprocess_unique_priority_cases(verilog_code: str) -> str:
    """
    Preprocess unique case and priority case statements.
    
    SystemVerilog adds 'unique' and 'priority' qualifiers to case statements
    for synthesis and simulation checking. We normalize these to regular cases.
    
    Args:
        verilog_code: Raw SystemVerilog code
    
    Returns:
        Code with unique/priority removed (for standard parser compatibility)
    """
    # Remove 'unique' keyword before case
    code = re.sub(r'\bunique\s+case\b', 'case', verilog_code, flags=re.IGNORECASE)
    
    # Remove 'unique0' keyword
    code = re.sub(r'\bunique0\s+case\b', 'case', code, flags=re.IGNORECASE)
    
    # Remove 'priority' keyword before case
    code = re.sub(r'\bpriority\s+case\b', 'case', code, flags=re.IGNORECASE)
    
    return code


# ============================================================================
# ALWAYS_FF / ALWAYS_COMB NORMALIZATION
# ============================================================================

def normalize_always_blocks(verilog_code: str) -> str:
    """
    Convert SystemVerilog always_ff and always_comb to standard always blocks.
    
    Conversions:
        always_ff @(posedge clk) -> always @(posedge clk)
        always_comb             -> always @(*)
    
    Args:
        verilog_code: Raw SystemVerilog code
    
    Returns:
        Code with normalized always blocks
    """
    # Convert always_ff to always (keep sensitivity list)
    code = re.sub(r'\balways_ff\b', 'always', verilog_code)
    
    # Convert always_comb to always @(*)
    code = re.sub(r'\balways_comb\b', 'always @(*)', code)
    
    # Convert always_latch to always @(*)
    code = re.sub(r'\balways_latch\b', 'always @(*)', code)
    
    return code


# ============================================================================
# LOGIC TYPE HANDLING
# ============================================================================

def normalize_logic_types(verilog_code: str) -> str:
    """
    Convert SystemVerilog 'logic' type to 'reg' for parser compatibility.
    
    Args:
        verilog_code: Raw SystemVerilog code
    
    Returns:
        Code with logic converted to reg
    """
    # Replace 'logic' with 'reg' (maintain wire/reg semantics)
    # This is safe for FSM state registers
    code = re.sub(r'\blogic\b', 'reg', verilog_code)
    
    return code


# ============================================================================
# ============================================================================
# TRANSITION EXTRACTION FROM CASE STATEMENTS
# ============================================================================

def extract_reverse_case_transitions(verilog_code: str, states: List[str]) -> List[Dict]:
    """
    Extract transitions from "reverse case" or "one-hot case" statements.
    
    Common in industrial designs for one-hot encoded FSMs:
        unique case(1'b1)
            state[iIDLE]: begin
                if (condition) nextstate = ACTIVE;
                else nextstate = IDLE;
            end
            state[iACTIVE]: begin
                nextstate = IDLE;
            end
        endcase
    
    Args:
        verilog_code: Original Verilog/SystemVerilog code
        states: List of known state names to match
    
    Returns:
        List of transition dictionaries
    """
    transitions = []
    
    if not states:
        return transitions
    
    # Filter out index states (iSI, iS0, etc.) - keep only actual state names
    # In one-hot encoding, index states start with 'i' and have corresponding states without 'i'
    actual_states = []
    index_to_state = {}
    
    for state in states:
        if state.startswith('i') and len(state) > 1:
            # This might be an index (iSI, iS0, etc.)
            actual_name = state[1:]  # Remove 'i' prefix
            if actual_name in states:
                # It's an index with a corresponding actual state
                index_to_state[state] = actual_name
            else:
                # No corresponding state, treat as actual state
                actual_states.append(state)
        else:
            actual_states.append(state)
    
    # Create pattern for actual state names only
    sorted_states = sorted(actual_states, key=len, reverse=True)
    state_pattern = '|'.join(re.escape(s) for s in sorted_states)
    
    # Find reverse case statements: case(1'b1) or case(1)
    reverse_case_pattern = r'case\s*\(\s*1[\'b]*[01]*\s*\)\s*(.*?)\bendcase\b'
    
    for case_match in re.finditer(reverse_case_pattern, verilog_code, re.DOTALL | re.IGNORECASE):
        case_body = case_match.group(1)
        
        # Pattern for state indexing: state[iSTATE] or state[STATE]
        # Captures the index name and the branch body
        branch_pattern = r'(?:state|nextstate|current_state)\s*\[\s*(\w+)\s*\]\s*:\s*begin\s*(.*?)\s*end'
        
        for branch_match in re.finditer(branch_pattern, case_body, re.DOTALL | re.IGNORECASE):
            state_index = branch_match.group(1).strip()
            branch_body = branch_match.group(2).strip()
            
            # Map index name to actual state name using our index map
            if state_index in index_to_state:
                src_state = index_to_state[state_index]
            elif state_index in actual_states:
                src_state = state_index
            else:
                # Try pattern matching as fallback
                src_state = None
                for state in actual_states:
                    if state_index.lower() in state.lower() or state.lower() in state_index.lower():
                        src_state = state
                        break
            
            if not src_state:
                continue
            
            # Extract assignments to nextstate/next/state
            assign_pattern = rf'(?:nextstate|next_state|next|state)\s*[<]?=\s*({state_pattern})\b'
            
            for assign_match in re.finditer(assign_pattern, branch_body, re.IGNORECASE):
                dst_state = assign_match.group(1).strip()
                
                # Extract condition
                assign_start = assign_match.start()
                text_before = branch_body[:assign_start]
                
                condition = "1"
                
                # Look for if/else if patterns
                if_patterns = [
                    r'else\s+if\s*\(([^)]+)\)\s*$',  # else if (cond)
                    r'if\s*\(([^)]+)\)\s*$',         # if (cond)
                    r'else\s*$'                      # else
                ]
                
                for pattern in if_patterns:
                    if_match = re.search(pattern, text_before, re.IGNORECASE)
                    if if_match:
                        if 'else' in pattern and len(if_match.groups()) == 0:
                            condition = "else"
                        else:
                            condition = if_match.group(1).strip()
                            condition = re.sub(r'\s+', ' ', condition)
                        break
                
                transitions.append({
                    "src": src_state,
                    "dst": dst_state,
                    "condition": condition
                })
    
    return transitions


def extract_sv_transitions(verilog_code: str, states: List[str]) -> List[Dict]:
    """
    Extract FSM transitions directly from case statements using regex.
    
    This handles cases where PyVerilog might not extract transitions properly
    from preprocessed SystemVerilog code. We parse the original code structure.
    
    Args:
        verilog_code: Original Verilog/SystemVerilog code
        states: List of known state names to match
    
    Returns:
        List of transition dictionaries: [{"src": "S1", "dst": "S2", "condition": "..."}]
    """
    transitions = []
    
    if not states:
        return transitions
    
    # Create pattern to match state names (sort by length descending to match longest first)
    sorted_states = sorted(states, key=len, reverse=True)
    state_pattern = '|'.join(re.escape(s) for s in sorted_states)
    
    # First, try to extract from reverse/one-hot case statements
    reverse_transitions = extract_reverse_case_transitions(verilog_code, states)
    if reverse_transitions:
        transitions.extend(reverse_transitions)
    
    # Find standard case statements: case (state_var) ... endcase
    case_pattern = r'case\s*\([^)]+\)\s*(.*?)\bendcase\b'
    
    for case_match in re.finditer(case_pattern, verilog_code, re.DOTALL | re.IGNORECASE):
        case_body = case_match.group(1)
        
        # Skip if this looks like a reverse case (already processed)
        if re.search(r'state\s*\[\s*\w+\s*\]\s*:', case_body):
            continue
        
        # Split case body into individual state branches
        # Each branch is: STATE_NAME: begin ... end
        state_branch_pattern = rf'\b({state_pattern})\s*:\s*begin\s*(.*?)\s*end'
        
        for branch_match in re.finditer(state_branch_pattern, case_body, re.DOTALL | re.IGNORECASE):
            src_state = branch_match.group(1).strip()
            branch_body = branch_match.group(2).strip()
            
            # Extract all assignments in this branch
            # Pattern: next_state = STATE or next_state <= STATE
            assign_pattern = rf'(?:next_state|next|state)\s*[<]?=\s*({state_pattern})\b'
            
            for assign_match in re.finditer(assign_pattern, branch_body, re.IGNORECASE):
                dst_state = assign_match.group(1).strip()
                
                # Try to extract condition by looking backward from assignment
                assign_start = assign_match.start()
                text_before = branch_body[:assign_start]
                
                # Default condition
                condition = "1"
                
                # Look for if/else if patterns - find the most recent if statement
                if_patterns = [
                    r'else\s+if\s*\(([^)]+)\)\s*$',  # else if (cond)
                    r'if\s*\(([^)]+)\)\s*$',         # if (cond)
                    r'else\s*$'                      # else
                ]
                
                for pattern in if_patterns:
                    if_match = re.search(pattern, text_before, re.IGNORECASE)
                    if if_match:
                        if 'else' in pattern and len(if_match.groups()) == 0:
                            condition = "else"
                        else:
                            condition = if_match.group(1).strip()
                            # Clean up condition
                            condition = re.sub(r'\s+', ' ', condition)
                        break
                
                transitions.append({
                    "src": src_state,
                    "dst": dst_state,
                    "condition": condition
                })
        
        # Also check for default case (but don't add as it's not a real state)
        # The default case is handled by the GNN as part of state analysis
        # default_pattern = rf'default\s*:\s*begin\s*(.*?)\s*end'
        # We skip default case transitions as they don't represent actual state nodes
    
    return transitions


# ============================================================================
# MAIN SYSTEMVERILOG PARSER
# ============================================================================

def parse_systemverilog_fsm(filepath: str) -> Dict:
    """
    Parse SystemVerilog FSM file with enhanced enum and typedef support.
    
    This is the main entry point that combines:
    1. SystemVerilog-specific parsing (enums, typedefs)
    2. Standard Verilog parsing (parameters, case statements)
    3. Transition extraction
    4. Reset state detection
    
    Args:
        filepath: Path to SystemVerilog file
    
    Returns:
        Dictionary with structure:
        {
            "module": "fsm_name",
            "states": ["STATE1", "STATE2", ...],
            "transitions": [
                {"src": "STATE1", "dst": "STATE2", "condition": "enable"},
                ...
            ],
            "reset_state": "RESET",
            "state_count": N,
            "transition_count": M
        }
    
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If parsing fails
    """
    # Read the SystemVerilog file
    with open(filepath, 'r') as f:
        sv_code = f.read()
    
    # Store original code for enum parsing
    original_code = sv_code
    
    # Preprocess SystemVerilog-specific constructs
    sv_code = preprocess_unique_priority_cases(sv_code)
    sv_code = normalize_always_blocks(sv_code)
    sv_code = normalize_logic_types(sv_code)
    
    # Write preprocessed code to temp file
    temp_filepath = filepath + '.preprocessed'
    with open(temp_filepath, 'w') as f:
        f.write(sv_code)
    
    try:
        # Parse with standard Verilog parser
        ast = parse_verilog_file(temp_filepath)
        
        # Extract states from parameters/localparams (standard Verilog)
        verilog_states = extract_verilog_states(ast)
        
        # Extract states from SystemVerilog enums (original code)
        enum_states = extract_enum_states(original_code)
        
        # Extract typedef definitions
        typedefs = extract_typedefs(original_code)
        typedef_states = resolve_typedef_states(original_code, typedefs)
        
        # Combine all state sources
        all_states = verilog_states + enum_states + typedef_states
        
        # Remove duplicates while preserving order
        all_states = list(dict.fromkeys(all_states))
        
        # Filter out index states in one-hot encoding (iSI, iS0 when SI, S0 exist)
        # These are used for bit indexing in reverse case statements but aren't actual states
        filtered_states = []
        index_states = set()
        
        for state in all_states:
            if state.startswith('i') and len(state) > 1:
                actual_name = state[1:]
                if actual_name in all_states:
                    # This is an index state (iSI) with corresponding actual state (SI)
                    index_states.add(state)
                    continue
            filtered_states.append(state)
        
        all_states = filtered_states
        
        # Extract transitions from PyVerilog AST
        ast_transitions = extract_verilog_transitions(ast)
        
        # Extract transitions directly from original code (more robust for SV)
        # Pass original unfiltered list for mapping, but filtered states will be used in output
        sv_transitions = extract_sv_transitions(original_code, filtered_states + list(index_states))
        
        # Merge transitions (prefer SV regex extraction if AST found none)
        if len(ast_transitions) > 0:
            transitions = ast_transitions
        else:
            transitions = sv_transitions
        
        # If we have both, combine and deduplicate
        if len(ast_transitions) > 0 and len(sv_transitions) > 0:
            all_transitions = ast_transitions + sv_transitions
            # Deduplicate by (src, dst) pair
            seen = set()
            transitions = []
            for t in all_transitions:
                key = (t['src'], t['dst'])
                if key not in seen:
                    seen.add(key)
                    transitions.append(t)
        
        # Detect reset state
        reset_state = detect_reset_state(ast, all_states)
        
        # Extract module name
        module_name = "unknown"
        if ast and ast.description and ast.description.definitions:
            for item in ast.description.definitions:
                if hasattr(item, 'name'):
                    module_name = item.name
                    break
        
        # Build result dictionary
        result = {
            "module": module_name,
            "states": all_states,
            "transitions": transitions,
            "reset_state": reset_state,
            "state_count": len(all_states),
            "transition_count": len(transitions),
            "systemverilog_features": {
                "enum_states_found": len(enum_states) > 0,
                "typedef_states_found": len(typedef_states) > 0,
                "total_enum_states": len(enum_states),
                "total_typedef_states": len(typedef_states),
                "total_parameter_states": len(verilog_states)
            }
        }
        
        return result
        
    finally:
        # Clean up temp file
        import os
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def is_systemverilog_file(filepath: str) -> bool:
    """
    Check if file contains SystemVerilog constructs.
    
    Args:
        filepath: Path to file
    
    Returns:
        True if SystemVerilog features detected
    """
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for SystemVerilog keywords
    sv_keywords = [
        r'\benum\b',
        r'\btypedef\b',
        r'\blogic\b',
        r'\balways_ff\b',
        r'\balways_comb\b',
        r'\bunique\s+case\b',
        r'\bpriority\s+case\b'
    ]
    
    for pattern in sv_keywords:
        if re.search(pattern, content, re.IGNORECASE):
            return True
    
    return False


def parse_fsm_automatic(filepath: str) -> Dict:
    """
    Automatically detect and parse Verilog or SystemVerilog FSM.
    
    Args:
        filepath: Path to Verilog/SystemVerilog file
    
    Returns:
        Parsed FSM dictionary
    """
    if is_systemverilog_file(filepath):
        print(f"[INFO] Detected SystemVerilog features in {filepath}")
        return parse_systemverilog_fsm(filepath)
    else:
        print(f"[INFO] Parsing as standard Verilog: {filepath}")
        # Use standard Verilog parser
        from parse_verilog_v2 import stage1_pipeline
        # Create a temporary output path that won't conflict
        import tempfile
        import os
        temp_output = os.path.join(tempfile.gettempdir(), "fsm_temp_output.json")
        result = stage1_pipeline(filepath, output_path=temp_output)
        # Clean up temp file
        if os.path.exists(temp_output):
            os.remove(temp_output)
        return result


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_systemverilog.py <input.sv> [output.json]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Parse FSM
        result = parse_fsm_automatic(input_file)
        
        # Print summary
        print("\n" + "="*60)
        print("SystemVerilog FSM Parser - Summary")
        print("="*60)
        print(f"Module: {result['module']}")
        print(f"States: {result['state_count']}")
        print(f"Transitions: {result['transition_count']}")
        print(f"Reset State: {result.get('reset_state', 'Unknown')}")
        
        if 'systemverilog_features' in result:
            sv = result['systemverilog_features']
            print(f"\nSystemVerilog Features:")
            print(f"  - Enum states: {sv['total_enum_states']}")
            print(f"  - Typedef states: {sv['total_typedef_states']}")
            print(f"  - Parameter states: {sv['total_parameter_states']}")
        
        print(f"\nStates: {', '.join(result['states'])}")
        print("="*60)
        
        # Save to JSON if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Saved to {output_file}")
        else:
            # Print JSON to stdout
            print("\nFull JSON output:")
            print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
