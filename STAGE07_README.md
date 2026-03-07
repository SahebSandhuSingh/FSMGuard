# FSMGuard Stage 07 - PPO Agent Training

## Overview

Stage 07 implements a **Proximal Policy Optimization (PPO)** reinforcement learning agent that learns optimal hardware security fix strategies for FSM vulnerabilities detected in earlier stages.

## Files Created

### Training Scripts
- **`train_agent.py`** - Full training (200K timesteps)
- **`demo_training.py`** - Quick demo training (5K timesteps)  
- **`test_training.py`** - Quick validation test (1K timesteps)

### Evaluation Script
- **`evaluate_agent.py`** - Evaluate trained agent performance

### Support Files
- **`fsm_env.py`** (Stage 06) - Gymnasium environment
- **`verify_sb3.py`** - SB3 compatibility verification

## Quick Start

### 1. Test Setup (1 minute)
```bash
python3 test_training.py
```
Verifies everything is configured correctly.

### 2. Demo Training (2-3 minutes)
```bash
python3 demo_training.py
```
Runs short 5K step training to demonstrate the pipeline.

### 3. Full Training (15-30 minutes)
```bash
python3 train_agent.py
```
Trains agent for 200K timesteps to learn optimal policy.

### 4. Evaluate Agent
```bash
python3 evaluate_agent.py
```
Runs 10 test episodes and shows detailed statistics.

To evaluate best model:
```bash
python3 evaluate_agent.py --best
```

## What the Agent Learns

The agent learns to map **CWE vulnerability types** to **appropriate hardware fixes**:

| CWE Type | Optimal Fix Category | Actions |
|----------|---------------------|---------|
| CWE-1245 | Guard Insertion | 0, 1, 2 |
| CWE-1233 | Transition Pruning | 3, 4 |
| CWE-1298 | State Re-encoding | 5, 6 |
| CWE-1280 | Deadlock Trap | 7, 8 |

## Training Progress

Expected learning curve over 200K steps:

- **0-50K**: Random exploration, ~30-40% accuracy
- **50K-150K**: Learning mappings, ~60-70% accuracy  
- **150K-200K**: Convergence, ~80-90% accuracy

## Model Architecture

**Policy Network (π)**: 30 → 128 → 128 → 64 → 9
- Input: 30-dim observation
- Hidden: 3 layers [128, 128, 64]
- Output: 9 action probabilities

**Value Network (V)**: 30 → 128 → 128 → 64 → 1
- Input: 30-dim observation  
- Hidden: 3 layers [128, 128, 64]
- Output: State value estimate

## Output Files

After training:
- **`fsm_ppo_agent.zip`** - Final trained model
- **`models/fsm_ppo_best.zip`** - Best model during training
- **`logs/`** - TensorBoard logs

## Hyperparameters

```python
learning_rate = 3e-4      # Adam optimizer learning rate
n_steps = 2048            # Steps per rollout
batch_size = 64           # Minibatch size
n_epochs = 10             # Optimization epochs per update
gamma = 0.99              # Discount factor
gae_lambda = 0.95         # GAE parameter
clip_range = 0.2          # PPO clip range
```

## Integration with Pipeline

Stage 07 output is used by Stage 08:

```python
# Stage 08 patch generation
from stable_baselines3 import PPO

model = PPO.load("fsm_ppo_agent")
obs = build_observation(weak_state)
action, _ = model.predict(obs)
patch = apply_fix(action, fsm_graph)
```

## Monitoring Training

View real-time training metrics:
```bash
tensorboard --logdir=./logs/
```

Then open http://localhost:6006 in your browser.

## Expected Results

After 200K training steps, the agent should:
- ✅ Select correct fix category for each CWE >85% of time
- ✅ Achieve average episode reward >50
- ✅ Maintain sequential coherence (same fixes for same CWEs)
- ✅ Avoid repetitive action patterns

## Troubleshooting

**Issue**: Training is slow
- **Solution**: Reduce n_steps or total_timesteps for testing

**Issue**: Low accuracy after training  
- **Solution**: Train longer (>200K steps) or adjust learning_rate

**Issue**: Agent always picks same action
- **Solution**: Increase entropy coefficient or use diverse training data

**Issue**: Environment check fails
- **Solution**: Run `python3 verify_sb3.py` to diagnose

## Dependencies

```bash
pip3 install stable-baselines3 gymnasium torch numpy
```

## Next Steps

After Stage 07 training:
1. Run evaluation to verify agent learned correctly
2. Proceed to Stage 08 (Patch Generation)
3. Integrate trained model into full FSMGuard pipeline

---

**Author**: FSMGuard Team  
**Date**: March 7, 2026  
**Stage**: 07 - RL Agent Training (PPO)
