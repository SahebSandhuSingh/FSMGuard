"""
FSMGuard - Stage 6: Quick Demo
================================

Demonstrates the FSMGuardEnv with a simple episode walkthrough.
Shows how the agent interacts with weak states step-by-step.

Author: FSMGuard Team
Date: 2026-03-07
"""

from fsm_env import FSMGuardEnv, ACTION_NAMES
import numpy as np


def demo_episode():
    """
    Run a demonstration episode with manual actions.
    """
    print("=" * 70)
    print("FSMGuardEnv - Interactive Demo")
    print("=" * 70)
    
    # Create sample weak states
    weak_states = [
        {
            "state_name": "MEM_ACC",
            "risk_score": 0.87,
            "cwe": "CWE-1245",  # Should use Guard Insertion (actions 0-2)
            "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
        },
        {
            "state_name": "DEBUG",
            "risk_score": 0.91,
            "cwe": "CWE-1233",  # Should use Transition Pruning (actions 3-4)
            "features": [2, 1, 1, 1, 0.5, 0, 1, 1, 1, 0, 1, 0, 1]
        },
        {
            "state_name": "EXECUTE",
            "risk_score": 0.74,
            "cwe": "CWE-1298",  # Should use State Re-encoding (actions 5-6)
            "features": [3, 2, 1, 3, 0.6, 0, 1, 1, 0, 1, 0, 1, 1]
        }
    ]
    
    # Initialize environment
    env = FSMGuardEnv(weak_states)
    obs, info = env.reset(seed=42)
    
    print(f"\nEpisode initialized with {len(weak_states)} weak states")
    print(f"Observation shape: {obs.shape}")
    print(f"Action space: {env.action_space.n} discrete actions\n")
    
    # Manually chosen optimal actions for each CWE
    optimal_actions = {
        "CWE-1245": 0,  # Guard Insertion + auth_signal
        "CWE-1233": 3,  # Transition Pruning + full removal
        "CWE-1298": 5   # State Re-encoding + hamming
    }
    
    total_reward = 0.0
    step = 0
    terminated = False
    
    print("-" * 70)
    print("Starting Episode...")
    print("-" * 70)
    
    while not terminated:
        step += 1
        current_state = env.weak_states[env.current_step]
        cwe = current_state["cwe"]
        
        # Choose optimal action based on CWE
        action = optimal_actions.get(cwe, 0)
        
        print(f"\n{'='*70}")
        print(f"STEP {step}/{len(weak_states)}")
        print(f"{'='*70}")
        print(f"Current State:  {current_state['state_name']}")
        print(f"CWE Label:      {cwe}")
        print(f"Risk Score:     {current_state['risk_score']:.3f}")
        print(f"Action Chosen:  {action} - {ACTION_NAMES[action]}")
        
        # Take action
        obs, reward, terminated, truncated, info = env.step(action)
        total_reward += reward
        
        print(f"\nReward:         {reward:.1f}")
        print(f"Fix Correct:    {'✅ YES' if info['fix_correct'] else '❌ NO'}")
        print(f"Total Reward:   {total_reward:.1f}")
        
        if terminated:
            print(f"\n{'='*70}")
            print(f"EPISODE COMPLETE!")
            print(f"{'='*70}")
            print(f"Final Total Reward: {total_reward:.1f}")
            print(f"Steps Taken: {step}")
    
    print("\n" + "=" * 70)
    print("Demo Complete")
    print("=" * 70)
    
    return total_reward


def show_observation_breakdown():
    """
    Show detailed breakdown of observation vector structure.
    """
    print("\n" + "=" * 70)
    print("Observation Vector Breakdown")
    print("=" * 70)
    
    weak_states = [{
        "state_name": "TEST_STATE",
        "risk_score": 0.85,
        "cwe": "CWE-1245",
        "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
    }]
    
    env = FSMGuardEnv(weak_states)
    obs, _ = env.reset(seed=42)
    
    print(f"\nTotal observation size: {len(obs)} values\n")
    print(f"[0:13]   Features (13 values):")
    print(f"         {obs[0:13]}")
    print(f"\n[13:22]  Fix History (9 values):")
    print(f"         {obs[13:22]}")
    print(f"\n[22]     Remaining states ratio: {obs[22]:.3f}")
    print(f"[23]     Risk score: {obs[23]:.3f}")
    print(f"[24]     Progress: {obs[24]:.3f}")
    print(f"\n[25:29]  CWE One-Hot (4 values):")
    print(f"         {obs[25:29]}")
    print(f"\n[29]     Episode progress: {obs[29]:.3f}")
    
    print("\n" + "=" * 70)


def show_action_definitions():
    """
    Display all available actions.
    """
    print("\n" + "=" * 70)
    print("Action Space Definitions")
    print("=" * 70)
    print("\nTotal Actions: 9\n")
    
    for action_idx, action_name in ACTION_NAMES.items():
        print(f"  {action_idx} → {action_name}")
    
    print("\n" + "-" * 70)
    print("CWE to Action Mapping (Optimal):")
    print("-" * 70)
    print("  CWE-1245 → Actions 0-2  (Guard Insertion)")
    print("  CWE-1233 → Actions 3-4  (Transition Pruning)")
    print("  CWE-1298 → Actions 5-6  (State Re-encoding)")
    print("  CWE-1280 → Actions 7-8  (Deadlock Trap)")
    print("=" * 70)


if __name__ == "__main__":
    # Show environment details
    show_action_definitions()
    show_observation_breakdown()
    
    # Run demo episode
    total_reward = demo_episode()
    
    print(f"\n🎯 Final Score: {total_reward:.1f} points")
    print("\n✅ FSMGuardEnv is ready for RL training with PPO!")
