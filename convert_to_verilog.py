#!/usr/bin/env python3
"""
Convert SystemVerilog file to standard Verilog
"""

import sys
import re

def convert_sv_to_v(sv_content):
    """Convert SystemVerilog content to Verilog"""
    
    # Replace always_ff with always
    v_content = re.sub(r'always_ff\s*@', 'always @', sv_content)
    
    # Replace always_comb with always @(*)
    v_content = re.sub(r'always_comb\b', 'always @(*)', v_content)
    
    # Remove 'unique' keyword from case statements
    v_content = re.sub(r'unique\s+case', 'case', v_content)
    
    # Replace logic with reg for internal signals
    v_content = re.sub(r'\blogic\b', 'reg', v_content)
    
    # Find outputs that are assigned in always blocks and make them output reg
    # This is a simple heuristic - look for output signals that appear with <= in always blocks
    
    return v_content

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 convert_to_verilog.py input.sv output.v")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    with open(input_file, 'r') as f:
        sv_content = f.read()
    
    v_content = convert_sv_to_v(sv_content)
    
    # Additional fix: outputs assigned in always blocks need to be output reg
    # Find all output statements
    outputs = re.findall(r'output\s+(\w+)', v_content)
    
    # For each output, check if it needs to be output reg
    # Rule: output reg ONLY if assigned in always block AND NOT driven by assign
    for out_signal in outputs:
        # Check if driven by assign statement
        has_assign = bool(re.search(rf'assign\s+{out_signal}\s*=', v_content))
        
        # Check if assigned in always block
        has_always_assign = bool(re.search(rf'always\s+@.*?begin.*?{out_signal}\s*[=<]', v_content, re.DOTALL))
        
        # Only make it output reg if it's in always block and NOT in assign
        if has_always_assign and not has_assign:
            # Replace this output declaration (only if not already 'output reg')
            v_content = re.sub(
                rf'(\boutput\s+)(?!reg\s)({out_signal}\b)',
                r'\1reg \2',
                v_content
            )
    
    with open(output_file, 'w') as f:
        f.write(v_content)
    
    print(f"✓ Converted {input_file} to {output_file}")
    print("  - Replaced always_ff with always @")
    print("  - Replaced always_comb with always @(*)")
    print("  - Removed 'unique' keyword")
    print("  - Replaced logic with reg")
    print(f"  - Fixed output reg declarations")

if __name__ == "__main__":
    main()
