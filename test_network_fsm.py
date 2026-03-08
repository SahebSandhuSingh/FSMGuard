#!/usr/bin/env python3
"""Test FSMGuard pipeline on network_fsm.v"""

import sys
import json

# Run pipeline on network FSM
input_file = "input/network_fsm.v"

print("="*70)
print("Testing FSMGuard on: network_fsm.v")
print("="*70)

# Stage 1: Parse Verilog
from parser.parse_verilog_v2 import stage1_pipeline
stage1_data = stage1_pipeline(input_file, "output/stage1_output.json")
print(f"\n✅ Stage 1: Parsed {len(stage1_data['states'])} states")

# Stage 2-3: Build graph and extract features
from fsmguard_pipeline import pipeline_stage2_stage3, build_fsm_graph
pyg_data = pipeline_stage2_stage3(stage1_data)
G, _ = build_fsm_graph(stage1_data)
print(f"✅ Stage 2-3: Graph built with {G.number_of_edges()} transitions")

# Stage 4: Security Analysis
from stage4_security_report import stage4_pipeline
state_names = stage1_data["states"]
report = stage4_pipeline(pyg_data, state_names, design_name="network_fsm",
                        model_path="fsm_gat_best.pth",
                        output_path="output/stage4_report.json")
print(f"✅ Stage 4: Detected {len(report['flagged_states'])} weak states")
for s in report['flagged_states']:
    print(f"   - {s['state_name']}: {s['cwe']} (Risk: {s['risk_score']:.3f})")

# Stage 5: Subgraph Extraction
from stage5_subgraph import stage5_pipeline
state_names = [s['state_name'] for s in report['flagged_states']]
stage5_pipeline(G, report['flagged_states'], state_names)
print(f"✅ Stage 5: Extracted {len(state_names)} subgraphs")

# Stage 6-7: RL Agent Decisions for ALL weak states
from stable_baselines3 import PPO
from fsm_env import FSMGuardEnv

model = PPO.load("models/fsm_ppo_best.zip")
categories = ["Guard Insertion", "Transition Pruning", "State Re-encoding", "Deadlock Trap"]
parameters = [
    ["auth_signal", "lock_signal", "priv_check"],
    ["full_removal", "redirect", "safe_redirect"],
    ["hamming", "parity", "both"],
    ["alert", "lockdown", "both"]
]
strictness_names = ["soft", "strict"]

fix_specs = []
for weak_state in report['flagged_states']:
    env = FSMGuardEnv([weak_state])
    obs, _ = env.reset()
    action, _ = model.predict(obs, deterministic=True)
    cat, par, strt = int(action[0]), int(action[1]), int(action[2])
    
    fix_specs.append({
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
    })

print(f"✅ Stage 6-7: Generated {len(fix_specs)} fixes")
for spec in fix_specs:
    print(f"   - {spec['state_name']}: {spec['fix_detail']['category']} + {spec['fix_detail']['parameter']}")

# Stage 8: Apply ALL fixes sequentially
from patch_gen import stage8_pipeline
stage8_reports = []
current_file = input_file

for idx, fix_spec in enumerate(fix_specs, 1):
    stage8_pipeline(current_file, fix_spec, output_dir="output")
    with open("output/stage8_report.json") as f:
        stage8_reports.append(json.load(f))
    current_file = "output/patched_fsm.v"

# Save combined report with all fixes
combined = {
    "fixes_applied": len(stage8_reports),
    "all_fixes": stage8_reports,
    "original_file": input_file,
    "patched_file": "output/patched_fsm.v"
}
with open("output/stage8_report.json", 'w') as f:
    json.dump(combined, f, indent=2)
print(f"✅ Stage 8: Applied {len(stage8_reports)} patches")

# Stage 9
from verify import stage9_pipeline
verify_result = stage9_pipeline("output/patched_fsm.v", "output/stage8_report.json")
print(f"✅ Stage 9: Verification {verify_result['overall']}")

# Stage 10
from report_gen import stage10_pipeline
final_report = stage10_pipeline()
print(f"✅ Stage 10: Report generated")

print("\n" + "="*70)
print("FINAL RESULTS")
print("="*70)
print(f"Design: {final_report['design']['original_file']}")
print(f"States: {final_report['design']['total_states']}")
print(f"Weak States Detected: {final_report['summary']['weak_states_detected']}")
print(f"Fixes Applied: {final_report['summary']['vulnerabilities_fixed']}")
print(f"Verification: {verify_result['overall']}")
print(f"Design Safe: {'YES ✅' if final_report['summary']['design_safe'] else 'NO ❌'}")
print("="*70)
