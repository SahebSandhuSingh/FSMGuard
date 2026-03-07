"""
FSMGuard — Model Training Script
=================================
Trains GAT model on FSM vulnerability dataset.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch_geometric.data import DataLoader
from torch_geometric.nn import GATConv
from sklearn.metrics import classification_report, precision_recall_fscore_support
import random
import numpy as np

# Fixed seed for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# ============================================================================
# MODEL ARCHITECTURE
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
# TRAINING CONFIGURATION
# ============================================================================

CONFIG = {
    'batch_size': 32,
    'learning_rate': 0.0005,  # Lower LR for subtle patterns
    'weight_decay': 5e-5,  # Less regularization
    'epochs': 150,  # More epochs for subtle patterns
    'weak_weight': 5.0,  # Higher weight for imbalanced data
    'safe_weight': 1.0,
    'train_split': 0.70,
    'val_split': 0.15,
    'test_split': 0.15
}


# ============================================================================
# TRAINING AND EVALUATION
# ============================================================================

def train_epoch(model, loader, optimizer, criterion, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    
    for data in loader:
        data = data.to(device)
        optimizer.zero_grad()
        
        out = model(data.x, data.edge_index, data.batch)
        loss = criterion(out, data.y)
        
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * data.num_graphs
    
    return total_loss / len(loader.dataset)


def evaluate(model, loader, device):
    """Evaluate model and compute metrics."""
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for data in loader:
            data = data.to(device)
            out = model(data.x, data.edge_index, data.batch)
            pred = out.argmax(dim=1)
            
            all_preds.extend(pred.cpu().tolist())
            all_labels.extend(data.y.cpu().tolist())
    
    # Compute metrics
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average=None, zero_division=0
    )
    
    # Return metrics for weak class (index 1)
    weak_precision = precision[1] if len(precision) > 1 else 0.0
    weak_recall = recall[1] if len(recall) > 1 else 0.0
    weak_f1 = f1[1] if len(f1) > 1 else 0.0
    
    return weak_precision, weak_recall, weak_f1


# ============================================================================
# MAIN TRAINING
# ============================================================================

def main():
    """Main training function."""
    print("=" * 80)
    print("FSMGuard — Model Training")
    print("=" * 80)
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"\nDevice: {device}")
    
    # Load dataset
    print("\n[1/5] Loading dataset...")
    dataset = torch.load('fsm_dataset.pt', weights_only=False)
    print(f"      ✓ Loaded {len(dataset)} graphs")
    
    # Shuffle dataset
    random.shuffle(dataset)
    
    # Split dataset
    n_train = int(CONFIG['train_split'] * len(dataset))
    n_val = int(CONFIG['val_split'] * len(dataset))
    
    train_dataset = dataset[:n_train]
    val_dataset = dataset[n_train:n_train + n_val]
    test_dataset = dataset[n_train + n_val:]
    
    print(f"      Train: {len(train_dataset)} graphs")
    print(f"      Val:   {len(val_dataset)} graphs")
    print(f"      Test:  {len(test_dataset)} graphs")
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=CONFIG['batch_size'], 
                             shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG['batch_size'], 
                           shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=CONFIG['batch_size'], 
                            shuffle=False)
    
    # Initialize model
    print("\n[2/5] Initializing model...")
    model = FSM_GAT().to(device)
    optimizer = optim.Adam(model.parameters(), 
                          lr=CONFIG['learning_rate'],
                          weight_decay=CONFIG['weight_decay'])
    
    # Weighted loss
    class_weights = torch.tensor([CONFIG['safe_weight'], CONFIG['weak_weight']], 
                                 dtype=torch.float).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    
    print(f"      ✓ Model: GAT with 4→2→2 head attention")
    print(f"      ✓ Optimizer: Adam (lr={CONFIG['learning_rate']})")
    print(f"      ✓ Loss: Weighted CrossEntropy (weak={CONFIG['weak_weight']}, safe={CONFIG['safe_weight']})")
    
    # Training loop
    print(f"\n[3/5] Training for {CONFIG['epochs']} epochs...")
    print("-" * 80)
    
    best_f1 = 0.0
    best_epoch = 0
    patience = 25
    patience_counter = 0
    
    for epoch in range(CONFIG['epochs']):
        # Train
        train_loss = train_epoch(model, train_loader, optimizer, criterion, device)
        
        # Evaluate
        val_precision, val_recall, val_f1 = evaluate(model, val_loader, device)
        
        # Print progress every 20 epochs
        if (epoch + 1) % 20 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{CONFIG['epochs']}: "
                  f"Loss={train_loss:.4f} | "
                  f"Weak P={val_precision:.3f} R={val_recall:.3f} F1={val_f1:.3f}")
        
        # Save best model
        if val_f1 > best_f1:
            best_f1 = val_f1
            best_epoch = epoch + 1
            patience_counter = 0
            torch.save(model.state_dict(), 'fsm_gat_best.pth')
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= patience:
            print(f"\nEarly stopping at epoch {epoch+1} (no improvement for {patience} epochs)")
            break
    
    print("-" * 80)
    print(f"✓ Training complete!")
    print(f"✓ Best F1: {best_f1:.3f} at epoch {best_epoch}")
    
    # Load best model for final evaluation
    print("\n[4/5] Evaluating on test set...")
    model.load_state_dict(torch.load('fsm_gat_best.pth', 
                                     map_location=device,
                                     weights_only=True))
    model.eval()
    
    # Collect predictions
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for data in test_loader:
            data = data.to(device)
            out = model(data.x, data.edge_index, data.batch)
            pred = out.argmax(dim=1)
            
            all_preds.extend(pred.cpu().tolist())
            all_labels.extend(data.y.cpu().tolist())
    
    # Print classification report
    print("\n" + "=" * 80)
    print("Test Set Classification Report")
    print("=" * 80)
    print(classification_report(all_labels, all_preds, 
                               target_names=['Safe', 'Weak'],
                               zero_division=0))
    
    # Save final model
    print("[5/5] Saving final model...")
    torch.save(model.state_dict(), 'fsm_gat_model.pth')
    print("      ✓ Model saved to: fsm_gat_model.pth")
    print("      ✓ Best model saved to: fsm_gat_best.pth")
    
    print("\n" + "=" * 80)
    print("Training Complete!")
    print("=" * 80)
    print("\nNext step: Run 'python3 threshold_test.py' to find optimal threshold\n")


if __name__ == "__main__":
    main()
