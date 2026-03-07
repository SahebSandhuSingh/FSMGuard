"""
FSMGuard - Model Training Pipeline
===================================

Trains the GAT model on labeled FSM vulnerability data.
Creates synthetic training data with known vulnerabilities.
"""
import torch
import torch.nn.functional as F
import torch.optim as optim
from torch_geometric.data import Data, DataLoader
import numpy as np
import sys
import os

sys.path.insert(0, 'parser')
sys.path.insert(0, '..')

from parse_verilog_v2 import stage1_pipeline
from fsmguard_pipeline import pipeline_stage2_stage3
from stage4_security_report import FSM_GAT

# ============================================================================
# TRAINING CONFIGURATION
# ============================================================================

CONFIG = {
    'learning_rate': 0.001,
    'epochs': 100,
    'batch_size': 1,  # Process one FSM at a time
    'hidden_dim': 32,
    'weight_decay': 5e-4,
    'model_save_path': 'fsm_gat_best.pth',
    'patience': 15  # Early stopping patience
}

# ============================================================================
# SYNTHETIC FSM TRAINING DATA GENERATOR
# ============================================================================

def generate_training_data():
    """
    Generate labeled training data from Verilog FSMs.
    
    Returns:
        List of (data, labels) tuples where:
        - data: PyTorch Geometric Data object
        - labels: Tensor of ground truth labels [num_states]
    """
    training_samples = []
    
    # Sample 1: Secure authentication FSM
    verilog_secure = """
module secure_fsm(
    input clk, reset, login, auth_ok, logout,
    output reg access
);
    reg [1:0] state;
    localparam IDLE = 2'b00, AUTH = 2'b01, ACCESS = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(login) state <= AUTH;
            AUTH: if(auth_ok) state <= ACCESS; else state <= IDLE;
            ACCESS: if(logout) state <= IDLE;
        endcase
    end
    always @(state) access = (state == ACCESS);
endmodule
"""
    data_secure = create_data_from_verilog(verilog_secure, "secure")
    # All states are secure (label 0)
    labels_secure = torch.tensor([0, 0, 0], dtype=torch.long)
    training_samples.append((data_secure, labels_secure))
    
    # Sample 2: Vulnerable FSM with backdoor
    verilog_backdoor = """
module backdoor_fsm(
    input clk, reset, login, backdoor, logout,
    output reg access
);
    reg [1:0] state;
    localparam IDLE = 2'b00, AUTH = 2'b01, ADMIN = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(backdoor) state <= ADMIN; else if(login) state <= AUTH;
            AUTH: if(login) state <= ADMIN; else state <= IDLE;
            ADMIN: state <= ADMIN;
        endcase
    end
    always @(state) access = (state == ADMIN);
endmodule
"""
    data_backdoor = create_data_from_verilog(verilog_backdoor, "backdoor")
    # IDLE is weak (backdoor), ADMIN is weak (self-loop + bypass)
    labels_backdoor = torch.tensor([1, 0, 1], dtype=torch.long)
    training_samples.append((data_backdoor, labels_backdoor))
    
    # Sample 3: Privilege escalation vulnerability
    verilog_escalation = """
module escalation_fsm(
    input clk, reset, user_login, escalate,
    output reg admin
);
    reg [1:0] state;
    localparam IDLE = 2'b00, USER = 2'b01, ADMIN = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(user_login) state <= USER;
            USER: if(escalate) state <= ADMIN; else state <= IDLE;
            ADMIN: state <= IDLE;
        endcase
    end
    always @(state) admin = (state == ADMIN);
endmodule
"""
    data_escalation = create_data_from_verilog(verilog_escalation, "escalation")
    # USER is weak (privilege escalation), ADMIN is weak (no auth)
    labels_escalation = torch.tensor([0, 1, 1], dtype=torch.long)
    training_samples.append((data_escalation, labels_escalation))
    
    # Sample 4: Lock state bypass
    verilog_lock_bypass = """
module lock_bypass_fsm(
    input clk, reset, attempt, fail, bypass,
    output reg locked
);
    reg [1:0] state;
    localparam IDLE = 2'b00, CHECK = 2'b01, LOCK = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(attempt) state <= CHECK;
            CHECK: if(fail) state <= LOCK; else if(bypass) state <= IDLE;
            LOCK: state <= LOCK;
        endcase
    end
    always @(state) locked = (state == LOCK);
endmodule
"""
    data_lock = create_data_from_verilog(verilog_lock_bypass, "lock_bypass")
    # CHECK is weak (bypass exists), LOCK is weak (stuck forever)
    labels_lock = torch.tensor([0, 1, 1], dtype=torch.long)
    training_samples.append((data_lock, labels_lock))
    
    # Sample 5: Multi-vulnerability FSM (complex)
    verilog_complex = """
module complex_vuln_fsm(
    input clk, reset, req, auth, backdoor, priv,
    output reg access
);
    reg [2:0] state;
    localparam IDLE=3'b000, AUTH=3'b001, USER=3'b010, ADMIN=3'b011, LOCK=3'b100;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(backdoor) state <= ADMIN; else if(req) state <= AUTH;
            AUTH: if(auth) state <= USER; else state <= LOCK;
            USER: if(priv) state <= ADMIN; else state <= IDLE;
            ADMIN: state <= ADMIN;
            LOCK: state <= IDLE;
        endcase
    end
    always @(state) access = (state == ADMIN);
endmodule
"""
    data_complex = create_data_from_verilog(verilog_complex, "complex")
    # IDLE weak (backdoor), USER weak (escalation), ADMIN weak (all issues)
    labels_complex = torch.tensor([1, 0, 1, 1, 0], dtype=torch.long)
    training_samples.append((data_complex, labels_complex))
    
    # Sample 6: Secure FSM with proper locking
    verilog_secure_lock = """
module secure_lock_fsm(
    input clk, reset, login, pass_ok, admin_key, logout,
    output reg admin
);
    reg [2:0] state;
    localparam IDLE=3'b000, LOGIN=3'b001, CHECK=3'b010, USER=3'b011, ADMIN=3'b100;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(login) state <= LOGIN;
            LOGIN: if(pass_ok) state <= CHECK;
            CHECK: if(admin_key) state <= ADMIN; else state <= USER;
            USER: if(logout) state <= IDLE;
            ADMIN: if(logout) state <= IDLE;
        endcase
    end
    always @(state) admin = (state == ADMIN);
endmodule
"""
    data_secure_lock = create_data_from_verilog(verilog_secure_lock, "secure_lock")
    # All secure - proper auth flow
    labels_secure_lock = torch.tensor([0, 0, 0, 0, 0], dtype=torch.long)
    training_samples.append((data_secure_lock, labels_secure_lock))
    
    # Sample 7: Self-loop vulnerability
    verilog_selfloop = """
module selfloop_fsm(
    input clk, reset, start, stop,
    output reg running
);
    reg [1:0] state;
    localparam IDLE = 2'b00, ACTIVE = 2'b01, STUCK = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(start) state <= ACTIVE;
            ACTIVE: if(stop) state <= STUCK;
            STUCK: state <= STUCK;
        endcase
    end
    always @(state) running = (state != IDLE);
endmodule
"""
    data_selfloop = create_data_from_verilog(verilog_selfloop, "selfloop")
    # STUCK is weak (permanent self-loop)
    labels_selfloop = torch.tensor([0, 0, 1], dtype=torch.long)
    training_samples.append((data_selfloop, labels_selfloop))
    
    # Sample 8: Auth bypass vulnerability
    verilog_auth_bypass = """
module auth_bypass_fsm(
    input clk, reset, direct, auth, verify,
    output reg access
);
    reg [1:0] state;
    localparam IDLE = 2'b00, AUTH = 2'b01, ACCESS = 2'b10;
    
    always @(posedge clk or posedge reset) begin
        if(reset) state <= IDLE;
        else case(state)
            IDLE: if(direct) state <= ACCESS; else if(auth) state <= AUTH;
            AUTH: if(verify) state <= ACCESS;
            ACCESS: state <= IDLE;
        endcase
    end
    always @(state) access = (state == ACCESS);
endmodule
"""
    data_auth_bypass = create_data_from_verilog(verilog_auth_bypass, "auth_bypass")
    # IDLE weak (bypass to ACCESS), ACCESS weak (no auth required)
    labels_auth_bypass = torch.tensor([1, 0, 1], dtype=torch.long)
    training_samples.append((data_auth_bypass, labels_auth_bypass))
    
    return training_samples


