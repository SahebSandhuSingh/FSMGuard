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


# Fix category mappings
CATEGORY_NAMES = [
    "Guard Insertion",
    "Transition Pruning",
    "State Re-encoding",
    "Deadlock Trap"
]

# Parameter mappings per category
PARAMETER_NAMES = [
    ["auth_signal", "lock_signal", "privilege_check"],           # Guard Insertion
    ["full_removal", "redirect", "safe_redirect"],               # Transition Pruning
    ["hamming", "parity", "both"],                                # State Re-encoding
    ["alert", "lockdown", "both"]                                 # Deadlock Trap
]

# Strictness mappings
STRICTNESS_NAMES = ["soft", "strict"]


class FSMGuardEnv(gym.Env):
    """
    Gymnasium environment for FSM vulnerability mitigation.
    
    Observation Space:
        Box(30,) containing:
        - [0:13]: Current state features (13 values)
        - [13:17]: Category history (4 binary values)
        - [17:20]: Parameter history (3 binary values)
        - [20:22]: Strictness history (2 binary values)
        - [22]: Remaining states ratio
        - [23]: Current risk score
        - [24]: Progress through sequence
        - [25:29]: CWE one-hot encoding (4 values)
        - [29]: Episode progress
    
    Action Space:
        MultiDiscrete([4, 3, 2]) representing:
        - Dimension 1: Fix Category (0-3)
        - Dimension 2: Fix Parameter (0-2)
        - Dimension 3: Strictness (0-1)
    
    Reward Rules:
        - Correct category + correct parameter: +10
        - Correct category + wrong parameter: +4
        - Wrong category: -5
        - Strict mode on high risk (>=0.80): +3 bonus
        - Soft mode on low risk (<0.50): +2 bonus
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
        
        # Normalize features format (convert dict to list if needed)
        self.weak_states_original = self._normalize_weak_states(weak_states)
        self.weak_states = self.weak_states_original.copy()
        self.total_weak_states = len(weak_states)
        
        # Define observation space: 30-dimensional continuous
        # Values normalized between 0 and 10
        self.observation_space = gym.spaces.Box(
            low=0.0,
            high=10.0,
            shape=(30,),
            dtype=np.float32
        )
        
        # Define action space: MultiDiscrete [category, parameter, strictness]
        self.action_space = gym.spaces.MultiDiscrete([4, 3, 2])
        
        # Episode state variables
        self.current_step = 0
        self.category_history = [0] * 4  # Track category usage
        self.parameter_history = [0] * 3  # Track parameter usage
        self.strictness_history = [0] * 2  # Track strictness usage
        self.previous_action = None
        self.previous_cwe = None
        self.consecutive_same_category = 0
        self.total_reward = 0.0
        
    def _normalize_weak_states(self, weak_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize weak states to ensure features are in list format.
        
        Stage 4 may return features as dict (key->value pairs) but the 
        environment expects a list. This method converts dict to list if needed.
        
        Args:
            weak_states: List of weak state dictionaries
        
        Returns:
            Normalized weak states with features as lists
        """
        # Feature order expected by the environment
        feature_order = [
            'in_degree', 'out_degree', 'self_loop', 'reset_distance',
            'neighbor_risk', 'is_terminal', 'guarded', 'privilege',
            'auth_bypass', 'auth_sequence_completed', 'path_bypasses_auth',
            'lock_signal_asserted', 'privilege_escalation'
        ]
        
        normalized_states = []
        for state in weak_states:
            normalized_state = state.copy()
            features = state.get('features', [])
            
            # Check if features is a dict and convert to list
            if isinstance(features, dict):
                # Convert dict to list using feature_order
                normalized_state['features'] = [
                    features.get(feat, 0.0) for feat in feature_order
                ]
            elif isinstance(features, list):
                # Already a list, ensure it has 13 elements
                if len(features) < 13:
                    # Pad with zeros if too short
                    normalized_state['features'] = features + [0.0] * (13 - len(features))
                else:
                    # Use first 13 if too long
                    normalized_state['features'] = features[:13]
            else:
                # Invalid format, create zero array
                normalized_state['features'] = [0.0] * 13
            
            normalized_states.append(normalized_state)
        
        return normalized_states
        
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
        self.category_history = [0] * 4
        self.parameter_history = [0] * 3
        self.strictness_history = [0] * 2
        self.previous_action = None
        self.previous_cwe = None
        self.consecutive_same_category = 0
        self.total_reward = 0.0
        
        # Build initial observation
        observation = self._build_observation()
        info = {}
        
        return observation, info
    
    def step(self, action: np.ndarray) ->Tuple[np.ndarray, float, bool, bool, Dict]:
        """
        Execute one step in the environment.
        
        Args:
            action: MultiDiscrete action [category, parameter, strictness]
        
        Returns:
            observation: Next observation (30,) array
            reward: Reward for this step
            terminated: Whether episode is complete
            truncated: Whether episode was truncated (always False)
            info: Dictionary with step metadata
        """
        # Parse action components
        category = int(action[0])
        parameter = int(action[1])
        strictness = int(action[2])
        
        # Get current weak state
        current_state = self.weak_states[self.current_step]
        state_name = current_state["state_name"]
        risk_score = current_state["risk_score"]
        cwe = current_state["cwe"]
        features = current_state["features"]
        
        # Compute reward for this action
        reward = self._compute_reward(category, parameter, strictness, risk_score, cwe)
        self.total_reward += reward
        
        # Update fix history
        self.category_history[category] = 1
        self.parameter_history[parameter] = 1
        self.strictness_history[strictness] = 1
        
        # Update consecutive category counter
        if self.previous_action is not None and category == self.previous_action[0]:
            self.consecutive_same_category += 1
        else:
            self.consecutive_same_category = 1
        
        # Store previous state for sequential coherence
        self.previous_action = action.copy()
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
        fallback = "RESET" if strictness == 1 else "IDLE"
        info = {
            "state_name": state_name,
            "action_taken": action.tolist(),
            "reward": reward,
            "cwe": cwe,
            "risk_score": risk_score,
            "fix_correct": reward >= 10.0,
            "total_reward": self.total_reward,
            "fix_category": category,
            "fix_parameter": parameter,
            "fix_strictness": strictness,
            "fix_spec": {
                "category": CATEGORY_NAMES[category],
                "parameter": PARAMETER_NAMES[category][parameter],
                "strictness": STRICTNESS_NAMES[strictness],
                "fallback": fallback
            }
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
        
        # [13:17] - Category history (4 values)
        for i, used in enumerate(self.category_history):
            obs[13 + i] = float(used)
        
        # [17:20] - Parameter history (3 values)
        for i, used in enumerate(self.parameter_history):
            obs[17 + i] = float(used)
        
        # [20:22] - Strictness history (2 values)
        for i, used in enumerate(self.strictness_history):
            obs[20 + i] = float(used)
        
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
    
    def _compute_reward(self, category: int, parameter: int, strictness: int,
                       risk_score: float, cwe: str) -> float:
        """
        Compute reward based on fix decisions and state context.
        
        Reward Rules:
            1. Correct category + correct parameter: +10
            2. Correct category + wrong parameter: +4
            3. Wrong category: -5
            4. Strict mode on high risk (>=0.80): +3 bonus
            5. Soft mode on low risk (<0.50): +2 bonus
            6. Episode completion: +20 (handled in step())
        
        Args:
            category: Fix category (0-3)
            parameter: Fix parameter (0-2)
            strictness: Strictness level (0-1)
            risk_score: Vulnerability score (0-1)
            cwe: CWE label
        
        Returns:
            Computed reward value
        """
        reward = 0.0
        
        # Define correct mappings: CWE -> (category, parameters)
        correct_fixes = {
            "CWE-1245": (0, [0, 1, 2]),  # Guard Insertion: auth/lock/priv
            "CWE-1233": (1, [0, 1]),      # Transition Pruning: removal/redirect
            "CWE-1298": (2, [0, 1, 2]),   # State Re-encoding: hamming/parity/both
            "CWE-1280": (3, [0, 1, 2])    # Deadlock Trap: alert/lockdown/both
        }
        
        # Get correct fix for this CWE
        if cwe in correct_fixes:
            correct_category, correct_parameters = correct_fixes[cwe]
            
            # Rule 1 & 2 & 3: Category and parameter matching
            if category == correct_category:
                if parameter in correct_parameters:
                    reward = 10.0  # Perfect match
                else:
                    reward = 4.0   # Correct category, wrong parameter
            else:
                reward = -5.0  # Wrong category
        else:
            # Unknown CWE
            reward = -5.0
        
        # Rule 4: Strict mode bonus on high risk
        if strictness == 1 and risk_score >= 0.80:
            reward += 3.0
        
        # Rule 5: Soft mode bonus on low risk
        if strictness == 0 and risk_score < 0.50:
            reward += 2.0
        
        return reward
    
    def _decode_action(self, action: np.ndarray) -> Dict[str, str]:
        """
        Decode action array into human-readable format.
        
        Args:
            action: MultiDiscrete action [category, parameter, strictness]
        
        Returns:
            Dictionary with decoded action components
        """
        category = int(action[0])
        parameter = int(action[1])
        strictness = int(action[2])
        
        return {
            "category": CATEGORY_NAMES[category],
            "parameter": PARAMETER_NAMES[category][parameter],
            "strictness": STRICTNESS_NAMES[strictness],
            "fallback": "RESET" if strictness == 1 else "IDLE"
        }
    
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
                decoded = self._decode_action(action)
                print(f"Category:   {decoded['category']}")
                print(f"Parameter:  {decoded['parameter']}")
                print(f"Strictness: {decoded['strictness']}")
                print(f"Fallback:   {decoded['fallback']}")
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
