"""
FSMGuard - Stage 7: Quick Training Test
========================================

Quick test of the training pipeline with reduced timesteps.
Verifies everything works before running full 200K training.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from fsm_env import FSMGuardEnv


def quick_test_training():
    """
    Quick test with only 1000 timesteps to verify setup.
    """
    print("=" * 70)
    print("FSMGuard - Quick Training Test")
    print("=" * 70)
    
    # Create environment
    print("\n[1/4] Creating environment...")
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
    print("  ✅ Environment created")
    
    # Validate environment
    print("\n[2/4] Validating environment...")
    try:
        check_env(env, warn=True, skip_render_check=True)
        print("  ✅ Environment valid")
    except Exception as e:
        print(f"  ❌ Environment check failed: {e}")
        return False
    
    # Create PPO agent
    print("\n[3/4] Creating PPO agent...")
    policy_kwargs = dict(
        net_arch=dict(pi=[128, 128, 64], vf=[128, 128, 64])
    )
    
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=256,  # Smaller for quick test
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        policy_kwargs=policy_kwargs,
        verbose=1
    )
    print("  ✅ PPO agent created")
    
    # Quick training
    print("\n[4/4] Running quick training (1000 steps)...")
    try:
        model.learn(total_timesteps=1000, progress_bar=True)
        print("\n  ✅ Training test passed")
    except Exception as e:
        print(f"\n  ❌ Training failed: {e}")
        return False
    
    # Test model prediction
    print("\nTesting model prediction...")
    obs, _ = env.reset()
    action, _states = model.predict(obs)
    print(f"  ✅ Model can predict actions: {action}")
    
    # Test save/load
    print("\nTesting model save/load...")
    test_path = "test_model"
    model.save(test_path)
    loaded_model = PPO.load(test_path)
    print(f"  ✅ Model save/load works")
    
    # Cleanup
    if os.path.exists(f"{test_path}.zip"):
        os.remove(f"{test_path}.zip")
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Ready for full training!")
    print("=" * 70)
    print("\nTo run full training:")
    print("  python3 train_agent.py")
    print("\n" + "=" * 70 + "\n")
    
    return True


if __name__ == "__main__":
    quick_test_training()
