"""
FSMGuard - Stage 4: GNN Weak State Detection & Security Report Generation
===========================================================================

This module loads a trained GAT model, runs inference on the FSM graph,
identifies weak states, and generates comprehensive security reports.

Author: FSMGuard Team
Date: 2026-03-07
"""

import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data
import networkx as nx
from typing import Dict, List, Tuple, Any


# ============================================================================
# GAT MODEL ARCHITECTURE (EXACT SPECIFICATION)
# ============================================================================

class FSM_GAT(nn.Module):
    """
    Graph Attention Network for FSM weak state detection.
    
    Architecture:
    - Conv1: 13 → 32 features (4 attention heads)
    - Conv2: 128 → 16 features (2 attention heads)
    - Conv3: 32 → 8 features (2 attention heads)
    - Classifier: 16 → 2 classes (safe/weak)
    """
    
    def __init__(self):
        super(FSM_GAT, self).__init__()
        self.conv1 = GATConv(13, 32, heads=4, dropout=0.3)
        self.conv2 = GATConv(128, 16, heads=2, dropout=0.3)  # 32*4=128 input
        self.conv3 = GATConv(32, 8, heads=2, dropout=0.3)    # 16*2=32 input
        self.classifier = nn.Linear(16, 2)                    # 8*2=16 input
        self.dropout = nn.Dropout(0.3)
    
    def forward(self, x, edge_index, batch=None):
        """
        Forward pass through the GAT network.
        
        Args:
            x: Node features [num_nodes, 13]
            edge_index: Edge connectivity [2, num_edges]
            batch: Batch assignment (optional)
        
        Returns:
            Logits [num_nodes, 2]
        """
        # Layer 1: 13 → 128 (32*4 heads)
        x = self.conv1(x, edge_index).relu()
        x = self.dropout(x)
        
        # Layer 2: 128 → 32 (16*2 heads)
        x = self.conv2(x, edge_index).relu()
        x = self.dropout(x)
        
        # Layer 3: 32 → 16 (8*2 heads)
        x = self.conv3(x, edge_index).relu()
        x = self.dropout(x)
        
        # Classification: 16 → 2
        return self.classifier(x)


# ============================================================================
# CWE CLASSIFICATION RULES
# ============================================================================

CWE_RULES = [
    {
        "cwe": "CWE-1245",
        "label": "Improper FSM Logic",
        "check": lambda f: f[10] == 1 and f[7] == 1
    },
    {
        "cwe": "CWE-1233",
        "label": "Security Lock Not Set Before Transition",
        "check": lambda f: f[11] == 0 and f[7] == 1
    },
    {
        "cwe": "CWE-1298",
        "label": "Hardware Logic Race Condition",
        "check": lambda f: f[12] == 1
    },
    {
        "cwe": "CWE-1280",
        "label": "Access Control Check After Asset Access",
        "check": lambda f: f[5] == 0 and f[8] == 1 and f[9] == 0
    }
]

# Default CWE if no rule matches
DEFAULT_CWE = {"cwe": "CWE-1245", "label": "Improper FSM Logic"}


# ============================================================================
# FIX RECOMMENDATION MAPPING
# ============================================================================

FIX_MAP = {
    "CWE-1245": "Guard Insertion",
    "CWE-1233": "Transition Pruning",
    "CWE-1298": "State Re-encoding",
    "CWE-1280": "Deadlock Trap Injection"
}


# ============================================================================
# FEATURE DISPLAY NAMES
# ============================================================================

FEATURE_NAMES = [
    ("in_degree", "Incoming Transitions"),
    ("out_degree", "Outgoing Transitions"),
    ("self_loop", "Self Loop"),
    ("reset_distance", "Distance from Reset"),
    ("neighbor_risk", "Neighbor Risk Score"),
    ("is_terminal", "Is Terminal State"),
    ("guarded", "Transition Guarded"),
    ("privilege", "Privileged State"),
    ("auth_bypass", "Auth Bypass Possible"),
    ("auth_sequence_completed", "Auth Sequence Complete"),
    ("path_bypasses_auth", "Path Bypasses Auth"),
    ("lock_signal_asserted", "Lock Signal Asserted"),
    ("privilege_escalation", "Privilege Escalation")
]


# ============================================================================
# MODEL LOADING AND INFERENCE
# ============================================================================

