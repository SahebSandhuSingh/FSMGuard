"""
FSMGuard - Stage 6: RL Environment (Gymnasium)
===============================================

Gymnasium environment for training RL agents to select optimal
hardware security fixes for FSM vulnerabilities.

Each episode processes one FSM design with multiple weak states.
Each step represents fixing one weak state with one of 9 actions.

Author: FSMGuard Team
Date: 2026-03-07
"""

import gymnasium as gym
import numpy as np
from typing import Dict, List, Any, Tuple, Optional


# Action name mappings for interpretability
ACTION_NAMES = {
    0: "Guard Insertion + auth_signal",
    1: "Guard Insertion + lock_signal",
    2: "Guard Insertion + privilege_check",
    3: "Transition Pruning + full removal",
    4: "Transition Pruning + redirect",
    5: "State Re-encoding + hamming",
    6: "State Re-encoding + parity",
    7: "Deadlock Trap + alert signal",
    8: "Deadlock Trap + hard lockdown"
}


class FSMGuardEnv(gym.Env):
    """
    Gymnasium environment for FSM vulnerability mitigation.
    
    Observation Space:
        Box(30,) containing:
        - [0:13]: Current state features (13 values)
        - [13:22]: Fix history (9 binary values)
        - [22]: Remaining states ratio
        - [23]: Current risk score
        - [24]: Progress through sequence
        - [25:29]: CWE one-hot encoding (4 values)
        - [29]: Episode progress
    
    Action Space:
        Discrete(9) representing 9 different hardware fixes
    
    Reward Rules:
        - CWE-matched fix: +10
        - Partially correct: +3
        - Wrong fix: -5
        - High risk bonus: +5 (if risk >= 0.80)
        - Sequential coherence: +2
        - Action variety penalty: -3
        - Episode completion: +20
    """
    
    metadata = {"render_modes": ["human"]}
    
    def __init__(self, weak_states: List[Dict[str, Any]]):
        """
        Initialize the FSMGuard environment.
        
        Args:
            weak_states: List of dictionaries from Stage 05, each containing:
                - state_name: Name of the weak state
                - risk_score: Vulnerability score (0-1)
                - cwe: CWE label (e.g., "CWE-1245")
                - features: List of 13 feature values
        """
        super().__init__()
        
        # Store weak states (keep original for resets)
        if not weak_states:
            raise ValueError("weak_states list cannot be empty")
        self.weak_states_original = weak_states.copy()
        self.weak_states = weak_states.copy()
        self.total_weak_states = len(weak_states)
        
        # Define observation space: 30-dimensional continuous
        # Values normalized between 0 and 10
        self.observation_space = gym.spaces.Box(
            low=0.0,
            high=10.0,
            shape=(30,),
            dtype=np.float32
        )
        
        # Define action space: 9 discrete actions
        self.action_space = gym.spaces.Discrete(9)
        
        # Episode state variables
        self.current_step = 0
        self.fix_history = [0] * 9  # Track which actions have been used
        self.previous_action = None
        self.previous_cwe = None
        self.consecutive_same_action = 0
        self.total_reward = 0.0
        
    def reset(self, seed: Optional[int] = None, options: Optional[Dict] = None) -> Tuple[np.ndarray, Dict]:
        """
        Reset the environment for a new episode.
        
        Args:
            seed: Random seed for reproducibility
            options: Additional options (unused)
        
        Returns:
            observation: Initial observation (30,) array
            info: Empty info dictionary
        """
        # Set random seed if provided (must be called before any randomness)
        super().reset(seed=seed)
        
        # Make a fresh copy from original and shuffle
        self.weak_states = self.weak_states_original.copy()
        
        # Create a local RNG for reproducibility
        if seed is not None:
            rng = np.random.RandomState(seed)
            # Shuffle weak states with seeded RNG
            rng.shuffle(self.weak_states)
        else:
            # Shuffle weak states for varied training
            np.random.shuffle(self.weak_states)
        
        # Reset episode state
        self.current_step = 0
        self.fix_history = [0] * 9
        self.previous_action = None
        self.previous_cwe = None
        self.consecutive_same_action = 0
        self.total_reward = 0.0
        
        # Build initial observation
        observation = self._build_observation()
        info = {}
        
        return observation, info
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: Integer action (0-8)
        
        Returns:
            observation: Next observation (30,) array
            reward: Reward for this step
            terminated: Whether episode is complete
            truncated: Whether episode was truncated (always False)
            info: Dictionary with step metadata
        """
        # Get current weak state
        current_state = self.weak_states[self.current_step]
        state_name = current_state["state_name"]
        risk_score = current_state["risk_score"]
        cwe = current_state["cwe"]
        features = current_state["features"]
        
        # Compute reward for this action
        reward = self._compute_reward(action, features, risk_score, cwe)
        self.total_reward += reward
        
        # Update fix history
        self.fix_history[action] = 1
        
        # Update consecutive action counter
        if action == self.previous_action:
            self.consecutive_same_action += 1
        else:
            self.consecutive_same_action = 1
        
        # Store previous state for sequential coherence
        self.previous_action = action
        self.previous_cwe = cwe
        
        # Increment step counter
        self.current_step += 1
        
        # Check if episode is done
        terminated = (self.current_step >= self.total_weak_states)
        truncated = False
        
        # Add episode completion bonus
        if terminated:
            reward += 20.0
        
        # Build next observation (or final state if done)
        if not terminated:
            observation = self._build_observation()
        else:
            # Return zeros for final observation (episode ended)
            observation = np.zeros(30, dtype=np.float32)
        
        # Build info dictionary
        info = {
            "state_name": state_name,
            "action_taken": action,
            "action_name": ACTION_NAMES[action],
            "reward": reward,
            "cwe": cwe,
            "risk_score": risk_score,
            "fix_correct": reward >= 10.0,
            "total_reward": self.total_reward
        }
        
        return observation, reward, terminated, truncated, info
    
    def _build_observation(self) -> np.ndarray:
        """
        Build observation vector for current state.
        
        Returns:
            30-dimensional numpy array
        """
        obs = np.zeros(30, dtype=np.float32)
        
        # Get current weak state
        current_state = self.weak_states[self.current_step]
        features = current_state["features"]
        risk_score = current_state["risk_score"]
        cwe = current_state["cwe"]
        
        # [0:13] - Normalized features (divide by 10 for normalization)
        for i, feat in enumerate(features[:13]):
            obs[i] = float(feat) / 10.0
        
        # [13:22] - Fix history (binary: 1 if action used, 0 otherwise)
        for i, used in enumerate(self.fix_history):
            obs[13 + i] = float(used)
        
        # [22] - Remaining states ratio
        remaining = self.total_weak_states - self.current_step
        obs[22] = float(remaining) / float(self.total_weak_states)
        
        # [23] - Current risk score
        obs[23] = float(risk_score)
        
        # [24] - Progress through sequence
        obs[24] = float(self.current_step) / float(self.total_weak_states)
        
        # [25:29] - CWE one-hot encoding
        cwe_encoding = self._cwe_one_hot(cwe)
        obs[25:29] = cwe_encoding
        
        # [29] - Episode progress (same as [24])
        obs[29] = float(self.current_step) / float(self.total_weak_states)
        
        return obs
    
    def _cwe_one_hot(self, cwe: str) -> np.ndarray:
        """
        Convert CWE label to one-hot encoding.
        
        Args:
            cwe: CWE label string (e.g., "CWE-1245")
        
        Returns:
            4-dimensional one-hot vector
        """
        encoding = np.zeros(4, dtype=np.float32)
        
        if cwe == "CWE-1245":
            encoding[0] = 1.0
        elif cwe == "CWE-1233":
            encoding[1] = 1.0
        elif cwe == "CWE-1298":
            encoding[2] = 1.0
        elif cwe == "CWE-1280":
            encoding[3] = 1.0
        # Unknown CWE returns [0, 0, 0, 0]
        
        return encoding
    
    def _compute_reward(self, action: int, features: List, 
                       risk_score: float, cwe: str) -> float:
        """
        Compute reward based on action, state features, and CWE label.
        
        Reward Rules:
            1. CWE-matched fix: +10
            2. Partially correct: +3
            3. Wrong fix: -5
            4. High risk bonus: +5 (if risk >= 0.80 and correct)
            5. Sequential coherence: +2 (same CWE, same fix category)
            6. Action variety penalty: -3 (same action 3+ times)
            7. Episode completion: +20 (handled in step())
        
        Args:
            action: Selected action (0-8)
            features: State features (not used in basic reward)
            risk_score: Vulnerability score (0-1)
            cwe: CWE label
        
        Returns:
            Computed reward value
        """
        reward = 0.0
        fix_correct = False
        
        # Rule 1 & 2 & 3: CWE-based reward
        if cwe == "CWE-1245":
            if action in [0, 1, 2]:  # Guard Insertion
                reward = 10.0
                fix_correct = True
            elif action in [3, 4]:  # Transition Pruning
                reward = 3.0
            else:
                reward = -5.0
        
        elif cwe == "CWE-1233":
            if action in [3, 4]:  # Transition Pruning
                reward = 10.0
                fix_correct = True
            elif action in [0, 1, 2]:  # Guard Insertion
                reward = 3.0
            else:
                reward = -5.0
        
        elif cwe == "CWE-1298":
            if action in [5, 6]:  # State Re-encoding
                reward = 10.0
                fix_correct = True
            elif action in [7, 8]:  # Deadlock Trap
                reward = 3.0
            else:
                reward = -5.0
        
        elif cwe == "CWE-1280":
            if action in [7, 8]:  # Deadlock Trap
                reward = 10.0
                fix_correct = True
            elif action in [5, 6]:  # State Re-encoding
                reward = 3.0
            else:
                reward = -5.0
        
        else:
            # Unknown CWE - neutral reward
            reward = -5.0
        
        # Rule 4: High risk bonus
        if fix_correct and risk_score >= 0.80:
            reward += 5.0
        
        # Rule 5: Sequential coherence bonus
        if self.previous_cwe == cwe and self.previous_action is not None:
            # Check if same fix category
            prev_category = self._get_action_category(self.previous_action)
            curr_category = self._get_action_category(action)
            if prev_category == curr_category:
                reward += 2.0
        
        # Rule 6: Action variety penalty
        if self.consecutive_same_action >= 3:
            reward -= 3.0
        
        return reward
    
    def _get_action_category(self, action: int) -> str:
        """
        Get the category of an action for coherence checking.
        
        Args:
            action: Action index (0-8)
        
        Returns:
            Category string
        """
        if action in [0, 1, 2]:
            return "guard_insertion"
        elif action in [3, 4]:
            return "transition_pruning"
        elif action in [5, 6]:
            return "state_reencoding"
        elif action in [7, 8]:
            return "deadlock_trap"
        else:
            return "unknown"
    
    def render(self):
        """
        Render current episode status to console.
        """
        if self.current_step == 0:
            print("\n" + "=" * 60)
            print("FSMGuard Environment - Episode Start")
            print("=" * 60)
            return
        
        # Get previous state (the one just processed)
        prev_step = self.current_step - 1
        if prev_step >= 0 and prev_step < len(self.weak_states):
            state = self.weak_states[prev_step]
            action = self.previous_action
            
            print(f"\nStep [{self.current_step}/{self.total_weak_states}] "
                  f"| State: {state['state_name']} | CWE: {state['cwe']}")
            if action is not None:
                print(f"Action: {ACTION_NAMES[action]}")
                print(f"Risk: {state['risk_score']:.3f}")
        
        if self.current_step >= self.total_weak_states:
            print("\n" + "=" * 60)
            print(f"Episode Complete | Total Reward: {self.total_reward:.2f}")
            print("=" * 60)
    
    def close(self):
        """
        Clean up environment resources.
        """
        pass
