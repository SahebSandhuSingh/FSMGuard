#!/usr/bin/env python3
"""
Test vulnerable FSM to verify weak state detection
"""
import sys
sys.path.insert(0, 'parser')
sys.path.insert(0, '..')

from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import stage4_pipeline

print('=' * 80)
print('Testing VULNERABLE FSM')
print('=' * 80)

# Run Stage 1
fsm_data = stage1_pipeline('input/vulnerable_fsm.v')
print(f'\nStates: {fsm_data["states"]}')
print(f'Transitions: {len(fsm_data["transitions"])}')

# Run Stage 2 & 3
data = pipeline_stage2_stage3(fsm_data)
print(f'\nFeature matrix: {data.x.shape}')

# Run Stage 4
report = stage4_pipeline(
    data=data,
    state_names=fsm_data['states'],
    design_name='vulnerable_fsm',
    model_path='fsm_gat_best.pth',
    output_path='output/vulnerable_report.json',
    threshold=0.40
)

print('\n' + '=' * 80)
print(f'DETECTION RESULTS:')
print('=' * 80)
print(f'Total states: {len(fsm_data["states"])}')
print(f'Weak states detected: {len(report["flagged_states"])}')

if report['flagged_states']:
    print('\nFlagged states:')
    for state in report['flagged_states']:
        print(f'  - {state["state_name"]}: Risk={state["risk_score"]:.3f}, Severity={state["severity"]}, CWE={state["cwe"]}')
else:
    print('\n⚠️  No weak states detected by the model')
    
print('=' * 80)

# Show feature analysis for vulnerable states
print('\nVULNERABLE FEATURES ANALYSIS:')
print('=' * 80)

feature_names = [
    'in_degree', 'out_degree', 'self_loop', 'reset_distance',
    'neighbor_risk', 'is_terminal', 'guarded', 'privilege',
    'auth_bypass', 'auth_sequence_completed', 'path_bypasses_auth',
    'lock_signal_asserted', 'privilege_escalation'
]

for i, state in enumerate(fsm_data['states']):
    print(f'\n{state}:')
    features_with_issues = []
    
    for j, fname in enumerate(feature_names):
        val = data.x[i, j].item()
        # Highlight potentially problematic features
        if fname in ['self_loop', 'privilege', 'auth_bypass', 'path_bypasses_auth', 'privilege_escalation']:
            if val > 0:
                features_with_issues.append(f'{fname}={val:.0f}')
    
    if features_with_issues:
        print(f'  ⚠️  Issues: {", ".join(features_with_issues)}')
    else:
        print(f'  ✓ No obvious issues in features')