def create_data_from_verilog(verilog_code, name):
    """
    Create PyG Data object from Verilog code string.
    
    Args:
        verilog_code: Verilog module as string
        name: Module name for temp file
        
    Returns:
        PyTorch Geometric Data object
    """
    # Write to temp file
    temp_file = f'input/temp_{name}.v'
    os.makedirs('input', exist_ok=True)
    with open(temp_file, 'w') as f:
        f.write(verilog_code)
    
    # Parse and extract features
    fsm_data = stage1_pipeline(temp_file)
    data = pipeline_stage2_stage3(fsm_data)
    
    # Clean up temp file
    os.remove(temp_file)
    
    return data


# ============================================================================
# TRAINING LOOP
# ============================================================================

def train_epoch(model, train_data, optimizer):
    """
    Train for one epoch.
    
    Args:
        model: FSM_GAT model
        train_data: List of (data, labels) tuples
        optimizer: Optimizer
        
    Returns:
        Average loss for the epoch
    """
    model.train()
    total_loss = 0
    total_correct = 0
    total_samples = 0
    
    for data, labels in train_data:
        optimizer.zero_grad()
        
        # Forward pass
        out = model(data.x, data.edge_index)
        
        # Compute loss
        loss = F.cross_entropy(out, labels)
        
        # Backward pass
        loss.backward()
        optimizer.step()
        
        # Track metrics
        total_loss += loss.item()
        pred = out.argmax(dim=1)
        total_correct += (pred == labels).sum().item()
        total_samples += labels.size(0)
    
    avg_loss = total_loss / len(train_data)
    accuracy = total_correct / total_samples
    
    return avg_loss, accuracy


