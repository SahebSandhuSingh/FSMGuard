"""
FSMGuard — PIPELINE VALIDATION SCRIPT
======================================

Validates the complete FSMGuard pipeline from Stage 01 through Stage 04.
Each stage's output is passed directly to the next stage and validated.

Usage:
    python3 validate_pipeline.py
"""

import sys
import os
import json
import torch
import numpy as np

# Add paths for imports
sys.path.insert(0, 'parser')
sys.path.insert(0, '..')

# Import all stages
from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import stage4_pipeline, load_model

# ============================================================================
# VALIDATION RESULTS STORAGE
# ============================================================================

class ValidationResults:
    """Store validation results for all stages."""
    def __init__(self):
        self.stage1 = {}
        self.stage2 = {}
        self.stage3 = {}
        self.stage4 = {}
        self.overall = True
        
    def add_check(self, stage, check_name, passed, expected=None, received=None):
        """Add a validation check result."""
        if stage not in [self.stage1, self.stage2, self.stage3, self.stage4]:
            return
            
        stage[check_name] = {
            'passed': passed,
            'expected': expected,
            'received': received
        }
        
        if not passed:
            self.overall = False


# ============================================================================
# STAGE 01 VALIDATION
# ============================================================================

def validate_stage1(filepath):
    """
    Validate Stage 01: Verilog parsing and FSM extraction.
    
    Checks:
    1. States list not empty (expects 5: IDLE, AUTH, CHECK, ACCESS, LOCK)
    2. Transitions not empty (expects at least 5)
    3. Reset state is IDLE
    4. Output file exists and is valid JSON
    
    Args:
        filepath: Path to Verilog file
        
    Returns:
        Tuple of (fsm_data, validation_dict)
    """
    checks = {}
    fsm_data = None
    
    try:
        # Run Stage 01
        fsm_data = stage1_pipeline(filepath)
        
        if not fsm_data:
            checks['states'] = {'passed': False, 'expected': '5 states', 'received': 'None'}
            checks['transitions'] = {'passed': False, 'expected': '5+ transitions', 'received': 'None'}
            checks['reset_state'] = {'passed': False, 'expected': 'IDLE', 'received': 'None'}
            checks['output_file'] = {'passed': False, 'expected': 'JSON file', 'received': 'None'}
            return None, checks
        
        # CHECK 1: States found
        expected_states = {"IDLE", "AUTH", "CHECK", "ACCESS", "LOCK"}
        found_states = set(fsm_data.get('states', []))
        all_found = expected_states.issubset(found_states)
        
        checks['states'] = {
            'passed': all_found,
            'expected': f'{len(expected_states)} states: {sorted(expected_states)}',
            'received': f'{len(found_states)} states: {sorted(found_states)}'
        }
        
        # CHECK 2: Transitions found
        transitions = fsm_data.get('transitions', [])
        expected_min = 5
        
        # Check for specific expected transitions
        transition_pairs = [(t['src'], t['dst']) for t in transitions]
        expected_transitions = [
            ('IDLE', 'AUTH'),
            ('AUTH', 'CHECK'),
            ('AUTH', 'LOCK'),
            ('CHECK', 'ACCESS'),
            ('CHECK', 'LOCK')
        ]
        
        found_transitions = [t for t in expected_transitions if t in transition_pairs]
        all_trans_found = len(found_transitions) >= expected_min
        
        checks['transitions'] = {
            'passed': all_trans_found,
            'expected': f'{expected_min}+ transitions',
            'received': f'{len(transitions)} transitions found'
        }
        
        if not all_trans_found:
            missing = [f"{s}→{d}" for s, d in expected_transitions if (s, d) not in transition_pairs]
            checks['transitions']['missing'] = missing
        
        # CHECK 3: Reset state correct
        reset_state = fsm_data.get('reset_state', '')
        reset_correct = reset_state == 'IDLE'
        
        checks['reset_state'] = {
            'passed': reset_correct,
            'expected': 'IDLE',
            'received': reset_state
        }
        
        # CHECK 4: Output file exists
        output_path = 'output/stage1_output.json'
        file_exists = os.path.exists(output_path)
        valid_json = False
        
        if file_exists:
            try:
                with open(output_path, 'r') as f:
                    json.load(f)
                valid_json = True
            except:
                valid_json = False
        
        checks['output_file'] = {
            'passed': file_exists and valid_json,
            'expected': 'Valid JSON file',
            'received': 'Found' if file_exists else 'Missing'
        }
        
    except Exception as e:
        checks['error'] = {
            'passed': False,
            'expected': 'Stage 01 to complete',
            'received': f'Exception: {str(e)}'
        }
    
    return fsm_data, checks


