#!/usr/bin/env python3
"""
Complete FSMGuard Pipeline Test
Runs all stages 1-10 on a test input file
"""

import sys
import os
import json

# Add paths
sys.path.insert(0, 'parser')

print("=" * 70)
print("FSMGuard - Complete Pipeline Test")
print("=" * 70)

input_file = "input/test_fsm.v"

# ============================================================================
# STAGE 1: Verilog Parsing
# ============================================================================
print("\n[STAGE 1] Parsing Verilog...")
from parse_verilog_v2 import stage1_pipeline

try:
    stage1_data = stage1_pipeline(input_file, "output/stage1_output.json")
    print(f"  ✅ Stage 1 complete")
    print(f"     States: {len(stage1_data['states'])}")
    print(f"     Transitions: {len(stage1_data['transitions'])}")
except Exception as e:
    print(f"  ❌ Stage 1 failed: {e}")
    sys.exit(1)

# ============================================================================
# STAGE 2-3: Graph Construction & Features
# ============================================================================
print("\n[STAGE 2-3] Building graph and extracting features...")
from fsmguard_pipeline import pipeline_stage2_stage3

try:
    pyg_data = pipeline_stage2_stage3(stage1_data)
    print(f"  ✅ Stages 2-3 complete")
    print(f"     Feature matrix: {pyg_data.x.shape}")
    print(f"     Edges: {pyg_data.edge_index.shape}")
except Exception as e:
    print(f"  ❌ Stages 2-3 failed: {e}")
    sys.exit(1)

# ============================================================================
# STAGE 4: Security Analysis
# ============================================================================
print("\n[STAGE 4] Security vulnerability detection...")
from stage4_security_report import stage4_pipeline

try:
    # Run security analysis
    state_names = stage1_data["states"]
    report = stage4_pipeline(pyg_data, state_names, design_name="test_fsm", 
                            model_path="fsm_gat_best.pth",
                            output_path="output/stage4_report.json")
    
    print(f"  ✅ Stage 4 complete")
    print(f"     Weak states detected: {len(report['flagged_states'])}")
    
    if report['flagged_states']:
        for ws in report['flagged_states']:
            print(f"     - {ws['state_name']}: {ws['cwe']} (risk: {ws['risk_score']:.2f})")
except Exception as e:
    print(f"  ❌ Stage 4 failed: {e}")
    sys.exit(1)

# ============================================================================
# STAGE 5: Subgraph Extraction (Optional)
# ============================================================================
print("\n[STAGE 5] Subgraph extraction...")
from stage5_subgraph import stage5_pipeline

try:
    from fsmguard_pipeline import build_fsm_graph
    G, _ = build_fsm_graph(stage1_data)
    
    # Stage 5 needs state_names (not output_path)
    state_names = stage1_data['states']
    subgraph_data = stage5_pipeline(G, report['flagged_states'], state_names)
    
    print(f"  ✅ Stage 5 complete")
    print(f"     Subgraphs extracted: {len(subgraph_data)}")
except Exception as e:
    print(f"  ⚠️  Stage 5 skipped: {e}")

# ============================================================================
# STAGE 6-7: RL Agent Decision (Using trained PPO agent)
# ============================================================================
print("\n[STAGE 6-7] RL agent selecting fixes...")

from stable_baselines3 import PPO
from fsm_env import FSMGuardEnv
import os

fix_specs = []
flagged_states = report.get('flagged_states', [])

