"""
FSMGuard - Stage 7: Agent Evaluation
====================================

Evaluates the trained PPO agent by running test episodes
and analyzing its fix selection behavior.

Shows per-step decisions and computes aggregate statistics
to assess agent performance.

Author: FSMGuard Team
Date: 2026-03-07
"""

import numpy as np
from stable_baselines3 import PPO
from fsm_env import FSMGuardEnv, CATEGORY_NAMES, PARAMETER_NAMES, STRICTNESS_NAMES
from collections import defaultdict


def decode_action(action):
    """
    Decode MultiDiscrete action into human-readable format.
    
    Args:
        action: NumPy array [category, parameter, strictness]
    
    Returns:
        Dictionary with decoded action components
    """
    categories = ["Guard", "Prune", "Re-encode", "Deadlock"]
    parameters = [
        ["auth_signal", "lock_signal", "priv_check"],
        ["full_removal", "redirect", "safe_redirect"],
        ["hamming", "parity", "both"],
        ["alert", "lockdown", "both"]
    ]
    strictness = ["soft", "strict"]
    
    cat = int(action[0])
    par = int(action[1])
    strt = int(action[2])
    
    return {
        "category": categories[cat],
        "parameter": parameters[cat][par],
        "strictness": strictness[strt],
        "fallback": "RESET" if strt == 1 else "IDLE"
    }


def create_evaluation_environment():
    """
    Create the same environment used for training.
    
    Returns:
        FSMGuardEnv instance
    """
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


