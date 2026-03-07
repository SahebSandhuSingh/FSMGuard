#!/usr/bin/env python3
"""
Quick retrain and test with realistic Verilog patterns
"""
import subprocess
import sys

print("=" * 80)
print("FSMGuard — Realistic Verilog Pattern Retraining")
print("=" * 80)
print("\nChanges made:")
print("  ✓ State count: 3-10 (realistic for hardware)")
print("  ✓ Patterns: Backdoor, auth bypass, privilege escalation, lock bypass")
print("  ✓ Structure: Sequential auth flows (RESET→AUTH→states)")
print("  ✓ Weak states: 1-2 per FSM (more realistic)")
print("  ✓ Training: 150 epochs, lower LR, early stopping")
print("=" * 80)

input("\nPress Enter to start retraining...")

# Clean old files
print("\n[1/4] Cleaning old training files...")
subprocess.run(["rm", "-f", "fsm_dataset.pt", "fsm_gat_best.pth", "fsm_gat_model.pth"], 
               capture_output=True)
print("      ✓ Removed old files")

# Generate new dataset
print("\n[2/4] Generating realistic dataset...")
result = subprocess.run([sys.executable, "generate.py"], 
                       capture_output=False)
if result.returncode != 0:
    print("❌ Dataset generation failed")
    sys.exit(1)

# Train model
print("\n[3/4] Training model...")
result = subprocess.run([sys.executable, "train.py"], 
                       capture_output=False)
if result.returncode != 0:
    print("❌ Training failed")
    sys.exit(1)

# Test on vulnerable FSM
print("\n[4/4] Testing on vulnerable FSM...")
test_code = """
import sys
sys.path.insert(0, 'parser')
sys.path.insert(0, '..')
import torch
import torch.nn.functional as F
from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import load_model

print('\\n' + '=' * 70)
print('DETECTION TEST ON VULNERABLE FSM')
print('=' * 70)

fsm_data = stage1_pipeline('input/vulnerable_fsm.v')
data = pipeline_stage2_stage3(fsm_data)
model = load_model('fsm_gat_model.pth')

with torch.no_grad():
    logits = model(data.x, data.edge_index)
    probs = F.softmax(logits, dim=1)
    risk_scores = probs[:, 1]

print('\\nState Risk Scores (Threshold=0.40):')
print('-' * 70)
detected = 0
for i, state in enumerate(fsm_data['states']):
    score = risk_scores[i].item()
    status = '🚨 WEAK' if score >= 0.40 else '✓ SAFE'
    if score >= 0.40:
        detected += 1
    print(f'{state:12s} Risk={score:.4f}  {status}')

print('-' * 70)
print(f'Detected {detected}/{len(fsm_data[\"states\"])} states as weak')
print(f'Max risk: {risk_scores.max().item():.4f}')
print(f'Mean risk: {risk_scores.mean().item():.4f}')

if risk_scores.max().item() >= 0.40:
    print('\\n✅ SUCCESS: Model now detects vulnerabilities!')
else:
    print(f'\\n⚠️ WARNING: Max risk still below threshold')
print('=' * 70)
"""

with open('_test_detection.py', 'w') as f:
    f.write(test_code)

result = subprocess.run([sys.executable, "_test_detection.py"], 
                       capture_output=False)

subprocess.run(["rm", "-f", "_test_detection.py"], capture_output=True)

print("\n" + "=" * 80)
print("✅ Retraining complete!")
print("=" * 80)
print("\nYou can now run:")
print("  python3 test_vulnerable.py")
print("  python3 validate_pipeline.py")
print("=" * 80)