def evaluate(model, test_data):
    """
    Evaluate model on test data.
    
    Args:
        model: FSM_GAT model
        test_data: List of (data, labels) tuples
        
    Returns:
        Average loss and accuracy
    """
    model.eval()
    total_loss = 0
    total_correct = 0
    total_samples = 0
    
    with torch.no_grad():
        for data, labels in test_data:
            out = model(data.x, data.edge_index)
            loss = F.cross_entropy(out, labels)
            
            total_loss += loss.item()
            pred = out.argmax(dim=1)
            total_correct += (pred == labels).sum().item()
            total_samples += labels.size(0)
    
    avg_loss = total_loss / len(test_data)
    accuracy = total_correct / total_samples
    
    return avg_loss, accuracy


# ============================================================================
# MAIN TRAINING FUNCTION
# ============================================================================

def train_model():
    """
    Main training function.
    Train GAT model on synthetic FSM vulnerability data.
    """
    print("=" * 80)
    print("FSMGuard - Model Training Pipeline")
    print("=" * 80)
    
    # Generate training data
    print("\n[1/4] Generating training data...")
    training_data = generate_training_data()
    print(f"      ✓ Generated {len(training_data)} FSM samples")
    
    # Split into train/val (80/20)
    split_idx = int(0.8 * len(training_data))
    train_data = training_data[:split_idx]
    val_data = training_data[split_idx:]
    print(f"      ✓ Train: {len(train_data)} samples, Val: {len(val_data)} samples")
    
    # Initialize model
    print("\n[2/4] Initializing model...")
    model = FSM_GAT()
    optimizer = optim.Adam(model.parameters(), 
                          lr=CONFIG['learning_rate'],
                          weight_decay=CONFIG['weight_decay'])
    print(f"      ✓ Model architecture: GAT with 3 layers")
    print(f"      ✓ Learning rate: {CONFIG['learning_rate']}")
    
    # Training loop
    print(f"\n[3/4] Training for {CONFIG['epochs']} epochs...")
    print("-" * 80)
    
    best_val_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(CONFIG['epochs']):
        train_loss, train_acc = train_epoch(model, train_data, optimizer)
        val_loss, val_acc = evaluate(model, val_data)
        
        # Print progress every 10 epochs
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{CONFIG['epochs']}: "
                  f"Train Loss={train_loss:.4f} Acc={train_acc:.3f} | "
                  f"Val Loss={val_loss:.4f} Acc={val_acc:.3f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), CONFIG['model_save_path'])
            patience_counter = 0
        else:
            patience_counter += 1
        
        # Early stopping
        if patience_counter >= CONFIG['patience']:
            print(f"\nEarly stopping at epoch {epoch+1}")
            break
    
    print("-" * 80)
    print(f"✓ Training complete!")
    print(f"✓ Best validation loss: {best_val_loss:.4f}")
    
    # Save final model
    print(f"\n[4/4] Saving trained model...")
    torch.save(model.state_dict(), CONFIG['model_save_path'])
    print(f"      ✓ Model saved to: {CONFIG['model_save_path']}")
    
    # Test on all data
    print("\n" + "=" * 80)
    print("Final Model Evaluation")
    print("=" * 80)
    
    model.load_state_dict(torch.load(CONFIG['model_save_path'], 
                                     map_location=torch.device('cpu'),
                                     weights_only=True))
    final_loss, final_acc = evaluate(model, training_data)
    
    print(f"Overall Accuracy: {final_acc:.1%}")
    print(f"Overall Loss: {final_loss:.4f}")
    print("=" * 80)
    
    return model


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n🚀 Starting FSMGuard model training...\n")
    
    # Ensure directories exist
    os.makedirs('input', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    
    # Train model
    trained_model = train_model()
    
    print("\n✅ Training complete! Model ready for use.")
    print(f"   Run 'python3 test_vulnerable.py' to test detection.\n")
