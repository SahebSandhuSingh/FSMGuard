#!/usr/bin/env python3
"""
FSMGuard - Run Stages 5-10 Pipeline
====================================
Runs the complete patching and verification pipeline on detected vulnerabilities.
"""

import json
import os
import sys
import networkx as nx
import numpy as np

# Import all stage modules
from stage5_subgraph import stage5_pipeline
from patch_gen import stage8_pipeline
from verify import stage9_pipeline

# Try to import RL components
try:
    from stable_baselines3 import PPO
    from fsm_env import FSMGuardEnv, CATEGORY_NAMES, PARAMETER_NAMES, STRICTNESS_NAMES
    RL_AVAILABLE = True
except ImportError:
    RL_AVAILABLE = False

# Try to import stage 6 (optional)
try:
    from demo_env import run_demo as run_stage6_demo
    STAGE6_AVAILABLE = True
except ImportError:
    STAGE6_AVAILABLE = False

# Try to import stage 10 (optional)
try:
    from report_gen import stage10_pipeline
    STAGE10_AVAILABLE = True
except ImportError:
    STAGE10_AVAILABLE = False


def load_stage1_data():
    """Load Stage 1 parsing output."""
    path = "output/stage1_parsing.json"
    if not os.path.exists(path):
        print(f"❌ Error: {path} not found. Run Stage 1-4 first.")
        sys.exit(1)
    
    with open(path, 'r') as f:
        return json.load(f)


def load_stage4_data():
    """Load Stage 4 detection output."""
    path = "output/stage4_report.json"
    if not os.path.exists(path):
        print(f"❌ Error: {path} not found. Run Stage 1-4 first.")
        sys.exit(1)
    
    with open(path, 'r') as f:
        return json.load(f)


def rebuild_graph(stage1_data):
    """Rebuild NetworkX graph from Stage 1 data."""
    G = nx.DiGraph()
    
    # Add nodes
    states = stage1_data["states"]
    for state in states:
        G.add_node(state)
    
    # Add edges
    transitions = stage1_data.get("transitions", [])
    for trans in transitions:
        src = trans["src"]
        dst = trans["dst"]
        condition = trans.get("condition", "")
        G.add_edge(src, dst, condition=condition)
    
    return G


def run_stage5(stage1_data, stage4_data):
    """Run Stage 5: Subgraph Isolation."""
    print("\n" + "="*70)
    print("STAGE 5: SUBGRAPH ISOLATION")
    print("="*70)
    
    # Rebuild graph
    G = rebuild_graph(stage1_data)
    state_names = stage1_data["states"]
    
    # Get flagged states from stage 4
    flagged_states = stage4_data.get("flagged_states", stage4_data.get("weak_states", []))
    
    if not flagged_states:
        print("⚠️  No weak states found. Skipping stages 5-10.")
        return None
    
    print(f"\nIsolating {len(flagged_states)} weak states...")
    
    # Run stage 5
    isolated = stage5_pipeline(G, flagged_states, state_names)
    
    print(f"✓ Isolated {len(isolated)} subgraphs")
    print(f"✓ Output saved to: output/stage5_output.json")
    
    return isolated


def run_stage6():
    """Run Stage 6: RL Environment Demo."""
    print("\n" + "="*70)
    print("STAGE 6: RL ENVIRONMENT (Demo)")
    print("="*70)
    
    if not STAGE6_AVAILABLE:
        print("\n⚠️  Stage 6 not available (import error)")
        print("  Skipping to Stage 7...")
        return
    
    # Check if stage5 output exists
    if not os.path.exists("output/stage5_output.json"):
        print("⚠️  Stage 5 output not found. Skipping Stage 6.")
        return
    
    print("\nRunning RL environment demo...")
    print("(Full RL training is in Stage 7)\n")
    
    # Run demo
    try:
        run_stage6_demo()
        print("\n✓ Stage 6 demo complete")
    except Exception as e:
        print(f"⚠️  Stage 6 demo error: {e}")