# ============================================================================
# STAGE 02 VALIDATION
# ============================================================================

def validate_stage2(fsm_data):
    """
    Validate Stage 02: Graph construction.
    
    Checks:
    1. Data object created
    2. Node count matches state count
    3. Edge count matches transition count
    4. Edge index shape is [2, num_edges]
    
    Args:
        fsm_data: FSM data from Stage 01
        
    Returns:
        Tuple of (data, validation_dict)
    """
    checks = {}
    data = None
    
    try:
        if not fsm_data:
            checks['data_object'] = {'passed': False, 'expected': 'PyG Data', 'received': 'No input'}
            return None, checks
        
        # Run Stage 02 & 03 (they're combined)
        data = pipeline_stage2_stage3(fsm_data)
        
        # CHECK 1: Data object created
        data_created = data is not None
        checks['data_object'] = {
            'passed': data_created,
            'expected': 'PyTorch Geometric Data object',
            'received': type(data).__name__ if data else 'None'
        }
        
        if not data:
            checks['node_count'] = {'passed': False, 'expected': 'Match states', 'received': 'No data'}
            checks['edge_count'] = {'passed': False, 'expected': 'Match transitions', 'received': 'No data'}
            checks['edge_shape'] = {'passed': False, 'expected': '[2, num_edges]', 'received': 'No data'}
            return None, checks
        
        # CHECK 2: Node count correct
        num_states = len(fsm_data['states'])
        num_nodes = data.x.shape[0]
        node_count_correct = num_nodes == num_states
        
        checks['node_count'] = {
            'passed': node_count_correct,
            'expected': f'{num_states} nodes',
            'received': f'{num_nodes} nodes'
        }
        
        # CHECK 3: Edge count correct
        num_transitions = len(fsm_data['transitions'])
        num_edges = data.edge_index.shape[1]
        edge_count_correct = num_edges == num_transitions
        
        checks['edge_count'] = {
            'passed': edge_count_correct,
            'expected': f'{num_transitions} edges',
            'received': f'{num_edges} edges'
        }
        
        # CHECK 4: Edge index shape
        edge_shape = list(data.edge_index.shape)
        expected_shape = [2, num_edges]
        shape_correct = edge_shape == expected_shape
        
        checks['edge_shape'] = {
            'passed': shape_correct,
            'expected': f'{expected_shape}',
            'received': f'{edge_shape}'
        }
        
    except Exception as e:
        checks['error'] = {
            'passed': False,
            'expected': 'Stage 02 to complete',
            'received': f'Exception: {str(e)}'
        }
    
    return data, checks


# ============================================================================
# STAGE 03 VALIDATION
# ============================================================================