def load_model(model_path="fsm_gat_best.pth"):
    """
    Load trained GAT model from file.
    
    Args:
        model_path: Path to model weights file
    
    Returns:
        Loaded FSM_GAT model in eval mode
    
    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model weights not found: {model_path}")
    
    # Initialize model
    model = FSM_GAT()
    
    # Load weights using weights_only=True for security
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu'), weights_only=True))
    
    # Set to evaluation mode
    model.eval()
    
    return model


def run_inference(model, data, threshold=0.40):
    """
    Run inference on FSM graph data.
    
    Args:
        model: Trained FSM_GAT model
        data: PyTorch Geometric Data object with x and edge_index
        threshold: Probability threshold for weak state classification
    
    Returns:
        Tuple of (weak_state_indices, risk_scores)
        - weak_state_indices: List of node indices flagged as weak
        - risk_scores: Tensor of weak class probabilities [num_nodes]
    """
    with torch.no_grad():
        # Forward pass
        logits = model(data.x, data.edge_index)
        
        # Apply softmax to get probabilities
        probs = F.softmax(logits, dim=1)
        
        # Extract weak class probability (class 1)
        risk_scores = probs[:, 1]
        
        # Apply threshold
        weak_mask = risk_scores >= threshold
        weak_state_indices = torch.where(weak_mask)[0].tolist()
    
    return weak_state_indices, risk_scores


# ============================================================================
# SECURITY ANALYSIS FUNCTIONS
# ============================================================================

def classify_cwe(features):
    """
    Classify CWE based on feature values using rule-based lookup.
    
    Args:
        features: Tensor or list of 13 feature values
    
    Returns:
        Dictionary with 'cwe' and 'label' keys
    """
    # Convert to list if tensor
    if isinstance(features, torch.Tensor):
        features = features.tolist()
    
    # Apply rules in priority order
    for rule in CWE_RULES:
        if rule["check"](features):
            return {"cwe": rule["cwe"], "label": rule["label"]}
    
    # Default CWE if no rule matches
    return DEFAULT_CWE


def compute_severity(risk_score):
    """
    Compute severity level from risk score.
    
    Args:
        risk_score: Float between 0 and 1
    
    Returns:
        String: "CRITICAL", "HIGH", or "MEDIUM"
    """
    if risk_score >= 0.80:
        return "CRITICAL"
    elif risk_score >= 0.60:
        return "HIGH"
    else:
        return "MEDIUM"


def get_fix(cwe):
    """
    Get recommended fix for a CWE.
    
    Args:
        cwe: CWE identifier string (e.g., "CWE-1245")
    
    Returns:
        Fix recommendation string
    """
    return FIX_MAP.get(cwe, "Manual Security Review Required")


def compute_attack_path(edge_index, weak_node_idx, state_names, reset_idx=0):
    """
    Compute shortest attack path from reset state to weak state.
    
    Args:
        edge_index: Edge connectivity tensor [2, num_edges]
        weak_node_idx: Index of weak state node
        state_names: List of state names
        reset_idx: Index of reset state (default: 0)
    
    Returns:
        Attack path string (e.g., "RESET → IDLE → ACCESS")
    """
    # Build NetworkX graph from edge_index
    G = nx.DiGraph()
    
    # Add nodes
    num_nodes = len(state_names)
    G.add_nodes_from(range(num_nodes))
    
    # Add edges
    edge_list = edge_index.t().tolist()
    G.add_edges_from(edge_list)
    
    # Compute shortest path
    try:
        if nx.has_path(G, reset_idx, weak_node_idx):
            path_indices = nx.shortest_path(G, source=reset_idx, target=weak_node_idx)
            path_names = [state_names[idx] for idx in path_indices]
            return " → ".join(path_names)
        else:
            return "No direct path found from reset"
    except Exception:
        return "Path computation failed"


def format_feature_value(feature_name, value):
    """
    Format feature value for display.
    
    Boolean features (0/1) are converted to YES/NO.
    Numeric features keep their values.
    
    Args:
        feature_name: Name of feature
        value: Feature value
    
    Returns:
        Formatted string
    """
    # Boolean features (0/1 → YES/NO)
    bool_features = {
        "self_loop", "is_terminal", "guarded", "privilege",
        "auth_bypass", "auth_sequence_completed", 
        "path_bypasses_auth", "lock_signal_asserted", "privilege_escalation"
    }
    
    if feature_name in bool_features:
        return "YES" if value == 1 else "NO"
    else:
        # Numeric features
        if isinstance(value, float):
            return f"{value:.2f}"
        else:
            return str(int(value))


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(weak_states_data, state_names, design_name, total_states):
    """
    Generate structured security report.
    
    Args:
        weak_states_data: List of dicts containing weak state analysis
        state_names: List of all state names
        design_name: Name of the design file
        total_states: Total number of states in FSM
    
    Returns:
        Dictionary containing complete security report
    """
    # Count severity levels
    summary = {"critical": 0, "high": 0, "medium": 0}
    
    for state_data in weak_states_data:
        severity = state_data["severity"].lower()
        if severity in summary:
            summary[severity] += 1
    
    # Build report structure
    report = {
        "design": design_name,
        "total_states": total_states,
        "weak_states_found": len(weak_states_data),
        "flagged_states": weak_states_data,
        "summary": summary
    }
    
    return report


def print_terminal_report(report):
    """
    Print human-readable security report to terminal.
    
    Args:
        report: Security report dictionary
    """
    print("\n" + "=" * 64)
    print("FSMGuard — SECURITY ANALYSIS REPORT")
    print(f"Design: {report['design']}")
    print(f"States Analyzed:   {report['total_states']}")
    print(f"Weak States Found: {report['weak_states_found']}")
    print("=" * 64)
    
    if report['weak_states_found'] == 0:
        print("\nNo weak states detected. Design appears secure.")
        print("=" * 64)
        return
    
    # Print each flagged state
    for state_data in report['flagged_states']:
        print(f"\nSTATE: {state_data['state_name']}")
        print(f"Risk Score:   {state_data['risk_score']:.2f}     Severity: {state_data['severity']}")
        print(f"CWE:          {state_data['cwe']} — {state_data['cwe_label']}")
        
        print("\nStructural Evidence:")
        features = state_data['features']
        for key, display_name in FEATURE_NAMES:
            if key in features:
                value = format_feature_value(key, features[key])
                print(f"  {display_name:28} {value}")
        
        print("\nAttack Path:")
        print(f"  {state_data['attack_path']}")
        
        print("\nRecommended Fix:")
        print(f"  {state_data['recommended_fix']}")
        
        print("\n" + "-" * 64)
    
    # Print summary
    print("\nSUMMARY")
    print(f"  Critical:  {report['summary']['critical']}")
    print(f"  High:      {report['summary']['high']}")
    print(f"  Medium:    {report['summary']['medium']}")
    print(f"  Total Weak States: {report['weak_states_found']}")
    print("=" * 64)


def save_report(report, output_path="output/stage4_report.json"):
    """
    Save security report to JSON file.
    
    Args:
        report: Security report dictionary
        output_path: Path to output JSON file
    """
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save to JSON with pretty printing
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Security report saved to: {output_path}")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def stage4_pipeline(data, state_names, design_name="FSM_Design", 
                    model_path="fsm_gat_best.pth",
                    output_path="output/stage4_report.json",
                    threshold=0.40):
    """
    Complete Stage 4 pipeline: Weak state detection and security report.
    
    Args:
        data: PyTorch Geometric Data object from Stage 3
        state_names: List of state names
        design_name: Name of the design (for report)
        model_path: Path to trained model weights
        output_path: Path to save JSON report
        threshold: Probability threshold for weak state classification
    
    Returns:
        Security report dictionary
    """
    print("=" * 70)
    print("FSMGuard - Stage 4: Security Analysis & Report Generation")
    print("=" * 70)
    
    try:
        # Step 1: Load trained model
        print(f"\n[1/5] Loading trained GAT model...")
        print(f"      Model path: {model_path}")
        model = load_model(model_path)
        print("      ✓ Model loaded successfully")
        
        # Step 2: Run inference
        print(f"\n[2/5] Running inference on FSM graph...")
        print(f"      Threshold: {threshold}")
        weak_indices, risk_scores = run_inference(model, data, threshold)
        print(f"      ✓ Detected {len(weak_indices)} weak states")
        
        # Step 3: Analyze each weak state
        print(f"\n[3/5] Analyzing weak states...")
        weak_states_data = []
        
        for idx in weak_indices:
            # Extract features for this state
            features = data.x[idx]
            risk_score = risk_scores[idx].item()
            
            # Classify CWE
            cwe_info = classify_cwe(features)
            
            # Compute severity
            severity = compute_severity(risk_score)
            
            # Get recommended fix
            fix = get_fix(cwe_info["cwe"])
            
            # Compute attack path
            attack_path = compute_attack_path(data.edge_index, idx, state_names)
            
            # Build feature dict
            features_dict = {}
            for i, (key, _) in enumerate(FEATURE_NAMES):
                features_dict[key] = features[i].item()
            
            # Compile state data
            state_data = {
                "state_name": state_names[idx],
                "risk_score": risk_score,
                "severity": severity,
                "cwe": cwe_info["cwe"],
                "cwe_label": cwe_info["label"],
                "recommended_fix": fix,
                "attack_path": attack_path,
                "features": features_dict
            }
            
            weak_states_data.append(state_data)
        
        print("      ✓ CWE classification complete")
        print("      ✓ Severity levels computed")
        print("      ✓ Attack paths identified")
        
        # Step 4: Generate report
        print(f"\n[4/5] Generating security report...")
        report = generate_report(weak_states_data, state_names, design_name, len(state_names))
        print("      ✓ Report structure created")
        
        # Step 5: Save and display report
        print(f"\n[5/5] Saving report...")
        save_report(report, output_path)
        
        # Print terminal report
        print_terminal_report(report)
        
        return report
        
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("   Please ensure the trained model file exists.")
        return None
    
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# MAIN EXECUTION (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    # This is a test stub - in practice, data comes from Stage 3
    print("Stage 4 module loaded successfully.")
    print("\nTo run Stage 4, call stage4_pipeline() with:")
    print("  - data: PyTorch Geometric Data object from Stage 3")
    print("  - state_names: List of FSM state names")
    print("  - design_name: Name of the design file")
    print("\nExample:")
    print("  report = stage4_pipeline(data, ['IDLE', 'AUTH', 'ACCESS'], 'sample_fsm')")
