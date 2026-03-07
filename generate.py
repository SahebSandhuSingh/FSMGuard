"""
FSMGuard — Dataset Generation Script
=====================================
Generates 20,000 synthetic FSM graphs with labeled weak and safe states.
"""
import torch
from torch_geometric.data import Data
import networkx as nx
import numpy as np
import random
import os

# Fixed seed for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

# ============================================================================
# CONFIGURATION
# ============================================================================

NUM_GRAPHS = 20000
MIN_STATES = 3
MAX_STATES = 10  # Realistic Verilog FSMs are smaller
MIN_WEAK_STATES = 1
MAX_WEAK_STATES = 2  # Fewer weak states per FSM

# Fixed node roles
RESET_NODE = 0
AUTH_NODE = 1
LOCK_NODE = 2

# ============================================================================
# WEAK PATTERN INJECTION - VERILOG-REALISTIC
# ============================================================================

def inject_pattern_1(G, weak_node, num_states):
    """Pattern 1: Backdoor to privileged state - Direct path from RESET."""
    # Add direct edge from reset to this privileged state
    G.add_edge(RESET_NODE, weak_node)
    # Make it a self-loop to simulate stuck privilege
    G.add_edge(weak_node, weak_node)


def inject_pattern_2(G, weak_node):
    """Pattern 2: Authentication bypass - Skip AUTH node from RESET."""
    # Create path that bypasses authentication
    G.add_edge(RESET_NODE, weak_node)


def inject_pattern_3(G, weak_node, num_states):
    """Pattern 3: Privilege escalation - Add edges from multiple states."""
    # Multiple paths lead to privileged state (similar to USER->ADMIN)
    candidates = [n for n in range(num_states) if n != weak_node and n != RESET_NODE]
    if len(candidates) >= 2:
        sources = random.sample(candidates, min(2, len(candidates)))
        for src in sources:
            G.add_edge(src, weak_node)


def inject_pattern_4(G, weak_node):
    """Pattern 4: Lock bypass - Remove lock signal protection."""
    # Remove edges from LOCK_NODE to break lock mechanism
    edges_to_remove = [(LOCK_NODE, weak_node)]
    for edge in edges_to_remove:
        if G.has_edge(edge[0], edge[1]):
            G.remove_edge(edge[0], edge[1])
    # Add bypass path
    G.add_edge(RESET_NODE, weak_node)


def inject_pattern_5(G, weak_node):
    """Pattern 5: Infinite privilege loop - Self-loop in privileged state."""
    # Create self-loop (stuck in privileged state forever)
    G.add_edge(weak_node, weak_node)
    # Ensure it's reachable without proper auth
    if not G.has_edge(RESET_NODE, weak_node):
        # Add path through non-auth node
        candidates = [n for n in G.nodes() if n not in [RESET_NODE, AUTH_NODE, weak_node]]
        if candidates:
            intermediate = random.choice(candidates)
            G.add_edge(RESET_NODE, intermediate)
            G.add_edge(intermediate, weak_node)


# ============================================================================
# FEATURE COMPUTATION
# ============================================================================

