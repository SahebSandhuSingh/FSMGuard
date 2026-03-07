"""
Thorough Stable Baselines3 Compatibility Verification
======================================================

Explicitly tests all SB3 requirements without bypassing checks.
Shows detailed diagnostics of what env_checker validates.

Author: FSMGuard Team  
Date: 2026-03-07
"""

from fsm_env import FSMGuardEnv
import numpy as np
import sys


def manual_sb3_checks():
    """
    Manually verify all requirements that SB3 env_checker validates.
    """
    print("=" * 70)
    print("Manual Stable Baselines3 Compatibility Checks")
    print("=" * 70)
    
    # Create test environment
    weak_states = [
        {
            "state_name": "TEST1",
            "risk_score": 0.85,
            "cwe": "CWE-1245",
            "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
        },
        {
            "state_name": "TEST2",
            "risk_score": 0.90,
            "cwe": "CWE-1233",
            "features": [2, 1, 1, 1, 0.5, 0, 1, 1, 1, 0, 1, 0, 1]
        }
    ]
    
    env = FSMGuardEnv(weak_states)
    
    # CHECK 1: Environment has required attributes
    print("\n" + "-" * 70)
    print("CHECK 1: Required Attributes")
    print("-" * 70)
    required_attrs = ['observation_space', 'action_space', 'reset', 'step']
    for attr in required_attrs:
        if hasattr(env, attr):
            print(f"  ✅ {attr}: Present")
        else:
            print(f"  ❌ {attr}: MISSING")
            return False
    
    # CHECK 2: Reset returns correct format
    print("\n" + "-" * 70)
    print("CHECK 2: Reset Method")
    print("-" * 70)
    try:
        result = env.reset()
        if isinstance(result, tuple) and len(result) == 2:
            obs, info = result
            print(f"  ✅ Returns tuple of (observation, info)")
            print(f"  ✅ Observation type: {type(obs)}")
            print(f"  ✅ Observation shape: {obs.shape}")
            print(f"  ✅ Info type: {type(info)}")
        else:
            print(f"  ❌ Reset should return (observation, info) tuple")
            return False
    except Exception as e:
        print(f"  ❌ Reset failed: {e}")
        return False
    
    # CHECK 3: Observation in observation_space
    print("\n" + "-" * 70)
    print("CHECK 3: Observation Space Compliance")
    print("-" * 70)
    obs, _ = env.reset()
    if env.observation_space.contains(obs):
        print(f"  ✅ Observation is in observation_space")
        print(f"  ✅ Observation dtype: {obs.dtype}")
        print(f"  ✅ Expected dtype: {env.observation_space.dtype}")
    else:
        print(f"  ❌ Observation NOT in observation_space")
        print(f"     Obs shape: {obs.shape}, Space shape: {env.observation_space.shape}")
        print(f"     Obs bounds: [{obs.min()}, {obs.max()}]")
        print(f"     Space bounds: [{env.observation_space.low.min()}, {env.observation_space.high.max()}]")
        return False
    
    # CHECK 4: Step returns correct format
    print("\n" + "-" * 70)
    print("CHECK 4: Step Method Format")
    print("-" * 70)
    action = env.action_space.sample()
    try:
        result = env.step(action)
        if isinstance(result, tuple) and len(result) == 5:
            obs, reward, terminated, truncated, info = result
            print(f"  ✅ Returns 5-tuple (obs, reward, terminated, truncated, info)")
            print(f"  ✅ Observation type: {type(obs)}")
            print(f"  ✅ Reward type: {type(reward)} = {reward}")
            print(f"  ✅ Terminated type: {type(terminated)} = {terminated}")
            print(f"  ✅ Truncated type: {type(truncated)} = {truncated}")
            print(f"  ✅ Info type: {type(info)}")
        else:
            print(f"  ❌ Step should return 5-tuple")
            return False
    except Exception as e:
        print(f"  ❌ Step failed: {e}")
        return False
    
    # CHECK 5: Reward is scalar float
    print("\n" + "-" * 70)
    print("CHECK 5: Reward Type")
    print("-" * 70)
    env.reset()
    obs, reward, terminated, truncated, info = env.step(0)
    if isinstance(reward, (int, float, np.number)):
        print(f"  ✅ Reward is scalar: {reward} (type: {type(reward).__name__})")
    else:
        print(f"  ❌ Reward must be scalar, got: {type(reward)}")
        return False
    
    # CHECK 6: Terminated and truncated are booleans
    print("\n" + "-" * 70)
    print("CHECK 6: Done Flags")
    print("-" * 70)
    if isinstance(terminated, (bool, np.bool_)):
        print(f"  ✅ Terminated is boolean: {terminated}")
    else:
        print(f"  ❌ Terminated must be boolean, got: {type(terminated)}")
        return False
    
    if isinstance(truncated, (bool, np.bool_)):
        print(f"  ✅ Truncated is boolean: {truncated}")
    else:
        print(f"  ❌ Truncated must be boolean, got: {type(truncated)}")
        return False
    
    # CHECK 7: Complete episode without errors
    print("\n" + "-" * 70)
    print("CHECK 7: Full Episode Rollout")
    print("-" * 70)
    env.reset()
    steps = 0
    try:
        for i in range(100):  # Safety limit
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            
            # Verify observation still in space
            if not env.observation_space.contains(obs):
                print(f"  ❌ Observation out of bounds at step {steps}")
                return False
            
            if terminated or truncated:
                print(f"  ✅ Episode completed successfully in {steps} steps")
                break
        else:
            print(f"  ⚠️  Episode didn't terminate in 100 steps")
    except Exception as e:
        print(f"  ❌ Episode failed at step {steps}: {e}")
        return False
    
    # CHECK 8: Multiple resets work correctly
    print("\n" + "-" * 70)
    print("CHECK 8: Multiple Resets")
    print("-" * 70)
    try:
        for i in range(3):
            obs, info = env.reset()
            if not env.observation_space.contains(obs):
                print(f"  ❌ Reset {i+1} produced invalid observation")
                return False
        print(f"  ✅ Multiple resets work correctly")
    except Exception as e:
        print(f"  ❌ Multiple resets failed: {e}")
        return False
    
    # CHECK 9: Seed reproducibility
    print("\n" + "-" * 70)
    print("CHECK 9: Seed Reproducibility")
    print("-" * 70)
    env.reset(seed=42)
    action = 0
    obs1, reward1, _, _, _ = env.step(action)
    
    env.reset(seed=42)
    obs2, reward2, _, _, _ = env.step(action)
    
    if np.allclose(obs1, obs2) and reward1 == reward2:
        print(f"  ✅ Same seed produces same results")
        print(f"     Reward: {reward1}")
    else:
        print(f"  ❌ Seed reproducibility failed")
        print(f"     Obs match: {np.allclose(obs1, obs2)}")
        print(f"     Reward match: {reward1 == reward2}")
        return False
    
    return True


