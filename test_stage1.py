#!/usr/bin/env python3
"""Quick test for Stage 1"""

import sys
sys.path.insert(0, 'parser')

from parse_verilog import stage1_pipeline
import json

# Test Stage 1
fsm_data = stage1_pipeline("input/sample_fsm.v")

print("\n" + "="*70)
print("FINAL OUTPUT")
print("="*70)
print(json.dumps(fsm_data, indent=2))
