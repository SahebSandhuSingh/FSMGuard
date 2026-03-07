# FSMGuard — GNN Training Pipeline

Complete pipeline for training the Graph Attention Network (GAT) model on synthetic FSM vulnerability data.

## 📋 Overview

This pipeline generates synthetic FSM datasets with known vulnerabilities and trains a GNN to detect weak states.

## 🚀 Quick Start

Run the complete pipeline:
```bash
python3 run_training_pipeline.py
```

Or run scripts individually:
```bash
python3 generate.py          # 1. Generate dataset
python3 train.py             # 2. Train model
python3 threshold_test.py    # 3. Find optimal threshold
```

## 📁 Files

### Training Scripts
- **generate.py** - Generates 20,000 synthetic FSMs with labeled vulnerabilities
- **train.py** - Trains GAT model with weighted loss and early stopping
- **threshold_test.py** - Tests 7 thresholds to find optimal precision/recall balance
- **run_training_pipeline.py** - Runs all three scripts in sequence

### Output Files
- **fsm_dataset.pt** - Training dataset (20,000 FSM graphs)
- **fsm_gat_model.pth** - Final trained model weights
- **fsm_gat_best.pth** - Best model during training (highest validation F1)

## 🔧 Dataset Generation (generate.py)

### Configuration
- **Graphs:** 20,000 synthetic FSMs
- **States per FSM:** 5-20 states
- **Weak states:** 1-3 per FSM
- **Target weak ratio:** 15-25%

### Fixed Node Roles
- **Node 0:** Reset state (always)
- **Node 1:** Auth state (always)
- **Node 2:** Lock state (always)

### Weak State Patterns

Five structural vulnerability patterns are injected:

1. **High in-degree no guard** - 4 incoming transitions
2. **Too close to reset** - Direct path from reset
3. **Self loop with high in-degree** - Self-loop + 3 incoming edges
4. **Terminal state no exit** - Dead-end state
5. **Direct path with self loop** - Reset connection + self-loop

### Features (13 per state)

**Structural (9):**
0. in_degree
1. out_degree
2. self_loop
3. reset_distance
4. neighbor_risk
5. is_terminal
6. guarded
7. privilege
8. auth_bypass

**CWE Security (4):**
9. auth_sequence_completed
10. path_bypasses_auth
11. lock_signal_asserted
12. privilege_escalation

## 🧠 Model Training (train.py)

### Architecture
```
Input: 13 features
  ↓
GATConv(13 → 32, 4 heads, dropout=0.3)
  ↓
GATConv(128 → 16, 2 heads, dropout=0.3)
  ↓
GATConv(32 → 8, 2 heads, dropout=0.3)
  ↓
Linear(16 → 2) [Safe, Weak]
```

### Training Configuration
- **Optimizer:** Adam (lr=0.001, weight_decay=1e-4)
- **Loss:** CrossEntropyLoss with class weights
  - Safe weight: 1.0
  - Weak weight: 4.0 (to handle class imbalance)
- **Batch size:** 32
- **Epochs:** 100 (with early stopping)
- **Split:** 70% train, 15% val, 15% test

### Metrics
- **Primary:** Weak F1 score (for model selection)
- **Monitored:** Precision, Recall per class

## 🎯 Threshold Testing (threshold_test.py)

Tests 7 thresholds: `[0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2]`

For each threshold, computes:
- **Precision:** How many flagged states are actually weak?
- **Recall:** How many weak states are detected?
- **F1:** Harmonic mean of precision and recall

### Security Guidance
- **Higher threshold (0.5):** Fewer false alarms, might miss vulnerabilities
- **Lower threshold (0.2):** Catches more vulnerabilities, more false alarms
- **Recommended (0.4):** Balanced approach for FSMGuard Stage 4

## 📊 Expected Results

After training on 20,000 graphs:

### Training Metrics
- **Overall Accuracy:** 60-80%
- **Weak F1:** 0.60-0.75

### Threshold 0.40 Performance
- **Weak Precision:** 0.60-0.80
- **Weak Recall:** 0.60-0.75
- **Weak F1:** 0.65-0.72

## 🧪 Testing Detection

After training, test on real FSMs:

```bash
# Test on vulnerable FSM
python3 test_vulnerable.py

# Run complete pipeline validation
python3 validate_pipeline.py

# Check individual scores
python3 check_scores.py
```

## 💡 Tips

### Improving Performance
1. **Increase dataset size** - Change `NUM_GRAPHS` in generate.py
2. **Add more patterns** - Extend `PATTERNS` list with new vulnerability types
3. **Tune hyperparameters** - Adjust learning rate, batch size, or model size
4. **Balance dataset** - Ensure weak ratio is 15-25%

### Troubleshooting
- **Low recall?** Lower the threshold (detect more, risk false alarms)
- **Low precision?** Raise the threshold (fewer false alarms, miss some)
- **Poor F1?** Regenerate dataset with better pattern diversity

## 📈 Monitoring Training

During training, watch for:
- **Loss decreasing** - Model is learning
- **F1 increasing** - Detection improving
- **Early stopping** - Prevents overfitting

## 🔄 Re-training

To retrain with new data:
```bash
rm fsm_dataset.pt fsm_gat_*.pth  # Clean up old files
python3 generate.py               # Generate new dataset
python3 train.py                  # Train fresh model
python3 threshold_test.py         # Re-test thresholds
```

## 📚 Integration with FSMGuard

The trained model integrates with Stage 4:
```python
from stage4_security_report import stage4_pipeline

report = stage4_pipeline(
    data=pyg_data,
    state_names=states,
    model_path='fsm_gat_best.pth',  # or fsm_gat_model.pth
    threshold=0.40
)
```

## ⚙️ Requirements

All scripts use these libraries:
- torch
- torch_geometric
- networkx
- numpy
- sklearn
- random
- os

## 🎓 Understanding the Pipeline

1. **Generate** creates synthetic FSMs with known vulnerabilities
2. **Train** teaches the model to recognize vulnerability patterns
3. **Threshold Test** finds the best detection sensitivity
4. **Stage 4** uses the trained model on real Verilog FSMs

The key insight: By training on synthetic data with clear patterns, the model learns structural features associated with vulnerabilities and can generalize to real hardware designs.
