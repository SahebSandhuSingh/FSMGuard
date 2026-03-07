#!/usr/bin/env python3
import sys
import torch
sys.path.insert(0, 'parser')
sys.path.insert(0, '..')

from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import load_model
import torch.nn.functional as F

# Load data
fsm_data = stage1_pipeline('input/vulnerable_fsm.v')
data = pipeline_stage2_stage3(fsm_data)

# Load model
model = load_model('fsm_gat_best.pth')

# Run inference
with torch.no_grad():
    logits = model(data.x, data.edge_index)
    probs = F.softmax(logits, dim=1)
    risk_scores = probs[:, 1]

print('\nRISK SCORES (threshold=0.40):')
print('=' * 60)
for i, state in enumerate(fsm_data['states']):
    score = risk_scores[i].item()
    status = 'WEAK' if score >= 0.40 else 'SAFE'
    print(f'{state:12s} Risk={score:.4f}  {status}')
print('=' * 60)
print(f'Max risk score: {risk_scores.max().item():.4f}')
print(f'Min risk score: {risk_scores.min().item():.4f}')
print(f'Mean risk score: {risk_scores.mean().item():.4f}')