def evaluate_agent(model_path: str = "fsm_ppo_agent", num_episodes: int = 10):
    """
    Evaluate the trained agent over multiple episodes.
    
    Args:
        model_path: Path to the trained model
        num_episodes: Number of test episodes to run
    """
    print("=" * 70)
    print("FSMGuard - Stage 07: Agent Evaluation")
    print("=" * 70)
    
    # Load trained agent
    print(f"\n[1/3] Loading trained agent from {model_path}.zip...")
    try:
        model = PPO.load(model_path)
        print("  ✅ Agent loaded successfully")
    except Exception as e:
        print(f"  ❌ Failed to load agent: {e}")
        print("\nMake sure you've trained the agent first:")
        print("  python3 train_agent.py")
        return
    
    # Create evaluation environment
    print("\n[2/3] Creating evaluation environment...")
    env = create_evaluation_environment()
    print(f"  ✅ Environment created with {len(env.weak_states_original)} weak states")
    
    # Run evaluation episodes
    print(f"\n[3/3] Running {num_episodes} evaluation episodes...\n")
    
    # Tracking statistics
    episode_rewards = []
    episode_accuracies = []
    cwe_action_map = defaultdict(lambda: defaultdict(int))  # CWE -> action -> count
    all_actions = []
    
    for episode in range(num_episodes):
        print("=" * 70)
        print(f"Episode {episode + 1}/{num_episodes}")
        print("=" * 70)
        
        obs, info = env.reset()
        done = False
        step = 0
        episode_reward = 0.0
        correct_fixes = 0
        total_fixes = 0
        
        while not done:
            step += 1
            
            # Get current state info BEFORE taking action
            current_state = env.weak_states[env.current_step]
            state_name = current_state["state_name"]
            cwe = current_state["cwe"]
            risk_score = current_state["risk_score"]
            
            # Agent selects action
            action, _states = model.predict(obs, deterministic=True)
            
            # Decode action for display
            decoded = decode_action(action)
            
            # Track CWE to action mapping (track category for statistics)
            cwe_action_map[cwe][int(action[0])] += 1
            all_actions.append(action.copy())
            
            # Take action in environment
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            # Update statistics
            episode_reward += reward
            total_fixes += 1
            if info.get("fix_correct", False):
                correct_fixes += 1
            
            # Print step details
            print(f"\nStep [{step}] | State: {state_name} | CWE: {cwe}")
            print(f"  Risk Score:  {risk_score:.3f}")
            print(f"  Category:    {decoded['category']}")
            print(f"  Parameter:   {decoded['parameter']}")
            print(f"  Strictness:  {decoded['strictness']}")
            print(f"  Fallback:    {decoded['fallback']}")
            print(f"  Reward:      {reward:.1f}")
            print(f"  Correct:     {'✅ YES' if info.get('fix_correct', False) else '❌ NO'}")
        
        # Episode summary
        accuracy = (correct_fixes / total_fixes * 100) if total_fixes > 0 else 0
        episode_rewards.append(episode_reward)
        episode_accuracies.append(accuracy)
        
        print(f"\n{'─' * 70}")
        print(f"Episode {episode + 1} Summary:")
        print(f"  Total Reward:  {episode_reward:.2f}")
        print(f"  Fix Accuracy:  {correct_fixes}/{total_fixes} ({accuracy:.1f}%)")
        print(f"{'─' * 70}\n")
    
    # Final Statistics
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    
    avg_reward = np.mean(episode_rewards)
    std_reward = np.std(episode_rewards)
    avg_accuracy = np.mean(episode_accuracies)
    std_accuracy = np.std(episode_accuracies)
    
    print(f"\nPerformance over {num_episodes} episodes:")
    print(f"  Average Reward:     {avg_reward:.2f} ± {std_reward:.2f}")
    print(f"  Average Accuracy:   {avg_accuracy:.1f}% ± {std_accuracy:.1f}%")
    print(f"  Best Episode:       {max(episode_rewards):.2f}")
    print(f"  Worst Episode:      {min(episode_rewards):.2f}")
    
    # Action distribution (by category)
    print(f"\nCategory Distribution:")
    category_counts = defaultdict(int)
    for action in all_actions:
        category_counts[int(action[0])] += 1
    
    total_actions = len(all_actions)
    categories = ["Guard Insertion", "Transition Pruning", "State Re-encoding", "Deadlock Trap"]
    for cat_idx in range(4):
        count = category_counts[cat_idx]
        percentage = (count / total_actions * 100) if total_actions > 0 else 0
        print(f"  {cat_idx}: {categories[cat_idx]}")
        print(f"      Used {count}/{total_actions} times ({percentage:.1f}%)")
    
    # CWE-specific behavior
    print(f"\nMost Common Category per CWE:")
    for cwe in sorted(cwe_action_map.keys()):
        actions_for_cwe = cwe_action_map[cwe]
        most_common_action = max(actions_for_cwe.items(), key=lambda x: x[1])
        action_idx, count = most_common_action
        total_for_cwe = sum(actions_for_cwe.values())
        percentage = (count / total_for_cwe * 100)
        
        print(f"  {cwe}:")
        print(f"    → Category {action_idx}: {categories[action_idx]}")
        print(f"      ({count}/{total_for_cwe} times, {percentage:.1f}%)")
    
    # Expected behavior check
    print(f"\nExpected Behavior Check:")
    expected_mappings = {
        "CWE-1245": 0,  # Guard Insertion
        "CWE-1233": 1,  # Transition Pruning
        "CWE-1298": 2,  # State Re-encoding
        "CWE-1280": 3   # Deadlock Trap
    }
    
    for cwe, expected_category in expected_mappings.items():
        if cwe in cwe_action_map:
            actions_for_cwe = cwe_action_map[cwe]
            most_common_action = max(actions_for_cwe.items(), key=lambda x: x[1])[0]
            if most_common_action == expected_category:
                print(f"  ✅ {cwe}: Agent learned correct fix category ({categories[expected_category]})")
            else:
                print(f"  ⚠️  {cwe}: Agent uses suboptimal category {most_common_action} ({categories[most_common_action]})")
    
    print("\n" + "=" * 70)
    print("Evaluation Complete!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    import sys
    
    # Check if user wants to evaluate best model
    model_path = "fsm_ppo_agent"
    if len(sys.argv) > 1 and sys.argv[1] == "--best":
        model_path = "./models/fsm_ppo_best"
        print("Evaluating best model from training...\n")
    
    evaluate_agent(model_path=model_path, num_episodes=10)