def validate_stage3(data, num_states):
    """
    Validate Stage 03: Feature generation.
    
    Checks:
    1. Feature matrix shape is [num_states, 13]
    2. All 13 features have valid values
    3. Reset state (node 0) has reset_distance == 0
    4. No NaN or infinite values
    
    Args:
        data: PyG Data object from Stage 02
        num_states: Expected number of states
        
    Returns:
        validation_dict
    """
    checks = {}
    
    try:
        if data is None:
            checks['feature_shape'] = {'passed': False, 'expected': f'[{num_states}, 13]', 'received': 'No data'}
            checks['all_features'] = {'passed': False, 'expected': '13 features', 'received': 'No data'}
            checks['reset_distance'] = {'passed': False, 'expected': '0', 'received': 'No data'}
            checks['no_nan'] = {'passed': False, 'expected': 'No NaN', 'received': 'No data'}
            return checks
        
        # CHECK 1: Feature shape
        feature_shape = list(data.x.shape)
        expected_shape = [num_states, 13]
        shape_correct = feature_shape == expected_shape
        
        checks['feature_shape'] = {
            'passed': shape_correct,
            'expected': f'{expected_shape}',
            'received': f'{feature_shape}'
        }
        
        # CHECK 2: All 13 features present and valid
        feature_names = [
            "in_degree", "out_degree", "self_loop", "reset_distance",
            "neighbor_risk", "is_terminal", "guarded", "privilege",
            "auth_bypass", "auth_sequence_completed", "path_bypasses_auth",
            "lock_signal_asserted", "privilege_escalation"
        ]
        
        all_valid = True
        invalid_features = []
        
        if data.x.shape[1] == 13:
            for i in range(13):
                col = data.x[:, i]
                # Check if column has any non-zero values or is intentionally binary/zero
                # Features that can legitimately be all zeros:
                # - Binary flags (2, 5, 6, 7, 8, 9, 10, 11, 12)
                # - neighbor_risk (4) - can be zero if no neighbors have risk
                allowed_zero_features = [2, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                
                if torch.all(col == 0) and i not in allowed_zero_features:
                    # Structural features like in_degree, out_degree shouldn't all be zero
                    all_valid = False
                    invalid_features.append(f"{i}:{feature_names[i]}")
        
        checks['all_features'] = {
            'passed': all_valid and data.x.shape[1] == 13,
            'expected': '13 valid features',
            'received': f'{data.x.shape[1]} features' + (f' (suspicious: {invalid_features})' if invalid_features else '')
        }
        
        # CHECK 3: Reset state distance
        # Assuming IDLE is first state (index 0) and its reset_distance (feature 3) should be 0
        if data.x.shape[0] > 0 and data.x.shape[1] > 3:
            reset_dist = data.x[0, 3].item()
            reset_dist_correct = abs(reset_dist) < 0.01  # Allow for floating point
            
            checks['reset_distance'] = {
                'passed': reset_dist_correct,
                'expected': '0.0',
                'received': f'{reset_dist:.4f}'
            }
        else:
            checks['reset_distance'] = {
                'passed': False,
                'expected': '0.0',
                'received': 'Shape too small'
            }
        
        # CHECK 4: No NaN or infinite values
        no_nan = torch.isfinite(data.x).all().item()
        
        checks['no_nan'] = {
            'passed': no_nan,
            'expected': 'All finite values',
            'received': 'Valid' if no_nan else 'Contains NaN/Inf'
        }
        
    except Exception as e:
        checks['error'] = {
            'passed': False,
            'expected': 'Stage 03 to complete',
            'received': f'Exception: {str(e)}'
        }
    
    return checks


# ============================================================================
# STAGE 04 VALIDATION
# ============================================================================

def validate_stage4(data, state_names):
    """
    Validate Stage 04: GNN detection and report generation.
    
    Checks:
    1. Model loads correctly
    2. Inference runs correctly
    3. Threshold applied correctly (0.40)
    4. Report generated correctly
    5. Severity mapping correct
    6. Attack paths valid
    
    Args:
        data: PyG Data object from Stage 03
        state_names: List of state names
        
    Returns:
        validation_dict
    """
    checks = {}
    
    try:
        # CHECK 1: Model loads
        model_path = "fsm_gat_best.pth"
        model = None
        model_loaded = False
        
        try:
            model = load_model(model_path)
            model_loaded = True
            checks['model_loads'] = {
                'passed': True,
                'expected': 'Model loaded',
                'received': 'Success'
            }
        except FileNotFoundError:
            checks['model_loads'] = {
                'passed': False,
                'expected': 'Model file exists',
                'received': f'{model_path} not found'
            }
        except Exception as e:
            checks['model_loads'] = {
                'passed': False,
                'expected': 'Model loads',
                'received': f'Error: {str(e)}'
            }
        
        if not model_loaded or data is None:
            checks['inference'] = {'passed': False, 'expected': 'Inference runs', 'received': 'No model/data'}
            checks['threshold'] = {'passed': False, 'expected': 'Threshold applied', 'received': 'No inference'}
            checks['report'] = {'passed': False, 'expected': 'Report generated', 'received': 'No inference'}
            checks['severity'] = {'passed': False, 'expected': 'Severity correct', 'received': 'No inference'}
            checks['attack_path'] = {'passed': False, 'expected': 'Attack path valid', 'received': 'No inference'}
            return checks
        
        # CHECK 2: Inference runs
        inference_passed = False
        output_shape_correct = False
        
        try:
            with torch.no_grad():
                logits = model(data.x, data.edge_index)
                output_shape = list(logits.shape)
                expected_output_shape = [len(state_names), 2]
                output_shape_correct = output_shape == expected_output_shape
                inference_passed = True
            
            checks['inference'] = {
                'passed': inference_passed and output_shape_correct,
                'expected': f'Output shape {expected_output_shape}',
                'received': f'Output shape {output_shape}' if inference_passed else 'Failed'
            }
        except Exception as e:
            checks['inference'] = {
                'passed': False,
                'expected': 'Inference completes',
                'received': f'Error: {str(e)}'
            }
        
        # Run full Stage 04 pipeline
        try:
            report = stage4_pipeline(
                data=data,
                state_names=state_names,
                design_name="validation_test",
                model_path=model_path,
                output_path="output/stage4_report.json",
                threshold=0.40
            )
            
            # CHECK 3: Threshold applied correctly
            threshold = 0.40
            threshold_correct = True
            
            for flagged in report['flagged_states']:
                if flagged['risk_score'] < threshold:
                    threshold_correct = False
                    break
            
            checks['threshold'] = {
                'passed': threshold_correct,
                'expected': f'All flagged >= {threshold}',
                'received': 'Correct' if threshold_correct else 'Some below threshold'
            }
            
            # CHECK 4: Report generated
            report_path = "output/stage4_report.json"
            report_exists = os.path.exists(report_path)
            
            required_fields = ['state_name', 'risk_score', 'severity', 'cwe', 
                             'recommended_fix', 'attack_path', 'features']
            all_fields_present = True
            
            if report_exists and report.get('flagged_states'):
                for flagged in report['flagged_states']:
                    for field in required_fields:
                        if field not in flagged:
                            all_fields_present = False
                            break
            
            checks['report'] = {
                'passed': report_exists and all_fields_present,
                'expected': 'Complete report with all fields',
                'received': 'Valid' if (report_exists and all_fields_present) else 'Incomplete'
            }
            
            # CHECK 5: Severity correct
            severity_correct = True
            severity_errors = []
            
            for flagged in report['flagged_states']:
                score = flagged['risk_score']
                severity = flagged['severity']
                
                expected_severity = None
                if score >= 0.80:
                    expected_severity = 'CRITICAL'
                elif score >= 0.60:
                    expected_severity = 'HIGH'
                elif score >= 0.40:
                    expected_severity = 'MEDIUM'
                
                if severity != expected_severity:
                    severity_correct = False
                    severity_errors.append(f"{flagged['state_name']}: {score:.2f}→{severity} (expected {expected_severity})")
            
            checks['severity'] = {
                'passed': severity_correct,
                'expected': 'Correct severity mapping',
                'received': 'Correct' if severity_correct else f'Errors: {severity_errors}'
            }
            
            # CHECK 6: Attack path valid
            attack_path_valid = True
            path_errors = []
            
            reset_state = state_names[0] if state_names else 'IDLE'  # Assume first is reset
            
            for flagged in report['flagged_states']:
                path = flagged.get('attack_path', '')
                
                if not path or path == "No direct path found from reset":
                    continue
                
                path_states = [s.strip() for s in path.split('→')]
                
                # Check path starts from reset state
                if path_states and path_states[0] != reset_state:
                    attack_path_valid = False
                    path_errors.append(f"{flagged['state_name']}: Path doesn't start from {reset_state}")
                
                # Check path ends at flagged state
                if path_states and path_states[-1] != flagged['state_name']:
                    attack_path_valid = False
                    path_errors.append(f"{flagged['state_name']}: Path doesn't end at target")
            
            checks['attack_path'] = {
                'passed': attack_path_valid,
                'expected': 'Valid attack paths',
                'received': 'Valid' if attack_path_valid else f'Errors: {path_errors}'
            }
            
        except Exception as e:
            checks['threshold'] = {'passed': False, 'expected': 'Threshold check', 'received': f'Error: {str(e)}'}
            checks['report'] = {'passed': False, 'expected': 'Report generated', 'received': f'Error: {str(e)}'}
            checks['severity'] = {'passed': False, 'expected': 'Severity check', 'received': f'Error: {str(e)}'}
            checks['attack_path'] = {'passed': False, 'expected': 'Attack path check', 'received': f'Error: {str(e)}'}
        
    except Exception as e:
        checks['error'] = {
            'passed': False,
            'expected': 'Stage 04 to complete',
            'received': f'Exception: {str(e)}'
        }
    
    return checks


# ============================================================================
# REPORT PRINTING
# ============================================================================

def print_validation_report(results):
    """
    Print formatted validation report.
    
    Args:
        results: ValidationResults object
    """
    print("\n" + "=" * 80)
    print("FSMGuard — PIPELINE VALIDATION REPORT")
    print("=" * 80)
    
    # Stage 01
    print("\nSTAGE 01 — Input & Parsing")
    stage1_pass = print_stage_checks(results.stage1, [
        ('states', 'States found'),
        ('transitions', 'Transitions found'),
        ('reset_state', 'Reset state correct'),
        ('output_file', 'Output file saved')
    ])
    print(f"  Stage 01 Status:             {'PASS' if stage1_pass else 'FAIL'}")
    print("-" * 80)
    
    # Stage 02
    print("\nSTAGE 02 — Graph Construction")
    stage2_pass = print_stage_checks(results.stage2, [
        ('data_object', 'Data object created'),
        ('node_count', 'Node count correct'),
        ('edge_count', 'Edge count correct'),
        ('edge_shape', 'Edge index shape')
    ])
    print(f"  Stage 02 Status:             {'PASS' if stage2_pass else 'FAIL'}")
    print("-" * 80)
    
    # Stage 03
    print("\nSTAGE 03 — Feature Generation")
    stage3_pass = print_stage_checks(results.stage3, [
        ('feature_shape', 'Feature shape'),
        ('all_features', 'All 13 features'),
        ('reset_distance', 'Reset distance'),
        ('no_nan', 'No NaN values')
    ])
    print(f"  Stage 03 Status:             {'PASS' if stage3_pass else 'FAIL'}")
    print("-" * 80)
    
    # Stage 04
    print("\nSTAGE 04 — GNN Detection & Report")
    stage4_pass = print_stage_checks(results.stage4, [
        ('model_loads', 'Model loads'),
        ('inference', 'Inference runs'),
        ('threshold', 'Threshold applied'),
        ('report', 'Report generated'),
        ('severity', 'Severity correct'),
        ('attack_path', 'Attack path valid')
    ])
    print(f"  Stage 04 Status:             {'PASS' if stage4_pass else 'FAIL'}")
    print("-" * 80)
    
    # Overall
    overall_pass = stage1_pass and stage2_pass and stage3_pass and stage4_pass
    print(f"\nOVERALL PIPELINE STATUS:       {'PASS' if overall_pass else 'FAIL'}")
    print("=" * 80)
    print()


def print_stage_checks(stage_dict, checks):
    """
    Print individual check results for a stage.
    
    Args:
        stage_dict: Dictionary of check results
        checks: List of (key, label) tuples
        
    Returns:
        Boolean indicating if all checks passed
    """
    all_passed = True
    
    for key, label in checks:
        if key in stage_dict:
            check = stage_dict[key]
            passed = check['passed']
            status = 'PASS' if passed else 'FAIL'
            
            # Pad label to align status
            padded_label = f"  CHECK {checks.index((key, label)) + 1} {label}:".ljust(32)
            print(f"{padded_label} {status}")
            
            if not passed:
                all_passed = False
                # Print detailed failure info
                if check.get('expected'):
                    print(f"    Expected: {check['expected']}")
                if check.get('received'):
                    print(f"    Received: {check['received']}")
                if check.get('missing'):
                    print(f"    Missing:  {', '.join(check['missing'])}")
        else:
            print(f"  CHECK {checks.index((key, label)) + 1} {label}:".ljust(32) + " SKIP")
            all_passed = False
    
    return all_passed


# ============================================================================
# MAIN VALIDATION FUNCTION
# ============================================================================

def run_full_validation(filepath):
    """
    Run complete pipeline validation.
    
    Args:
        filepath: Path to Verilog input file
        
    Returns:
        ValidationResults object
    """
    results = ValidationResults()
    
    # Ensure output directory exists
    os.makedirs('output', exist_ok=True)
    
    # Stage 01
    print("\n[Validating Stage 01...]")
    fsm_data, stage1_checks = validate_stage1(filepath)
    results.stage1 = stage1_checks
    
    if not fsm_data:
        print("❌ Stage 01 failed - cannot continue to Stage 02")
        results.stage2 = {'error': {'passed': False, 'expected': 'Stage 01 output', 'received': 'None'}}
        results.stage3 = {'error': {'passed': False, 'expected': 'Stage 01 output', 'received': 'None'}}
        results.stage4 = {'error': {'passed': False, 'expected': 'Stage 01 output', 'received': 'None'}}
        return results
    
    # Stage 02
    print("[Validating Stage 02...]")
    data, stage2_checks = validate_stage2(fsm_data)
    results.stage2 = stage2_checks
    
    if not data:
        print("❌ Stage 02 failed - cannot continue to Stage 03")
        results.stage3 = {'error': {'passed': False, 'expected': 'Stage 02 output', 'received': 'None'}}
        results.stage4 = {'error': {'passed': False, 'expected': 'Stage 02 output', 'received': 'None'}}
        return results
    
    # Stage 03
    print("[Validating Stage 03...]")
    stage3_checks = validate_stage3(data, len(fsm_data['states']))
    results.stage3 = stage3_checks
    
    # Stage 04
    print("[Validating Stage 04...]")
    stage4_checks = validate_stage4(data, fsm_data['states'])
    results.stage4 = stage4_checks
    
    return results


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for validation script."""
    
    # Configuration
    verilog_file = "input/sample_fsm.v"
    
    # Check if input file exists
    if not os.path.exists(verilog_file):
        print(f"\n❌ ERROR: Input file not found: {verilog_file}")
        print("Please create the sample FSM Verilog file first.")
        return
    
    # Ensure directories exist
    os.makedirs('input', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    print("=" * 80)
    print("FSMGuard — Pipeline Integration Validation")
    print("=" * 80)
    print(f"\nInput file: {verilog_file}")
    print("Testing: Stage 01 → Stage 02 → Stage 03 → Stage 04")
    print()
    
    # Run validation
    results = run_full_validation(verilog_file)
    
    # Print report
    print_validation_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if results.overall else 1)


if __name__ == "__main__":
    main()
