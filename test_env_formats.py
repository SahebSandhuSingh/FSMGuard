#!/usr/bin/env python3
"""Test that FSMGuardEnv handles both dict and list feature formats"""

from fsm_env import FSMGuardEnv
import numpy as np

print("=" * 70)
print("Testing FSMGuardEnv Feature Format Handling")
print("=" * 70)

# Test 1: Features as list (original format)
print("\nTest 1: Features as LIST (training format)")
weak_states_list = [{
    'state_name': 'TEST_STATE',
    'risk_score': 0.75,
    'cwe': 'CWE-1245',
    'features': [1, 2, 0, 3, 0.5, 0, 1, 1, 0, 1, 0, 1, 1]
}]
env1 = FSMGuardEnv(weak_states_list)
obs1, _ = env1.reset()
print(f"  ✅ Environment created successfully")
print(f"     Observation shape: {obs1.shape}")
print(f"     First 5 features: {obs1[:5]}")

# Test 2: Features as dict (Stage 4 format)
print("\nTest 2: Features as DICT (Stage 4 format)")
weak_states_dict = [{
    'state_name': 'TEST_STATE',
    'risk_score': 0.75,
    'cwe': 'CWE-1245',
    'features': {
        'in_degree': 1.0,
        'out_degree': 2.0,
        'self_loop': 0.0,
        'reset_distance': 3.0,
        'neighbor_risk': 0.5,
        'is_terminal': 0.0,
        'guarded': 1.0,
        'privilege': 1.0,
        'auth_bypass': 0.0,
        'auth_sequence_completed': 1.0,
        'path_bypasses_auth': 0.0,
        'lock_signal_asserted': 1.0,
        'privilege_escalation': 1.0
    }
}]
env2 = FSMGuardEnv(weak_states_dict)
obs2, _ = env2.reset()
print(f"  ✅ Environment created successfully")
print(f"     Observation shape: {obs2.shape}")
print(f"     First 5 features: {obs2[:5]}")

# Verify they match
print("\n" + "=" * 70)
if np.allclose(obs1[:13], obs2[:13], rtol=1e-5):
    print("✅ SUCCESS: Both formats produce identical observations!")
    print("   Environment now handles dict and list features seamlessly.")
else:
    print("⚠️  WARNING: Observations differ slightly")
    print(f"   Max difference: {np.max(np.abs(obs1[:13] - obs2[:13]))}")
print("=" * 70)
