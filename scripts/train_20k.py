"""
FSMGuard - 20K Training Run
============================

Trains for 20,000 steps - good balance between speed and completeness.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from train_agent import FSMGuardCallback, create_training_environment

print("=" * 70)
print("FSMGuard - 20K Steps Training")
print("=" * 70)

# Create and validate environment
print("\n[1/3] Setting up environment...")
env = create_training_environment()
check_env(env, warn=False, skip_render_check=True)
print("  ✅ Environment ready")

# Configure PPO
print("\n[2/3] Configuring PPO agent...")
policy_kwargs = dict(
    net_arch=dict(pi=[128, 128, 64], vf=[128, 128, 64])
)

log_dir = "./logs/"
os.makedirs(log_dir, exist_ok=True)

model = PPO(
    policy="MlpPolicy",
    env=env,
    learning_rate=3e-4,
    n_steps=1024,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    policy_kwargs=policy_kwargs,
    verbose=1,
    tensorboard_log=log_dir
)
print("  ✅ Agent configured")

# Train with progress tracking
print("\n[3/3] Training for 20,000 steps...")
print("  Updates every 5,000 steps\n")

callback = FSMGuardCallback(
    check_freq=5000,
    save_path="./models/",
    verbose=1
)

model.learn(
    total_timesteps=20000,
    callback=callback,
    progress_bar=True
)

# Save final model
print("\nSaving model...")
model.save("fsm_ppo_20k")
print("  ✅ Saved to fsm_ppo_20k.zip")

print("\n" + "=" * 70)
print("20K Training Complete!")
print("=" * 70)
print("\nEvaluate with:")
print("  python3 -c \"from evaluate_agent import evaluate_agent; evaluate_agent('fsm_ppo_20k', 5)\"")
print("\nOr use best model:")
print("  python3 evaluate_agent.py --best")
print("=" * 70 + "\n")