def compute_features(G, num_states):
    """
    Compute 13 features for each state.
    
    Args:
        G: NetworkX DiGraph
        num_states: Number of states
        
    Returns:
        Tensor of shape [num_states, 13]
    """
    features = torch.zeros((num_states, 13), dtype=torch.float)
    
    # Compute shortest paths from reset node once
    try:
        distances = nx.single_source_shortest_path_length(G, RESET_NODE)
    except:
        distances = {}
    
    for node in range(num_states):
        # Feature 0: in_degree
        features[node, 0] = G.in_degree(node)
        
        # Feature 1: out_degree
        features[node, 1] = G.out_degree(node)
        
        # Feature 2: self_loop
        features[node, 2] = 1.0 if G.has_edge(node, node) else 0.0
        
        # Feature 3: reset_distance
        features[node, 3] = distances.get(node, -1)
        
        # Feature 4: neighbor_risk (mean in_degree of predecessors)
        predecessors = list(G.predecessors(node))
        if predecessors:
            neighbor_risk = np.mean([G.in_degree(p) for p in predecessors])
            features[node, 4] = neighbor_risk
        else:
            features[node, 4] = 0.0
        
        # Feature 5: is_terminal
        features[node, 5] = 1.0 if G.out_degree(node) == 0 else 0.0
        
        # Feature 6: guarded (multiple exit paths)
        features[node, 6] = 1.0 if G.out_degree(node) > 1 else 0.0
        
        # Feature 7: privilege
        is_terminal = (G.out_degree(node) == 0)
        high_indegree = (G.in_degree(node) >= 4)
        features[node, 7] = 1.0 if (is_terminal or high_indegree) else 0.0
        
        # Feature 8: auth_bypass (reset_distance <= 1)
        features[node, 8] = 1.0 if features[node, 3] <= 1 else 0.0
        
        # Feature 9: auth_sequence_completed
        # Check if any path from RESET_NODE to this node passes through AUTH_NODE
        auth_sequence = 0.0
        if node != RESET_NODE and nx.has_path(G, RESET_NODE, node):
            try:
                paths = nx.all_simple_paths(G, RESET_NODE, node, cutoff=6)
                for path in paths:
                    if AUTH_NODE in path:
                        auth_sequence = 1.0
                        break
            except:
                pass
        features[node, 9] = auth_sequence
        
        # Feature 10: path_bypasses_auth
        # Check if any path from RESET_NODE to this node does NOT pass through AUTH_NODE
        path_bypass = 0.0
        if node != RESET_NODE and nx.has_path(G, RESET_NODE, node):
            try:
                paths = nx.all_simple_paths(G, RESET_NODE, node, cutoff=5)
                for path in paths:
                    if AUTH_NODE not in path:
                        path_bypass = 1.0
                        break
            except:
                pass
        features[node, 10] = path_bypass
        
        # Feature 11: lock_signal_asserted
        # Check if LOCK_NODE has direct edge to this node
        features[node, 11] = 1.0 if G.has_edge(LOCK_NODE, node) else 0.0
        
        # Feature 12: privilege_escalation
        privilege = features[node, 7].item()
        bypass = features[node, 10].item()
        features[node, 12] = 1.0 if (privilege == 1.0 and bypass == 1.0) else 0.0
    
    return features


# ============================================================================
# FSM GENERATION
# ============================================================================

