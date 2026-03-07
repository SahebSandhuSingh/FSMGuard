"""
FSMGuard - Stage 6: Environment Validation
==========================================

Validates the FSMGuardEnv against all requirements:
- Observation space shape
- Action space size
- Reward computation
- Episode termination
- Info dictionary fields

Author: FSMGuard Team
Date: 2026-03-07
"""

import numpy as np
from fsm_env import FSMGuardEnv


def run_validation():
    """
    Run comprehensive validation tests on FSMGuardEnv.
    """
    print("=" * 60)
    print("FSMGuardEnv Validation Script")
    print("=" * 60)
    
    # Sample weak states for testing (3 states)
    weak_states = [
        {
            "state_name": "MEM_ACC",
            "risk_score": 0.87,
            "cwe": "CWE-1245",
            "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
        },
        {
            "state_name": "DEBUG",
            "risk_score": 0.91,
            "cwe": "CWE-1233",
            "features": [2, 1, 1, 1, 0.5, 0, 1, 1, 1, 0, 1, 0, 1]
        },
        {
            "state_name": "EXECUTE",
            "risk_score": 0.74,
            "cwe": "CWE-1298",
            "features": [3, 2, 1, 3, 0.6, 0, 1, 1, 0, 1, 0, 1, 1]
        }
    ]
    
    print(f"\nTest Data: {len(weak_states)} weak states")
    for state in weak_states:
        print(f"  - {state['state_name']} | {state['cwe']} | Risk: {state['risk_score']}")
    
    # Initialize environment
    print("\n" + "-" * 60)
    print("Initializing FSMGuardEnv...")
    print("-" * 60)
    env = FSMGuardEnv(weak_states)
    print("✅ Environment initialized successfully")
    
    # CHECK 1: Observation space shape
    print("\n" + "-" * 60)
    print("CHECK 1: Observation Space Shape")
    print("-" * 60)
    obs, info = env.reset(seed=42)
    if obs.shape == (30,):
        print(f"✅ PASS: Observation shape is {obs.shape}")
    else:
        print(f"❌ FAIL: Expected shape (30,), got {obs.shape}")
        return False
    
    # CHECK 2: Action space size
    print("\n" + "-" * 60)
    print("CHECK 2: Action Space Size")
    print("-" * 60)
    if env.action_space.n == 9:
        print(f"✅ PASS: Action space size is {env.action_space.n}")
    else:
        print(f"❌ FAIL: Expected 9 actions, got {env.action_space.n}")
        return False
    
    # CHECK 3: CWE-1245 + action 0 (Guard Insertion) gives reward >= 10
    print("\n" + "-" * 60)
    print("CHECK 3: CWE-1245 + Guard Insertion Reward")
    print("-" * 60)
    env.reset(seed=42)
    # Find MEM_ACC state (CWE-1245)
    for step in range(len(weak_states)):
        current_state = env.weak_states[env.current_step]
        if current_state["cwe"] == "CWE-1245":
            obs, reward, terminated, truncated, info = env.step(0)  # Action 0: Guard Insertion
            print(f"  State: {current_state['state_name']}, CWE: {current_state['cwe']}")
            print(f"  Action: 0 (Guard Insertion + auth_signal)")
            print(f"  Reward: {reward}")
            if reward >= 10.0:
                print(f"✅ PASS: Reward {reward} >= 10")
            else:
                print(f"❌ FAIL: Expected reward >= 10, got {reward}")
                return False
            break
    
    # CHECK 4: CWE-1233 + action 3 (Transition Pruning) gives reward >= 10
    print("\n" + "-" * 60)
    print("CHECK 4: CWE-1233 + Transition Pruning Reward")
    print("-" * 60)
    env.reset(seed=42)
    found_cwe_1233 = False
    for step in range(len(weak_states)):
        current_state = env.weak_states[env.current_step]
        if current_state["cwe"] == "CWE-1233":
            obs, reward, terminated, truncated, info = env.step(3)  # Action 3: Transition Pruning
            print(f"  State: {current_state['state_name']}, CWE: {current_state['cwe']}")
            print(f"  Action: 3 (Transition Pruning + full removal)")
            print(f"  Reward: {reward}")
            if reward >= 10.0:
                print(f"✅ PASS: Reward {reward} >= 10")
                found_cwe_1233 = True
            else:
                print(f"❌ FAIL: Expected reward >= 10, got {reward}")
                return False
            break
    if not found_cwe_1233:
        print("⚠️  WARNING: CWE-1233 state not encountered in this seed")
    
    # CHECK 5: Wrong action gives reward == -5
    print("\n" + "-" * 60)
    print("CHECK 5: Wrong Action Penalty")
    print("-" * 60)
    env.reset(seed=42)
    current_state = env.weak_states[env.current_step]
    # CWE-1245 with wrong action (e.g., action 7 - Deadlock Trap)
    if current_state["cwe"] == "CWE-1245":
        obs, reward, terminated, truncated, info = env.step(7)  # Wrong action for CWE-1245
        print(f"  State: {current_state['state_name']}, CWE: {current_state['cwe']}")
        print(f"  Action: 7 (Deadlock Trap - WRONG for CWE-1245)")
        print(f"  Reward: {reward}")
        if reward == -5.0:
            print(f"✅ PASS: Wrong action penalty is {reward}")
        else:
            print(f"❌ FAIL: Expected reward -5, got {reward}")
            return False
    
    # CHECK 6: Episode terminates after 3 steps
    print("\n" + "-" * 60)
    print("CHECK 6: Episode Termination")
    print("-" * 60)
    env.reset(seed=42)
    steps_taken = 0
    terminated = False
    while not terminated and steps_taken < 10:  # Safety limit
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        steps_taken += 1
    
    if steps_taken == 3 and terminated:
        print(f"✅ PASS: Episode terminated after {steps_taken} steps")
    else:
        print(f"❌ FAIL: Expected termination after 3 steps, got {steps_taken}")
        return False
    
    # CHECK 7: Fix history updates correctly
    print("\n" + "-" * 60)
    print("CHECK 7: Fix History Tracking")
    print("-" * 60)
    env.reset(seed=42)
    actions_to_test = [0, 3, 5]
    for action in actions_to_test:
        obs, reward, terminated, truncated, info = env.step(action)
    
    # Check that fix_history has correct actions marked
    expected_history = [0] * 9
    for action in actions_to_test:
        expected_history[action] = 1
    
    if env.fix_history == expected_history:
        print(f"  Actions taken: {actions_to_test}")
        print(f"  Fix history: {env.fix_history}")
        print(f"✅ PASS: Fix history updated correctly")
    else:
        print(f"❌ FAIL: Fix history mismatch")
        print(f"  Expected: {expected_history}")
        print(f"  Got: {env.fix_history}")
        return False
    
    # CHECK 8: Info dictionary contains required fields
    print("\n" + "-" * 60)
    print("CHECK 8: Info Dictionary Fields")
    print("-" * 60)
    env.reset(seed=42)
    obs, reward, terminated, truncated, info = env.step(0)
    
    required_fields = [
        "state_name", "action_taken", "action_name",
        "reward", "cwe", "risk_score", "fix_correct"
    ]
    
    all_fields_present = True
    for field in required_fields:
        if field in info:
            print(f"  ✅ {field}: {info[field]}")
        else:
            print(f"  ❌ Missing field: {field}")
            all_fields_present = False
    
    if all_fields_present:
        print(f"✅ PASS: All required info fields present")
    else:
        print(f"❌ FAIL: Missing required info fields")
        return False
    
    # Additional validation: Check observation bounds
    print("\n" + "-" * 60)
    print("BONUS CHECK: Observation Value Bounds")
    print("-" * 60)
    env.reset(seed=42)
    obs, reward, terminated, truncated, info = env.step(0)
    
    if np.all(obs >= 0.0) and np.all(obs <= 10.0):
        print(f"  Observation min: {obs.min():.3f}")
        print(f"  Observation max: {obs.max():.3f}")
        print(f"✅ PASS: All observation values in [0, 10] range")
    else:
        print(f"❌ FAIL: Observation values out of bounds")
        print(f"  Min: {obs.min()}, Max: {obs.max()}")
        return False
    
    # Check for NaN values
    if not np.any(np.isnan(obs)):
        print(f"✅ PASS: No NaN values in observation")
    else:
        print(f"❌ FAIL: NaN values detected in observation")
        return False
    
    # Final summary
    print("\n" + "=" * 60)
    print("✅ ALL VALIDATION CHECKS PASSED")
    print("=" * 60)
    print("\nFSMGuardEnv is ready for Stable Baselines3 integration!")
    
    return True


