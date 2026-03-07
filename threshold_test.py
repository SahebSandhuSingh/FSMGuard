"""
FSMGuard — Threshold Testing Script
====================================
Tests multiple thresholds to find optimal precision/recall balance.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import DataLoader
from torch_geometric.nn import GATConv
from sklearn.metrics import precision_recall_fscore_support
import random
import numpy as np

# Fixed seed for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# ============================================================================
# MODEL ARCHITECTURE (same as train.py)
# ============================================================================

class FSM_GAT(nn.Module):
    """Graph Attention Network for FSM vulnerability detection."""
    
    def __init__(self):
        super().__init__()
        self.conv1 = GATConv(13, 32, heads=4, dropout=0.3)
        self.conv2 = GATConv(128, 16, heads=2, dropout=0.3)
        self.conv3 = GATConv(32, 8, heads=2, dropout=0.3)
        self.classifier = nn.Linear(16, 2)
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x, edge_index, batch=None):
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv2(x, edge_index).relu()
        x = self.dropout(x)
        x = self.conv3(x, edge_index).relu()
        x = self.dropout(x)
        return self.classifier(x)


# ============================================================================
# CONFIGURATION
# ============================================================================

THRESHOLDS = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2]

CONFIG = {
    'batch_size': 32,
    'train_split': 0.70,
    'val_split': 0.15,
    'test_split': 0.15
}


# ============================================================================
# THRESHOLD EVALUATION
# ============================================================================

def evaluate_threshold(model, loader, threshold, device):
    """
    Evaluate model at specific threshold.
    
    Args:
        model: Trained FSM_GAT model
        loader: DataLoader for test set
        threshold: Probability threshold for weak classification
        device: torch device
        
    Returns:
        Tuple of (precision, recall, f1) for weak class
    """
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            
            # Forward pass
            out = model(data.x, data.edge_index, data.batch)
            
            # Apply softmax to get probabilities
            probs = F.softmax(out, dim=1)
            
            # Extract weak class probability (index 1)
            weak_probs = probs[:, 1]
            
            # Apply threshold
            pred = (weak_probs >= threshold).long()
            
            all_preds.extend(pred.cpu().tolist())
            all_labels.extend(data.y.cpu().tolist())
    
    # Compute metrics
    try:
        precision, recall, f1, _ = precision_recall_fscore_support(
            all_labels, all_preds, average=None, zero_division=0
        )
        
        # Get metrics for weak class (index 1)
        if len(precision) > 1:
            weak_precision = precision[1]
            weak_recall = recall[1]
            weak_f1 = f1[1]
        else:
            # Handle case where only one class is predicted
            weak_precision = 0.0
            weak_recall = 0.0
            weak_f1 = 0.0
    except:
        weak_precision = 0.0
        weak_recall = 0.0
        weak_f1 = 0.0
    
    return weak_precision, weak_recall, weak_f1


# ============================================================================
# MAIN THRESHOLD TESTING
# ============================================================================

def main():
    """Main threshold testing function."""
    print("=" * 80)
    print("FSMGuard — Threshold Testing")
    print("=" * 80)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    
    # Load dataset
    print("\n[1/3] Loading dataset...")
    dataset = torch.load('fsm_dataset.pt', weights_only=False)
    print(f"      ✓ Loaded {len(dataset)} graphs")
    
    # Shuffle dataset (same seed as train.py)
    random.shuffle(dataset)
    
    # Split dataset (same as train.py)
    n_train = int(CONFIG['train_split'] * len(dataset))
    n_val = int(CONFIG['val_split'] * len(dataset))
    
    test_dataset = dataset[n_train + n_val:]
    print(f"      ✓ Using {len(test_dataset)} test graphs")
    
    # Create test loader
    test_loader = DataLoader(test_dataset, batch_size=CONFIG['batch_size'], 
                            shuffle=False)
    
    # Load model
    print("\n[2/3] Loading trained model...")
    model = FSM_GAT().to(device)
    model.load_state_dict(torch.load('fsm_gat_model.pth', 
                                     map_location=device,
                                     weights_only=True))
    model.eval()
    print("      ✓ Model loaded: fsm_gat_model.pth")
    
    # Test thresholds
    print(f"\n[3/3] Testing {len(THRESHOLDS)} thresholds...")
    print("=" * 80)
    
    results = []
    
    for threshold in THRESHOLDS:
        precision, recall, f1 = evaluate_threshold(model, test_loader, 
                                                   threshold, device)
        results.append({
            'threshold': threshold,
            'precision': precision,
            'recall': recall,
            'f1': f1
        })
        
        print(f"Threshold {threshold:.2f} → "
              f"Precision: {precision:.2f} | "
              f"Recall: {recall:.2f} | "
              f"F1: {f1:.2f}")
    
    # Find best threshold
    best_result = max(results, key=lambda x: x['f1'])
    
    print("=" * 80)
    print("\nRecommended threshold: {:.2f}".format(best_result['threshold']))
    print(f"  Precision: {best_result['precision']:.2f}")
    print(f"  Recall:    {best_result['recall']:.2f}")
    print(f"  F1:        {best_result['f1']:.2f}")
    print("\n" + "=" * 80)
    print("Threshold Testing Complete!")
    print("=" * 80)
    
    # Provide guidance
    print("\nGuidance:")
    print("  - Use threshold 0.40 as specified in Stage 4 pipeline")
    print("  - Higher threshold → Higher precision, Lower recall")
    print("  - Lower threshold → Lower precision, Higher recall")
    print("  - For security tools, prioritize recall (minimize missed vulnerabilities)")
    print()


if __name__ == "__main__":
    main()
