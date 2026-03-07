"""
FSMGuard - Stage 7: PPO Agent Training
======================================

Trains a Proximal Policy Optimization (PPO) agent to learn
optimal hardware security fix strategies for FSM vulnerabilities.

The agent learns to map CWE labels to appropriate fixes through
reinforcement learning over thousands of episodes.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_checker import check_env
from fsm_env import FSMGuardEnv, ACTION_NAMES


class FSMGuardCallback(BaseCallback):
    """
    Custom callback for tracking training progress.
    
    Monitors:
    - Mean reward every 10,000 steps
    - Fix accuracy (% of correct actions)
    - Saves best model automatically
    """
    
    def __init__(self, check_freq: int = 10000, save_path: str = "./models/", verbose: int = 1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.save_path = save_path
        self.best_mean_reward = -np.inf
        self.episode_rewards = []
        self.episode_correct_fixes = []
        self.current_episode_reward = 0.0
        self.current_episode_correct = 0
        self.current_episode_total = 0
        
        # Create save directory
        os.makedirs(save_path, exist_ok=True)
    
    def _on_step(self) -> bool:
        """
        Called after each step in the environment.
        """
        # Track rewards and fix correctness from info
        if len(self.locals.get("infos", [])) > 0:
            info = self.locals["infos"][0]
            if "reward" in info:
                self.current_episode_reward += info["reward"]
                self.current_episode_total += 1
                if info.get("fix_correct", False):
                    self.current_episode_correct += 1
            
            # Check if episode ended
            if self.locals.get("dones", [False])[0]:
                # Store episode statistics
                self.episode_rewards.append(self.current_episode_reward)
                if self.current_episode_total > 0:
                    accuracy = self.current_episode_correct / self.current_episode_total
                    self.episode_correct_fixes.append(accuracy)
                
                # Reset episode tracking
                self.current_episode_reward = 0.0
                self.current_episode_correct = 0
                self.current_episode_total = 0
        
        # Check progress every check_freq steps
        if self.n_calls % self.check_freq == 0 and len(self.episode_rewards) > 0:
            # Calculate statistics from last 100 episodes
            recent_rewards = self.episode_rewards[-100:]
            recent_accuracy = self.episode_correct_fixes[-100:] if self.episode_correct_fixes else [0]
            
            mean_reward = np.mean(recent_rewards)
            mean_accuracy = np.mean(recent_accuracy) * 100
            
            # Save best model
            if mean_reward > self.best_mean_reward:
                self.best_mean_reward = mean_reward
                save_path = os.path.join(self.save_path, "fsm_ppo_best")
                self.model.save(save_path)
                if self.verbose > 0:
                    print(f"  → New best model saved! (reward: {mean_reward:.2f})")
            
            # Print progress
            if self.verbose > 0:
                print(f"\n{'='*70}")
                print(f"Step [{self.n_calls:,}] Training Progress")
                print(f"{'='*70}")
                print(f"  Mean Reward (last 100):  {mean_reward:.2f}")
                print(f"  Fix Accuracy (last 100): {mean_accuracy:.1f}%")
                print(f"  Best Mean Reward:        {self.best_mean_reward:.2f}")
                print(f"  Total Episodes:          {len(self.episode_rewards)}")
                print(f"{'='*70}\n")
        
        return True


def create_training_environment():
    """
    Create the FSMGuardEnv with sample weak states for training.
    
    Returns:
        FSMGuardEnv instance
    """
    # Sample weak states covering all 4 CWE types
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
        },
        {
            "state_name": "HALT",
            "risk_score": 0.65,
            "cwe": "CWE-1280",
            "features": [2, 0, 0, 2, 0.4, 1, 0, 1, 0, 0, 1, 0, 1]
        }
    ]
    
    return FSMGuardEnv(weak_states)


def train_ppo_agent():
    """
    Train the PPO agent to learn optimal FSM fix strategies.
    """
    print("=" * 70)
    print("FSMGuard - Stage 07: PPO Agent Training")
    print("=" * 70)
    
    # Step 1: Create environment
    print("\n[1/5] Creating training environment...")
    env = create_training_environment()
    print(f"  ✅ Environment created with {len(env.weak_states_original)} weak states")
    
    # Step 2: Validate environment
    print("\n[2/5] Validating environment compatibility...")
    try:
        check_env(env, warn=True, skip_render_check=True)
        print("  ✅ Environment check passed")
    except Exception as e:
        print(f"  ❌ Environment check failed: {e}")
        return
    
    # Step 3: Configure PPO with custom policy network
    print("\n[3/5] Configuring PPO agent...")
    
    # Custom policy network architecture
    # 3-layer networks for both policy (pi) and value (vf)
    policy_kwargs = dict(
        net_arch=dict(
            pi=[128, 128, 64],  # Policy network: 128 → 128 → 64
            vf=[128, 128, 64]   # Value network:  128 → 128 → 64
        )
    )
    
    # Create TensorBoard log directory
    log_dir = "./logs/"
    os.makedirs(log_dir, exist_ok=True)
    
    # Initialize PPO model
    model = PPO(
        policy="MlpPolicy",
        env=env,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=log_dir
    )
    
    print("  ✅ PPO agent configured")
    print(f"     Policy Network: [128, 128, 64]")
    print(f"     Value Network:  [128, 128, 64]")
    print(f"     Learning Rate:  3e-4")
    print(f"     Total Actions:  9")
    
    # Step 4: Train agent with custom callback
    print("\n[4/5] Training agent...")
    print(f"  Total timesteps: 200,000")
    print(f"  Progress updates every 10,000 steps\n")
    
    # Create callback for progress tracking
    callback = FSMGuardCallback(
        check_freq=10000,
        save_path="./models/",
        verbose=1
    )
    
    # Train the agent
    try:
        model.learn(
            total_timesteps=200000,
            callback=callback,
            progress_bar=True
        )
        print("\n  ✅ Training completed successfully")
    except KeyboardInterrupt:
        print("\n  ⚠️  Training interrupted by user")
    except Exception as e:
        print(f"\n  ❌ Training failed: {e}")
        return
    
    # Step 5: Save final trained agent
    print("\n[5/5] Saving trained agent...")
    model_path = "fsm_ppo_agent"
    model.save(model_path)
    print(f"  ✅ Agent saved to {model_path}.zip")
    
    # Final summary
    print("\n" + "=" * 70)
    print("Training Complete!")
    print("=" * 70)
    print(f"  Final model:     {model_path}.zip")
    print(f"  Best model:      ./models/fsm_ppo_best.zip")
    print(f"  TensorBoard logs: {log_dir}")
    print("\nTo evaluate the agent, run:")
    print("  python3 evaluate_agent.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    train_ppo_agent()
