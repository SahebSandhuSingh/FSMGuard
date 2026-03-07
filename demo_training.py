"""
FSMGuard - Stage 7: Quick Demo Training
========================================

Runs a SHORT training session (5000 steps) to demonstrate
the training pipeline without waiting for full 200K steps.

Use this to:
- Verify training works
- See progress updates
- Test evaluation pipeline
- Demo for presentations

For production use, run train_agent.py with 200K steps.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from fsm_env import FSMGuardEnv
from train_agent import FSMGuardCallback, create_training_environment


def demo_training():
    """
    Quick demo training with 5000 timesteps.
    """
    print("=" * 70)
    print("FSMGuard - Demo Training (5000 steps)")
    print("=" * 70)
    print("\nThis is a SHORT demo. For full training, use train_agent.py\n")
    
    # Create environment
    print("[1/4] Creating environment...")
    env = create_training_environment()
    print(f"  ✅ Environment created with {len(env.weak_states_original)} weak states")
    
    # Validate environment
    print("\n[2/4] Validating environment...")
    check_env(env, warn=False, skip_render_check=True)
    print("  ✅ Environment validated")
    
    # Configure PPO
    print("\n[3/4] Configuring PPO...")
    
    policy_kwargs = dict(
        net_arch=dict(
            pi=[128, 128, 64],
            vf=[128, 128, 64]
        )
    )
    
    log_dir = "./logs/"
    os.makedirs(log_dir, exist_ok=True)
    
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=512,  # Smaller for demo
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=log_dir
    )
    
    print("  ✅ PPO configured")
    
    # Train
    print("\n[4/4] Training (5000 steps)...")
    print("  Progress updates every 2000 steps\n")
    
    callback = FSMGuardCallback(
        check_freq=2000,
        save_path="./models/",
        verbose=1
    )
    
    model.learn(
        total_timesteps=5000,
        callback=callback,
        progress_bar=True
    )
    
    # Save
    print("\nSaving demo model...")
    model.save("fsm_ppo_demo")
    print("  ✅ Saved to fsm_ppo_demo.zip")
    
    print("\n" + "=" * 70)
    print("Demo Training Complete!")
    print("=" * 70)
    print("\nTo evaluate this demo model, run:")
    print("  python3 -c \"from evaluate_agent import evaluate_agent; evaluate_agent('fsm_ppo_demo', 3)\"")
    print("\nFor full training (200K steps):")
    print("  python3 train_agent.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    demo_training()