def run_stage7():
    """Run Stage 7: RL Agent (check if model exists)."""
    print("\n" + "="*70)
    print("STAGE 7: RL AGENT")
    print("="*70)
    
    model_path = "models/fsm_ppo_best.zip"
    
    if os.path.exists(model_path):
        print(f"\n✓ Trained agent found: {model_path}")
        print(f"  Model size: {os.path.getsize(model_path) / 1024:.1f} KB")
        print("  (Use train_agent.py to retrain or evaluate_agent.py to test)")
    else:
        print(f"\n⚠️  No trained agent found at {model_path}")
        print("  Run: python3 train_agent.py --episodes 1000")
        print("  (Skipping to Stage 8 with default fixes)")


def run_stage8(stage5_data, input_file):
    """Run Stage 8: Patch Generation."""
    print("\n" + "="*70)
    print("STAGE 8: PATCH GENERATION")
    print("="*70)
    
    if not stage5_data:
        print("⚠️  No stage 5 data. Skipping Stage 8.")
        return False
    
    print(f"\nGenerating patches for {len(stage5_data)} weak states...")
    
    # Try to load trained RL agent
    agent = None
    model_path = "models/fsm_ppo_best.zip"
    
    if RL_AVAILABLE and os.path.exists(model_path):
        try:
            agent = PPO.load(model_path)
            print(f"✓ Using trained RL agent: {model_path}")
        except Exception as e:
            print(f"⚠️  Failed to load agent: {e}")
            print("  Falling back to heuristic rules")
    else:
        if not RL_AVAILABLE:
            print("⚠️  RL libraries not available, using heuristic rules")
        else:
            print(f"⚠️  Trained agent not found at {model_path}, using heuristic rules")
    
    # Generate patches for each weak state
    patches_applied = []
    all_patch_details = []
    for i, weak_state in enumerate(stage5_data, 1):  # Patch ALL vulnerable states
        state_name = weak_state["state_name"]
        cwe = weak_state.get("cwe", "CWE-1245")
        risk_score = weak_state.get("risk_score", 0.5)
        
        print(f"\n[{i}/{len(stage5_data)}] Patching state: {state_name}")
        
        # Get action from trained agent or use heuristics
        if agent is not None:
            try:
                # Create environment for this weak state
                env = FSMGuardEnv([weak_state])
                obs, _ = env.reset()
                
                # Get agent's prediction
                action, _ = agent.predict(obs, deterministic=True)
                category, parameter, strictness = int(action[0]), int(action[1]), int(action[2])
                
                print(f"  🤖 AI Agent Decision:")
                print(f"     Category: {CATEGORY_NAMES[category]}")
                print(f"     Parameter: {PARAMETER_NAMES[category][parameter]}")
                print(f"     Strictness: {STRICTNESS_NAMES[strictness]}")
                
            except Exception as e:
                print(f"  ⚠️  Agent prediction failed: {e}")
                print(f"     Using heuristic fallback")
                # Fallback to heuristics
                if "1245" in cwe:
                    category, parameter, strictness = 0, 2, 1
                elif "1280" in cwe:
                    category, parameter, strictness = 3, 2, 1
                else:
                    category, parameter, strictness = 0, 0, 1
        else:
            # Use heuristic rules
            if "1245" in cwe:
                category, parameter, strictness = 0, 2, 1  # Guard Insertion + privilege_check + strict
            elif "1280" in cwe:
                category, parameter, strictness = 3, 2, 1  # Deadlock Trap + both + strict
            else:
                category, parameter, strictness = 0, 0, 1  # Default: Guard + auth_signal + strict
            
            print(f"  📋 Heuristic Rule Applied:")
            print(f"     Category: {CATEGORY_NAMES[category]}")
            print(f"     Parameter: {PARAMETER_NAMES[category][parameter]}")
            print(f"     Strictness: {STRICTNESS_NAMES[strictness]}")
        
        # Create fix specification
        fix_spec = {
            "state_name": state_name,
            "category": category,
            "parameter": parameter,
            "strictness": strictness,
            "fallback": "RESET",
            "cwe": cwe,
            "risk_score": risk_score,
            "fix_detail": {
                "category": CATEGORY_NAMES[category],
                "parameter": PARAMETER_NAMES[category][parameter],
                "strictness": STRICTNESS_NAMES[strictness]
            }
        }
        
        try:
            result = stage8_pipeline(
                input_file,
                fix_spec,
                output_dir="output"
            )
            
            if result and "patched_file" in result:
                print(f"  ✓ Patch applied successfully")
                patches_applied.append(state_name)
                # Store patch details for final report
                all_patch_details.append({
                    "state_name": state_name,
                    "cwe": cwe,
                    "risk_score": risk_score,
                    "fix_category": CATEGORY_NAMES[category],
                    "fix_parameter": PARAMETER_NAMES[category][parameter],
                    "fix_strictness": STRICTNESS_NAMES[strictness]
                })
            else:
                print(f"  ⚠️  Patch failed")
        
        except Exception as e:
            print(f"  ⚠️  Error: {e}")
    
    # Save comprehensive patch report
    if all_patch_details:
        comprehensive_report = {
            "patches_applied": len(all_patch_details),
            "total_vulnerabilities": len(stage5_data),
            "all_fixes": all_patch_details,
            "original_file": input_file,
            "patched_file": "output/patched_fsm.v"
        }
        with open("output/stage8_comprehensive_report.json", 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"✓ Stage 8 complete: {len(patches_applied)}/{len(stage5_data)} patches applied")
    print(f"{'='*70}")
    
    return len(patches_applied) > 0


