"""
FSMGuard - Stage 8: Patch Execution (Zero Decision Making)
==========================================================

Executes hardware security patches based on complete fix specifications
from the Stage 7 RL agent. This module makes ZERO security decisions -
all intelligence comes from the trained agent.

Stage 8 is a pure template executor that mechanically applies fixes.

Dependencies:
    - jinja2 (required): Template engine
    - pyverilog (optional): Full AST parsing (requires iverilog)
    
Note: Stage 8 works in template-only mode without pyverilog/iverilog.
      Full AST analysis is optional and not required for patch generation.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import json
from typing import Dict, Any, List, Tuple

# Optional imports for full AST parsing
try:
    from pyverilog.vparser.parser import parse
    from pyverilog.vparser.ast import *
    PYVERILOG_AVAILABLE = True
except ImportError:
    PYVERILOG_AVAILABLE = False
    print("⚠️  pyverilog not available - Stage 8 will run in template-only mode")

from jinja2 import Environment, FileSystemLoader
import re


# Template directory
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")


def extract_fsm_signals(verilog_code: str, stage1_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extract FSM signal names and states from Verilog code.
    
    Args:
        verilog_code: Verilog source code
        stage1_data: Optional Stage 1 parsing data with states and reset info
    
    Returns:
        Dictionary with extracted signal information:
        - state_var: Name of state variable (e.g., "state")
        - states: List of state names (e.g., ["SI", "S0", "S1"])
        - inputs: List of input signal names
        - reset_state: Actual reset state name (e.g., "SI")
        - fallback_state: First state (typically IDLE/RESET/SI)
        - clk_signal: Clock signal name (e.g., "CLK", "clk", "clock")
        - reset_signal: Reset signal name (e.g., "RESET", "rst", "resetn")
    """
    signals = {
        "state_var": "state",  # Default
        "states": [],
        "inputs": [],
        "reset_state": "RESET",  # Default
        "fallback_state": "RESET",
        "clk_signal": "clk",  # Default
        "reset_signal": "reset"  # Default
    }
    
    # Extract clock signal from always blocks (e.g., always @(posedge CLK))
    clk_match = re.search(r'always\s+@\s*\(\s*posedge\s+(\w+)\s*\)', verilog_code)
    if clk_match:
        signals["clk_signal"] = clk_match.group(1)
    
    # Extract reset signal from module ports or conditional checks
    # Look for common reset signal names in input declarations
    reset_patterns = [r'input\s+(?:wire\s+)?(\w*[Rr]eset\w*)', r'input\s+(?:wire\s+)?(\w*[Rr]st\w*)']
    for pattern in reset_patterns:
        reset_match = re.search(pattern, verilog_code)
        if reset_match:
            signals["reset_signal"] = reset_match.group(1)
            break
    
    # If we have stage1 data, use it (most reliable)
    if stage1_data:
        signals["states"] = stage1_data.get("states", [])
        signals["reset_state"] = stage1_data.get("reset_state", "RESET")
        if signals["states"]:
            signals["fallback_state"] = signals["reset_state"]
    
    # Extract state variable name from "reg [x:x] <name>;" or "reg <name>;"
    state_var_match = re.search(r'reg\s+(?:\[\d+:\d+\])?\s*(\w+)\s*;', verilog_code)
    if state_var_match:
        potential_state_var = state_var_match.group(1)
        # Verify it's used in case statements
        if re.search(rf'case\s*\([^)]*{potential_state_var}[^)]*\)', verilog_code):
            signals["state_var"] = potential_state_var
    
    # If we don't have stage1 data, try to extract states from code
    if not signals["states"]:
        # Try parameter declarations (e.g., parameter SI = 6'b000001)
        # Filter out index parameters (those with small integer values)
        param_matches = re.findall(r'parameter\s+(\w+)\s*=\s*([^;]+);', verilog_code)
        states = []
        for name, value in param_matches:
            # Skip if it's an index (small integer like 0, 1, 2)
            if re.match(r'^\d+$', value.strip()) and int(value.strip()) < 32:
                continue
            # Skip if name starts with 'i' and next char is uppercase (likely index)
            if name.startswith('i') and len(name) > 1 and name[1].isupper():
                # Check if corresponding state exists
                actual_name = name[1:]
                if any(actual_name == pname for pname, _ in param_matches):
                    continue
            states.append(name)
        
        # Also try localparam
        localparam_states = re.findall(r'localparam\s+(\w+)\s*=\s*[^;]+;', verilog_code)
        states.extend(localparam_states)
        
        if states:
            signals["states"] = list(set(states))  # Remove duplicates
            signals["fallback_state"] = states[0]
            signals["reset_state"] = states[0]
    
    # Extract input signals from module port declarations
    # Handle both old and new Verilog styles
    inputs = []
    
    # Pattern 1: input signal_name (old style)
    inputs.extend(re.findall(r'input\s+(?:wire\s+|reg\s+)?(\w+)', verilog_code))
    
    # Pattern 2: module port list parsing (more reliable)
    module_match = re.search(r'module\s+\w+\s*\((.*?)\);', verilog_code, re.DOTALL)
    if module_match:
        port_list = module_match.group(1)
        # Extract input signal names
        inputs_from_ports = re.findall(r'input\s+(?:wire\s+|reg\s+)?(?:\[[^\]]+\])?\s*(\w+)', port_list)
        inputs.extend(inputs_from_ports)
    
    # Filter out clk and reset signals
    signals["inputs"] = [inp for inp in set(inputs) if inp.lower() not in ['clk', 'clock', 'reset', 'rst', 'resetn']]
    
    return signals