def generate_fsm():
    """
    Generate one synthetic FSM with weak states.
    Creates Verilog-realistic FSM patterns.
    
    Returns:
        PyTorch Geometric Data object
    """
    # Random number of states (smaller, more realistic)
    num_states = random.randint(MIN_STATES, MAX_STATES)
    
    # Create directed graph
    G = nx.DiGraph()
    G.add_nodes_from(range(num_states))
    
    # Create a more realistic FSM structure (sequential flow)
    # Build authentication-like flow: RESET -> AUTH -> intermediate states
    
    # Core authentication path: 0 -> 1 -> ...
    if num_states >= 2:
        G.add_edge(RESET_NODE, AUTH_NODE)
    
    # Add transitions from AUTH to other states
    if num_states > 2:
        for node in range(2, min(num_states, 5)):
            if random.random() > 0.3:  # 70% chance
                G.add_edge(AUTH_NODE, node)
    
    # Add random transitions between states (1-2 per state)
    for node in range(num_states):
        if G.out_degree(node) == 0:  # If no outgoing edges yet
            num_transitions = random.randint(1, 2)
            targets = random.sample(range(num_states), 
                                  min(num_transitions, num_states))
            for target in targets:
                if node != target or random.random() > 0.8:  # Rare self-loops
                    G.add_edge(node, target)
    
    # Ensure LOCK_NODE has some edges for lock_signal feature
    if num_states > 3 and G.out_degree(LOCK_NODE) < 2:
        targets = random.sample(range(num_states), 
                              min(2, num_states))
        for target in targets:
            if target != LOCK_NODE:
                G.add_edge(LOCK_NODE, target)
    
    # Ensure reset node has at least one outgoing edge
    if G.out_degree(RESET_NODE) == 0:
        target = random.choice([n for n in range(num_states) if n != RESET_NODE])
        G.add_edge(RESET_NODE, target)
    
    # Select weak states (excluding fixed role nodes initially)
    num_weak = random.randint(MIN_WEAK_STATES, MAX_WEAK_STATES)
    candidates = [n for n in range(3, num_states)]  # Exclude 0, 1, 2
    
    if len(candidates) < num_weak:
        # Can also mark role nodes as weak
        candidates = [n for n in range(num_states)]
        num_weak = min(num_weak, len(candidates))
    
    if num_weak > 0 and candidates:
        weak_states = random.sample(candidates, min(num_weak, len(candidates)))
    else:
        weak_states = []
    
    # Inject weak patterns
    for weak_node in weak_states:
        pattern_idx = random.randint(0, 4)
        if pattern_idx == 0:
            inject_pattern_1(G, weak_node, num_states)
        elif pattern_idx == 1:
            inject_pattern_2(G, weak_node)
        elif pattern_idx == 2:
            inject_pattern_3(G, weak_node, num_states)
        elif pattern_idx == 3:
            inject_pattern_4(G, weak_node)
        else:
            inject_pattern_5(G, weak_node)
    
    # Compute features
    features = compute_features(G, num_states)
    
    # Create edge index
    if G.number_of_edges() > 0:
        edge_list = list(G.edges())
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.zeros((2, 0), dtype=torch.long)
    
    # Create labels
    labels = torch.zeros(num_states, dtype=torch.long)
    for weak_node in weak_states:
        labels[weak_node] = 1
    
    # Create Data object
    data = Data(x=features, edge_index=edge_index, y=labels)
    
    return data


# ============================================================================
# MAIN GENERATION
# ============================================================================

def main():
    """Generate dataset and save to file."""
    print("=" * 80)
    print("FSMGuard — Dataset Generation")
    print("=" * 80)
    print(f"\nGenerating {NUM_GRAPHS} synthetic FSM graphs...")
    print(f"States per FSM: {MIN_STATES} to {MAX_STATES}")
    print(f"Weak states per FSM: {MIN_WEAK_STATES} to {MAX_WEAK_STATES}")
    print(f"Features per state: 13")
    print(f"Fixed roles: Node 0=RESET, Node 1=AUTH, Node 2=LOCK\n")
    
    dataset = []
    total_weak = 0
    total_safe = 0
    
    for i in range(NUM_GRAPHS):
        data = generate_fsm()
        dataset.append(data)
        
        # Count weak and safe states
        weak_count = (data.y == 1).sum().item()
        safe_count = (data.y == 0).sum().item()
        total_weak += weak_count
        total_safe += safe_count
        
        # Progress indicator
        if (i + 1) % 2000 == 0:
            print(f"  Generated {i + 1}/{NUM_GRAPHS} graphs...")
    
    # Save dataset
    print(f"\n✓ Generated {NUM_GRAPHS} graphs")
    print(f"\nSaving to fsm_dataset.pt...")
    torch.save(dataset, 'fsm_dataset.pt')
    print("✓ Dataset saved")
    
    # Statistics
    total_states = total_weak + total_safe
    weak_ratio = (total_weak / total_states) * 100 if total_states > 0 else 0
    
    print("\n" + "=" * 80)
    print("Dataset Statistics")
    print("=" * 80)
    print(f"Total graphs: {NUM_GRAPHS}")
    print(f"Weak states:  {total_weak}")
    print(f"Safe states:  {total_safe}")
    print(f"Weak ratio:   {weak_ratio:.2f}%")
    print("=" * 80)
    
    if 15 <= weak_ratio <= 25:
        print("✓ Weak ratio within target range (15-25%)")
    else:
        print(f"⚠ Weak ratio outside target range (15-25%)")
    
    print("\nNext step: Run 'python3 train.py' to train the model\n")


if __name__ == "__main__":
    main()