def run_stage9():
    """Run Stage 9: Verification."""
    print("\n" + "="*70)
    print("STAGE 9: VERIFICATION")
    print("="*70)
    
    patched_file = "output/patched_fsm.v"
    
    if not os.path.exists(patched_file):
        print(f"\n⚠️  No patched file found: {patched_file}")
        print("  Stage 8 may not have generated patches.")
        return
    
    print("\nVerifying patched FSM...")
    
    try:
        result = stage9_pipeline(patched_file)
        
        if result.get("verification_passed"):
            print("✓ Verification PASSED")
        else:
            print("⚠️  Verification WARNINGS detected")
        
        print(f"✓ Report saved to: output/stage9_result.json")
    
    except Exception as e:
        print(f"⚠️  Verification error: {e}")


def run_stage10():
    """Run Stage 10: Final Report."""
    print("\n" + "="*70)
    print("STAGE 10: FINAL REPORT GENERATION")
    print("="*70)
    
    if not STAGE10_AVAILABLE:
        print("\n⚠️  Stage 10 not available")
        return
    
    print("\nGenerating comprehensive security report...")
    
    try:
        report = stage10_pipeline()
        
        print("✓ Final report generated")
        print(f"✓ Saved to: output/final_report.json")
        
        # Print summary
        if "summary" in report:
            summary = report["summary"]
            print(f"\n📊 Summary:")
            print(f"   Total vulnerabilities: {summary.get('total_vulnerabilities', 0)}")
            print(f"   Patches applied: {summary.get('patches_applied', 0)}")
            print(f"   Verification status: {summary.get('verification_status', 'Unknown')}")
    
    except Exception as e:
        print(f"⚠️  Report generation error: {e}")


def main():
    """Main pipeline runner."""
    print("="*70)
    print("FSMGuard - Stages 5-10: Patching & Verification Pipeline")
    print("="*70)
    
    # Check if stage 1-4 outputs exist
    print("\n📋 Checking prerequisites...")
    
    try:
        stage1_data = load_stage1_data()
        stage4_data = load_stage4_data()
        print("✓ Stage 1-4 outputs found")
        
        # Get input file from stage 1 data
        input_file = stage1_data.get("input_file", "input/dma_timing_control_verilog.v")
        
    except SystemExit:
        return 1
    
    # Run stages 5-10
    try:
        # Stage 5: Subgraph Isolation
        stage5_data = run_stage5(stage1_data, stage4_data)
        
        # Stage 6: RL Environment Demo
        run_stage6()
        
        # Stage 7: RL Agent (check only)
        run_stage7()
        
        # Stage 8: Patch Generation
        patches_applied = run_stage8(stage5_data, input_file)
        
        # Stage 9: Verification (if patches were applied)
        if patches_applied:
            run_stage9()
        
        # Stage 10: Final Report
        run_stage10()
        
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETE")
        print("="*70)
        print("\n📁 Output files:")
        print("  - output/stage5_output.json")
        print("  - output/stage8_report.json")
        print("  - output/stage9_result.json")
        print("  - output/final_report.json")
        print("="*70)
        
        return 0
    
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