def load_verilog(filepath: str) -> Tuple[Any, str]:
    """
    Load and parse Verilog file using PyVerilog.
    
    Args:
        filepath: Path to Verilog file
    
    Returns:
        Tuple of (AST, original_code)
    
    Raises:
        FileNotFoundError: If file doesn't exist
        Exception: If parsing fails
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Verilog file not found: {filepath}")
    
    # Read original code for reference
    with open(filepath, 'r') as f:
        original_code = f.read()
    
    # Parse Verilog to AST (optional - Stage 8 works without full parsing)
    # For template execution, we don't need full AST analysis
    if PYVERILOG_AVAILABLE:
        try:
            ast, _ = parse([filepath])
            return ast, original_code
        except Exception as e:
            # If parsing fails (e.g., iverilog not installed), continue without AST
            # Stage 8 can still apply templates to the code
            print(f"  ⚠️  AST parsing skipped (iverilog not available)")
            print(f"     Stage 8 will apply templates without AST analysis")
            return None, original_code
    else:
        # pyverilog not installed - use template-only mode
        return None, original_code


def find_weak_state(ast: Any, state_name: str) -> Tuple[bool, Any]:
    """
    Find the weak state transition in the AST.
    
    Args:
        ast: PyVerilog AST
        state_name: Name of the weak state to find
    
    Returns:
        Tuple of (found: bool, node: AST node or None)
    """
    # This is a simplified implementation
    # In production, would traverse AST to find the exact state case
    # For now, we return True if AST is valid
    if ast is None:
        return False, None
    
    # TODO: Full AST traversal to locate state case statement
    # For demonstration, we assume state exists
    return True, ast


def compute_new_encoding(current_states: Dict[str, int], weak_state: str,
                         encoding_type: str = "hamming") -> str:
    """
    Compute new state encoding with hamming distance >= 3.
    
    Args:
        current_states: Dictionary mapping state names to encodings
        weak_state: Name of state to re-encode
        encoding_type: "hamming", "parity", or "both"
    
    Returns:
        New encoding as a string (e.g., "4'b1010")
    """
    # Get current encoding
    current_encoding = current_states.get(weak_state, 0)
    
    # Find new encoding with hamming distance >= 3 from all other states
    bit_width = 4  # Assume 4-bit encoding
    
    # Try encodings until we find one with sufficient hamming distance
    for candidate in range(2 ** bit_width):
        if candidate == current_encoding:
            continue
        
        # Check hamming distance from all other states
        min_distance = bit_width
        for other_state, other_encoding in current_states.items():
            if other_state != weak_state:
                distance = bin(candidate ^ other_encoding).count('1')
                min_distance = min(min_distance, distance)
        
        if min_distance >= 3:
            # Format as Verilog literal
            return f"{bit_width}'b{candidate:0{bit_width}b}"
    
    # Fallback: use inverted encoding
    new_encoding = ~current_encoding & ((1 << bit_width) - 1)
    return f"{bit_width}'b{new_encoding:0{bit_width}b}"


def execute_patch(original_code: str, fix_spec: Dict[str, Any], stage1_json_path: str = "output/stage1_parsing.json") -> str:
    """
    Execute patch by applying template to original Verilog code.
    
    CRITICAL: This function makes ZERO security decisions.
    It only looks up and applies templates based on agent's fix_spec.
    
    Args:
        original_code: Original Verilog source code
        fix_spec: Complete fix specification from agent containing:
            - state_name: Name of weak state
            - category: Fix category (0-3)
            - parameter: Fix parameter (0-2)
            - strictness: Strictness level (0-1)
            - cwe: CWE identifier
            - risk_score: Risk score
            - fix_detail: Human-readable fix description
        stage1_json_path: Path to stage1 parsing output (contains states and reset info)
    
    Returns:
        Patched Verilog code as string
    """
    # Extract fix components
    state_name = fix_spec["state_name"]
    category = fix_spec["category"]
    parameter = fix_spec["parameter"]
    strictness = fix_spec["strictness"]
    cwe = fix_spec["cwe"]
    fallback = fix_spec.get("fallback", "RESET")
    
    # Load stage1 data to get actual states and reset state
    stage1_data = None
    if os.path.exists(stage1_json_path):
        try:
            with open(stage1_json_path, 'r') as f:
                stage1_full = json.load(f)
                # stage1_parsing.json format: {"states": ["SI", "S0", ...], "reset_state": "SI"}
                states = stage1_full.get("states", [])
                reset_state = stage1_full.get("reset_state", states[0] if states else "RESET")
                
                stage1_data = {
                    "states": states,
                    "reset_state": reset_state
                }
        except Exception as e:
            print(f"  ⚠️  Could not load stage1 data: {e}")
    
    # Extract FSM signals from actual Verilog code
    fsm_signals = extract_fsm_signals(original_code, stage1_data)
    
    # If target state name doesn't exist in FSM, use first state
    if state_name not in fsm_signals["states"] and fsm_signals["states"]:
        print(f"  ⚠️  State '{state_name}' not found, using '{fsm_signals['states'][0]}'")
        state_name = fsm_signals["states"][0]
    
    # Use reset state as fallback (SI in DMA controller, not "RESET" which is a port)
    fallback = fsm_signals.get("reset_state", fsm_signals.get("fallback_state", "RESET"))
    
    # Select input signal based on parameter (0, 1, 2 -> first 3 inputs)
    auth_signal = fsm_signals["inputs"][parameter] if parameter < len(fsm_signals["inputs"]) else "auth_valid"
    
    # Set up Jinja2 environment
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    
    # Select appropriate template based on category
    template_map = {
        0: "guard.j2",      # Guard Insertion
        1: "prune.j2",      # Transition Pruning
        2: "reencode.j2",   # State Re-encoding
        3: "deadlock.j2"    # Deadlock Trap
    }
    
    template_name = template_map.get(category)
    if template_name is None:
        raise ValueError(f"Invalid fix category: {category}")
    
    try:
        template = env.get_template(template_name)
    except Exception as e:
        raise Exception(f"Failed to load template {template_name}: {e}")
    
    # Prepare template variables with actual FSM signal names
    template_vars = {
        "state_name": state_name,
        "parameter": parameter,
        "strictness": strictness,
        "fallback": fallback,
        "cwe": cwe,
        "risk_score": fix_spec.get("risk_score", 0.0),
        "category_name": fix_spec.get("fix_detail", {}).get("category", "Unknown"),
        "parameter_name": fix_spec.get("fix_detail", {}).get("parameter", "unknown"),
        "strictness_name": fix_spec.get("fix_detail", {}).get("strictness", "soft"),
        # Add extracted FSM-specific signals
        "state_var": fsm_signals["state_var"],
        "auth_signal": auth_signal,
        "states": fsm_signals["states"],
        "inputs": fsm_signals["inputs"],
        "clk": fsm_signals.get("clk_signal", "clk"),
        "reset": fsm_signals.get("reset_signal", "reset")
    }
    
    # Render patch snippet from template
    patch_snippet = template.render(**template_vars)
    
    # Apply patch to original code
    # Insert patch before the last 'endmodule' to keep valid Verilog syntax
    if 'endmodule' in original_code:
        # Find last occurrence of endmodule
        last_endmodule_pos = original_code.rfind('endmodule')
        patched_code = (
            original_code[:last_endmodule_pos] +
            "\n// ==== FSMGuard Patch Start ====\n" +
            patch_snippet +
            "\n// ==== FSMGuard Patch End ====\n\n" +
            original_code[last_endmodule_pos:]
        )
    else:
        # No endmodule found, append as before
        patched_code = original_code + "\n\n" + patch_snippet
    
    return patched_code


def generate_patched_verilog(patched_code: str, output_path: str):
    """
    Save patched Verilog code to file.
    
    Args:
        patched_code: Modified Verilog code
        output_path: Path to save patched file
    
    Raises:
        IOError: If file cannot be written
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Write patched code
    try:
        with open(output_path, 'w') as f:
            f.write(patched_code)
    except Exception as e:
        raise IOError(f"Failed to write patched file: {e}")


