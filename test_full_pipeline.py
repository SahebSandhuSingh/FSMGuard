#!/usr/bin/env python3
"""
FSMGuard - Complete Pipeline Test (Stage 1 → 2 → 3)
==================================================
Tests the integration of all stages end-to-end.
"""

import sys
sys.path.insert(0, 'parser')

from parse_verilog import stage1_pipeline
import json

# Import Stage 2 & 3
sys.path.insert(0, '..')
from fsmguard_pipeline import pipeline_stage2_stage3

print("=" * 70)
print("FSMGuard - Complete Pipeline Test")
print("=" * 70)

# Stage 1: Extract FSM from Verilog
print("\n[STAGE 1] Extracting FSM from Verilog...")
fsm_data = stage1_pipeline("input/sample_fsm.v")

print("\nStage 1 Output:")
print(json.dumps(fsm_data, indent=2))

# Stage 2 & 3: Build graph and generate features
print("\n[STAGE 2 & 3] Building graph and extracting features...")
data = pipeline_stage2_stage3(fsm_data)

print(f"\n✓ Complete Pipeline Success!")
print(f"  - States: {len(fsm_data['states'])}")
print(f"  - Transitions: {len(fsm_data['transitions'])}")
print(f"  - Feature Matrix: {data.x.shape}")
print(f"  - Edge Index: {data.edge_index.shape}")

print("\n" + "=" * 70)
print("All stages completed successfully!")
print("=" * 70)