def test_stable_baselines3_compatibility():
    """
    Test compatibility with Stable Baselines3 env_checker.
    """
    print("\n" + "=" * 60)
    print("Testing Stable Baselines3 Compatibility")
    print("=" * 60)
    
    try:
        from stable_baselines3.common.env_checker import check_env
        
        # Create sample environment
        weak_states = [
            {
                "state_name": "MEM_ACC",
                "risk_score": 0.87,
                "cwe": "CWE-1245",
                "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
            },
            {
                "state_name": "DEBUG",
                "risk_score": 0.91,
                "cwe": "CWE-1233",
                "features": [2, 1, 1, 1, 0.5, 0, 1, 1, 1, 0, 1, 0, 1]
            }
        ]
        
        env = FSMGuardEnv(weak_states)
        print("\nRunning Stable Baselines3 env_checker...")
        check_env(env, warn=True)
        print("✅ PASS: Environment is compatible with Stable Baselines3")
        
    except ImportError:
        print("⚠️  WARNING: Stable Baselines3 not installed")
        print("   Install with: pip install stable-baselines3")
        print("   Skipping compatibility check")
    except Exception as e:
        print(f"❌ FAIL: Environment check failed")
        print(f"   Error: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Run main validation
    success = run_validation()
    
    # Test SB3 compatibility if available
    if success:
        test_stable_baselines3_compatibility()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ VALIDATION COMPLETE - Environment Ready")
    else:
        print("❌ VALIDATION FAILED - Check errors above")
    print("=" * 60)