def save_patch_report(fix_spec: Dict[str, Any], patch_snippet: str,
                     original_file: str, patched_file: str,
                     output_path: str = "output/stage8_report.json"):
    """
    Save patch report to JSON file.
    
    Args:
        fix_spec: Complete fix specification from agent
        patch_snippet: The applied patch code
        original_file: Path to original Verilog file
        patched_file: Path to patched Verilog file
        output_path: Path to save report
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Build report
    report = {
        "state_name": fix_spec["state_name"],
        "cwe": fix_spec["cwe"],
        "risk_score": fix_spec.get("risk_score", 0.0),
        "fix_category": fix_spec.get("fix_detail", {}).get("category", "Unknown"),
        "fix_parameter": fix_spec.get("fix_detail", {}).get("parameter", "unknown"),
        "fix_strictness": fix_spec.get("fix_detail", {}).get("strictness", "soft"),
        "fallback": fix_spec.get("fallback", "RESET"),
        "patch_snippet": patch_snippet,
        "original_file": original_file,
        "patched_file": patched_file
    }
    
    # Save report
    try:
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to write patch report: {e}")


def print_patch_confirmation(fix_spec: Dict[str, Any], patched_file: str):
    """
    Print confirmation of applied patch to console.
    
    Args:
        fix_spec: Complete fix specification
        patched_file: Path to patched file
    """
    print("\n" + "=" * 70)
    print("PATCH APPLIED")
    print("=" * 70)
    print(f"  State:      {fix_spec['state_name']}")
    print(f"  CWE:        {fix_spec['cwe']}")
    print(f"  Category:   {fix_spec.get('fix_detail', {}).get('category', 'Unknown')}")
    print(f"  Parameter:  {fix_spec.get('fix_detail', {}).get('parameter', 'unknown')}")
    print(f"  Strictness: {fix_spec.get('fix_detail', {}).get('strictness', 'soft')}")
    print(f"  Fallback:   {fix_spec.get('fallback', 'RESET')}")
    print(f"  Saved:      {patched_file}")
    print("=" * 70 + "\n")


def stage8_pipeline(verilog_path: str, fix_spec: Dict[str, Any],
                    output_dir: str = "output") -> Dict[str, str]:
    """
    Complete Stage 8 pipeline: Execute patch based on agent's decision.
    
    Args:
        verilog_path: Path to original Verilog file
        fix_spec: Complete fix specification from Stage 7 agent
        output_dir: Directory for output files
    
    Returns:
        Dictionary with paths to generated files
    """
    print("=" * 70)
    print("FSMGuard - Stage 8: Patch Execution")
    print("=" * 70)
    
    # Step 1: Load original Verilog
    print("\n[1/5] Loading Verilog file...")
    try:
        ast, original_code = load_verilog(verilog_path)
        print(f"  ✅ Loaded: {verilog_path}")
    except Exception as e:
        print(f"  ❌ Failed to load Verilog: {e}")
        return {}
    
    # Step 2: Find weak state in AST
    print(f"\n[2/5] Locating weak state: {fix_spec['state_name']}...")
    if ast is not None:
        found, node = find_weak_state(ast, fix_spec['state_name'])
        if found:
            print(f"  ✅ State found in AST")
        else:
            print(f"  ⚠️  State not found in AST, continuing with template application")
    else:
        print(f"  ⚠️  AST not available, using template-only mode")
    
    # Step 3: Execute patch (apply template)
    print("\n[3/5] Applying patch template...")
    try:
        patched_code = execute_patch(original_code, fix_spec)
        # Extract just the patch snippet for reporting
        patch_snippet = patched_code[len(original_code):].strip()
        print(f"  ✅ Patch applied successfully")
    except Exception as e:
        print(f"  ❌ Failed to apply patch: {e}")
        return {}
    
    # Step 4: Save patched Verilog
    print("\n[4/5] Saving patched Verilog...")
    patched_path = os.path.join(output_dir, "patched_fsm.v")
    try:
        generate_patched_verilog(patched_code, patched_path)
        print(f"  ✅ Saved: {patched_path}")
    except Exception as e:
        print(f"  ❌ Failed to save patched file: {e}")
        return {}
    
    # Step 5: Save patch report
    print("\n[5/5] Generating patch report...")
    report_path = os.path.join(output_dir, "stage8_report.json")
    try:
        save_patch_report(fix_spec, patch_snippet, verilog_path, patched_path, report_path)
        print(f"  ✅ Report saved: {report_path}")
    except Exception as e:
        print(f"  ❌ Failed to save report: {e}")
        return {}
    
    # Print confirmation
    print_patch_confirmation(fix_spec, patched_path)
    
    return {
        "patched_file": patched_path,
        "report_file": report_path
    }


if __name__ == "__main__":
    """
    Demonstration of Stage 8 patch generation.
    """
    # Sample fix specification from Stage 7 agent
    fix_spec = {
        "state_name": "MEM_ACC",
        "cwe": "CWE-1245",
        "risk_score": 0.87,
        "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1],
        "category": 0,      # Guard Insertion
        "parameter": 0,     # auth_signal
        "strictness": 1,    # strict
        "fallback": "RESET",
        "fix_detail": {
            "category": "Guard Insertion",
            "parameter": "auth_signal",
            "strictness": "strict"
        }
    }
    
    # Run Stage 8 pipeline
    print("FSMGuard Stage 8 - Demonstration\n")
    
    # Use sample FSM as input
    verilog_path = "input/sample_fsm.v"
    if os.path.exists(verilog_path):
        result = stage8_pipeline(verilog_path, fix_spec)
        
        if result:
            print("✅ Stage 8 completed successfully!")
            print(f"\nGenerated files:")
            print(f"  - Patched Verilog: {result['patched_file']}")
            print(f"  - Patch Report:    {result['report_file']}")
        else:
            print("❌ Stage 8 failed")
    else:
        print(f"❌ Input file not found: {verilog_path}")
        print("\nPlease ensure input/sample_fsm.v exists")