def run_official_sb3_checker():
    """
    Run the official Stable Baselines3 env_checker.
    """
    print("\n" + "=" * 70)
    print("Official Stable Baselines3 env_checker")
    print("=" * 70)
    
    try:
        from stable_baselines3.common.env_checker import check_env
        
        weak_states = [
            {
                "state_name": "TEST",
                "risk_score": 0.85,
                "cwe": "CWE-1245",
                "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
            }
        ]
        
        env = FSMGuardEnv(weak_states)
        
        print("\nRunning check_env() with warn=True...")
        print("(This will show any warnings or issues)\n")
        
        # This is the official checker - it will raise errors if something is wrong
        check_env(env, warn=True, skip_render_check=True)
        
        print("\n✅ Official env_checker completed with no errors")
        return True
        
    except Exception as e:
        print(f"\n❌ Official env_checker FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_with_ppo():
    """
    Test actually creating a PPO model with the environment.
    """
    print("\n" + "=" * 70)
    print("PPO Model Creation Test")
    print("=" * 70)
    
    try:
        from stable_baselines3 import PPO
        
        weak_states = [
            {
                "state_name": "TEST",
                "risk_score": 0.85,
                "cwe": "CWE-1245",
                "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
            },
            {
                "state_name": "TEST2",
                "risk_score": 0.90,
                "cwe": "CWE-1233",
                "features": [2, 1, 1, 1, 0.5, 0, 1, 1, 1, 0, 1, 0, 1]
            }
        ]
        
        env = FSMGuardEnv(weak_states)
        
        print("\nCreating PPO model...")
        model = PPO("MlpPolicy", env, verbose=0)
        print("✅ PPO model created successfully")
        
        print("\nTesting model.learn() for 10 steps...")
        model.learn(total_timesteps=10)
        print("✅ PPO training works correctly")
        
        print("\nTesting model.predict()...")
        obs, _ = env.reset()
        action, _states = model.predict(obs)
        print(f"✅ Model prediction works: action = {action}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ PPO test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("█" + " " * 68 + "█")
    print("█" + "  COMPREHENSIVE STABLE BASELINES3 COMPATIBILITY TEST".center(68) + "█")
    print("█" + " " * 68 + "█")
    print("█" * 70 + "\n")
    
    # Run all tests
    test1 = manual_sb3_checks()
    test2 = run_official_sb3_checker()
    test3 = test_with_ppo()
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    print(f"  Manual checks:          {'✅ PASSED' if test1 else '❌ FAILED'}")
    print(f"  Official env_checker:   {'✅ PASSED' if test2 else '❌ FAILED'}")
    print(f"  PPO integration:        {'✅ PASSED' if test3 else '❌ FAILED'}")
    print("=" * 70)
    
    if test1 and test2 and test3:
        print("\n🎉 ALL TESTS PASSED - Environment is fully compatible!")
        print("   No checks bypassed. Ready for RL training.\n")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - See details above\n")
        sys.exit(1)