if flagged_states:
    model_path = "models/fsm_ppo_best.zip"
    
    if os.path.exists(model_path):
        print(f"  ✅ Loading trained agent: {model_path}")
        
        try:
            # Load trained model
            model = PPO.load(model_path)
            
            categories = ["Guard Insertion", "Transition Pruning", "State Re-encoding", "Deadlock Trap"]
            parameters = [
                ["auth_signal", "lock_signal", "priv_check"],
                ["full_removal", "redirect", "safe_redirect"],
                ["hamming", "parity", "both"],
                ["alert", "lockdown", "both"]
            ]
            strictness_names = ["soft", "strict"]
            
            # Get fix for EACH weak state
            print(f"  🔄 Processing {len(flagged_states)} weak states...")
            for idx, weak_state in enumerate(flagged_states, 1):
                # Create environment for this specific state
                env = FSMGuardEnv([weak_state])
                obs, _ = env.reset()
                
                # Get agent's fix decision for this state
                action, _ = model.predict(obs, deterministic=True)
                
                cat = int(action[0])
                par = int(action[1])
                strt = int(action[2])
                
                fix_spec = {
                    "state_name": weak_state['state_name'],
                    "category": cat,
                    "parameter": par,
                    "strictness": strt,
                    "cwe": weak_state['cwe'],
                    "risk_score": weak_state['risk_score'],
                    "fallback": stage1_data['states'][0],
                    "fix_detail": {
                        "category": categories[cat],
                        "parameter": parameters[cat][par],
                        "strictness": strictness_names[strt]
                    }
                }
                fix_specs.append(fix_spec)
                
                print(f"  ✅ [{idx}/{len(flagged_states)}] {weak_state['state_name']}: {categories[cat]} + {parameters[cat][par]} ({strictness_names[strt]})")
            
            print(f"  ✅ Agent selected fixes for ALL {len(flagged_states)} weak states")
            
        except Exception as e:
            print(f"  ❌ Agent failed: {e}")
            import traceback
            traceback.print_exc()
            print("     Falling back to mock fix...")
            weak_state = flagged_states[0]
            fix_specs = [{
                "state_name": weak_state['state_name'],
                "category": 0,
                "parameter": 0,
                "strictness": 1,
                "cwe": weak_state['cwe'],
                "risk_score": weak_state['risk_score'],
                "fallback": stage1_data['states'][0],
                "fix_detail": {
                    "category": "Guard Insertion",
                    "parameter": "auth_signal",
                    "strictness": "strict"
                }
            }]
    else:
        print(f"  ⚠️  Trained model not found: {model_path}")
        print("     Using mock fix instead...")
        weak_state = flagged_states[0]
        fix_specs = [{
            "state_name": weak_state['state_name'],
            "category": 0,
            "parameter": 0,
            "strictness": 1,
            "cwe": weak_state['cwe'],
            "risk_score": weak_state['risk_score'],
            "fallback": stage1_data['states'][0],
            "fix_detail": {
                "category": "Guard Insertion",
                "parameter": "auth_signal",
                "strictness": "strict"
            }
        }]
else:
    print("  ⚠️  No vulnerabilities found, skipping fix generation")
    fix_specs = []

# ============================================================================
# STAGE 8: Patch Generation
# ============================================================================
if fix_specs:
    print(f"\n[STAGE 8] Generating security patches for {len(fix_specs)} vulnerabilities...")
    from patch_gen import stage8_pipeline
    import json
    
    stage8_reports = []  # Collect all fix reports
    
    try:
        # Apply ALL fixes sequentially
        current_file = input_file
        
        for idx, fix_spec in enumerate(fix_specs, 1):
            print(f"  🔄 [{idx}/{len(fix_specs)}] Applying fix for {fix_spec['state_name']}...")
            
            # Apply fix (each iteration works on the previously patched file)
            patch_files = stage8_pipeline(current_file, fix_spec, output_dir="output")
            
            # Read the generated report and add to our collection
            with open("output/stage8_report.json", 'r') as f:
                fix_report = json.load(f)
                stage8_reports.append(fix_report)
            
            # Update current file to the patched version for next iteration
            current_file = "output/patched_fsm.v"
            
            print(f"  ✅ [{idx}/{len(fix_specs)}] {fix_spec['state_name']}: {fix_spec['fix_detail']['category']} applied")
        
        # Save combined report with all fixes
        combined_stage8 = {
            "fixes_applied": len(stage8_reports),
            "all_fixes": stage8_reports,
            "original_file": input_file,
            "patched_file": "output/patched_fsm.v"
        }
        with open("output/stage8_report.json", 'w') as f:
            json.dump(combined_stage8, f, indent=2)
        
        print(f"  ✅ Stage 8 complete - Applied {len(fix_specs)} fixes to design")
    except Exception as e:
        print(f"  ❌ Stage 8 failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================================================
# STAGE 9: Verification
# ============================================================================
    print("\n[STAGE 9] Verifying patched design...")
    from verify import stage9_pipeline
    
    try:
        verify_result = stage9_pipeline("output/patched_fsm.v", "output/stage8_report.json")
        print(f"  ✅ Stage 9 complete")
        print(f"     Overall: {verify_result['overall']}")
    except Exception as e:
        print(f"  ❌ Stage 9 failed: {e}")
        sys.exit(1)

# ============================================================================
# STAGE 10: Final Report
# ============================================================================
    print("\n[STAGE 10] Generating final report...")
    from report_gen import stage10_pipeline
    
    try:
        final_report = stage10_pipeline()
        print(f"  ✅ Stage 10 complete")
        print(f"     Design safe: {final_report['summary']['design_safe']}")
    except Exception as e:
        print(f"  ❌ Stage 10 failed: {e}")
        sys.exit(1)

print("\n" + "=" * 70)
print("PIPELINE TEST COMPLETE!")
print("=" * 70)
print(f"\nInput:  {input_file}")
print(f"Output: output/patched_fsm.v")
print(f"Report: output/fsm_report.txt")
print("=" * 70)
