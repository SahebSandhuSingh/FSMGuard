"""
FSMGuard - Stage 2 & 3: Graph Construction and Feature Generation
==================================================================

This module implements the graph construction and security feature extraction
pipeline for Finite State Machine (FSM) security analysis.

Author: FSMGuard Team
Date: 2026-03-07
"""

import networkx as nx
import numpy as np
import torch
from torch_geometric.data import Data
from typing import Dict, List, Tuple, Any


def build_fsm_graph(fsm_data: Dict[str, Any]) -> Tuple[nx.DiGraph, Dict[str, int]]:
    """
    Build a directed graph from FSM data.
    
    Stage 2 - Graph Construction:
    - Creates NetworkX DiGraph from FSM states and transitions
    - Stores transition conditions as edge attributes
    - Maintains state name to node index mapping
    
    Args:
        fsm_data: Dictionary containing:
            - "states": List of state names
            - "transitions": List of dicts with "src", "dst", "condition"
            - "reset_state": Name of the reset state
    
    Returns:
        Tuple of (NetworkX DiGraph, state_to_index mapping dict)
    """
    G = nx.DiGraph()
    
    # Create mapping from state name to node index
    states = fsm_data["states"]
    node_map = {state: idx for idx, state in enumerate(states)}
    
    # Add nodes to graph
    for state in states:
        G.add_node(state)
    
    # Add edges with transition conditions as attributes
    transitions = fsm_data.get("transitions", [])
    for trans in transitions:
        src = trans["src"]
        dst = trans["dst"]
        condition = trans.get("condition", "")
        
        # Store condition as edge attribute
        G.add_edge(src, dst, condition=condition)
    
    return G, node_map


def compute_features(G: nx.DiGraph, reset_state: str) -> np.ndarray:
    """
    Compute 13 security and structural features for each FSM state.
    
    Stage 3 - Feature Generation:
    Computes structural and CWE-based security features for vulnerability detection.
    
    Features:
        Structural (9):
        1. in_degree: Number of incoming edges
        2. out_degree: Number of outgoing edges
        3. self_loop: 1 if node has self-transition
        4. reset_distance: Shortest path from reset state (-1 if unreachable)
        5. neighbor_risk: Count of neighbors with self-loops
        6. is_terminal: 1 if no outgoing edges
        7. guarded: 1 if all incoming edges have conditions
        8. privilege: 1 if state name suggests privileged access
        9. auth_bypass: 1 if reachable from reset without passing AUTH
        
        CWE Security (4):
        10. auth_sequence_completed: 1 if proper auth path exists
        11. path_bypasses_auth: 1 if can reach privileged state without AUTH
        12. lock_signal_asserted: 1 if state represents locked/error state
        13. privilege_escalation: 1 if directly transitions to privileged state
    
    Args:
        G: NetworkX DiGraph of the FSM
        reset_state: Name of the reset/initial state
    
    Returns:
        NumPy array of shape [num_states, 13]
    """
    num_states = G.number_of_nodes()
    features = np.zeros((num_states, 13), dtype=np.float32)
    
    # Create node list to maintain consistent ordering
    nodes = list(G.nodes())
    node_to_idx = {node: idx for idx, node in enumerate(nodes)}
    
    # Helper function to check if state is privileged
    def is_privileged_state(state: str) -> bool:
        """Check if state name indicates privileged access."""
        state_upper = state.upper()
        return any(keyword in state_upper for keyword in ["ACCESS", "ADMIN", "PRIV"])
    
    # Helper function to check if state is auth state
    def is_auth_state(state: str) -> bool:
        """Check if state represents authentication."""
        return "AUTH" in state.upper()
    
    # Helper function to check if state is locked
    def is_lock_state(state: str) -> bool:
        """Check if state represents locked/error state."""
        return "LOCK" in state.upper()
    
    # Precompute shortest paths from reset state
    reset_distances = {}
    if reset_state in G:
        try:
            # Compute all shortest path lengths from reset state
            reset_distances = nx.single_source_shortest_path_length(G, reset_state)
        except Exception:
            # If graph is disconnected or other issues
            reset_distances = {}
    
    # Compute features for each node
    for idx, node in enumerate(nodes):
        # Feature 1: in_degree
        features[idx, 0] = G.in_degree(node)
        
        # Feature 2: out_degree
        features[idx, 1] = G.out_degree(node)
        
        # Feature 3: self_loop
        features[idx, 2] = 1.0 if G.has_edge(node, node) else 0.0
        
        # Feature 4: reset_distance
        if node in reset_distances:
            features[idx, 3] = reset_distances[node]
        else:
            features[idx, 3] = -1.0
        
        # Feature 5: neighbor_risk (neighbors with self-loops)
        neighbor_risk = 0
        # Check predecessors and successors
        neighbors = set(G.predecessors(node)) | set(G.successors(node))
        for neighbor in neighbors:
            if G.has_edge(neighbor, neighbor):
                neighbor_risk += 1
        features[idx, 4] = neighbor_risk
        
        # Feature 6: is_terminal (no outgoing edges)
        features[idx, 5] = 1.0 if G.out_degree(node) == 0 else 0.0
        
        # Feature 7: guarded (all incoming edges have conditions)
        incoming_edges = G.in_edges(node, data=True)
        if incoming_edges:
            all_guarded = all(
                edge_data.get("condition", "") != "" 
                for _, _, edge_data in incoming_edges
            )
            features[idx, 6] = 1.0 if all_guarded else 0.0
        else:
            features[idx, 6] = 0.0
        
        # Feature 8: privilege (state name suggests privileged access)
        features[idx, 7] = 1.0 if is_privileged_state(node) else 0.0
        
        # Feature 9: auth_bypass (reachable from reset without AUTH)
        # Check if there's a path from reset to this node that doesn't go through AUTH
        auth_bypass = 0.0
        if reset_state in G and node != reset_state:
            try:
                # Check if any path exists from reset to node
                if nx.has_path(G, reset_state, node):
                    # Check if all simple paths pass through an AUTH state
                    passes_auth = False
                    try:
                        # Limit path search to avoid performance issues
                        paths = nx.all_simple_paths(G, reset_state, node, cutoff=10)
                        for path in paths:
                            # Check if this path has an AUTH state
                            if any(is_auth_state(state) for state in path):
                                passes_auth = True
                                break
                            else:
                                # Found a path without AUTH
                                auth_bypass = 1.0
                                break
                    except Exception:
                        # If path enumeration fails, use conservative estimate
                        auth_bypass = 0.0
            except Exception:
                auth_bypass = 0.0
        features[idx, 8] = auth_bypass
        
        # Feature 10: auth_sequence_completed (reset → AUTH → ACCESS path)
        auth_sequence = 0.0
        if reset_state in G:
            # Look for AUTH states and ACCESS states
            auth_states = [n for n in nodes if is_auth_state(n)]
            access_states = [n for n in nodes if is_privileged_state(n)]
            
            # Check if there's a path: reset → any_auth → any_access
            for auth_state in auth_states:
                for access_state in access_states:
                    try:
                        if (nx.has_path(G, reset_state, auth_state) and 
                            nx.has_path(G, auth_state, access_state)):
                            auth_sequence = 1.0
                            break
                    except Exception:
                        continue
                if auth_sequence == 1.0:
                    break
        features[idx, 9] = auth_sequence
        
        # Feature 11: path_bypasses_auth (reset → ACCESS without AUTH)
        path_bypass = 0.0
        if reset_state in G and is_privileged_state(node):
            try:
                if nx.has_path(G, reset_state, node):
                    # Check if any path bypasses auth
                    try:
                        paths = nx.all_simple_paths(G, reset_state, node, cutoff=10)
                        for path in paths:
                            if not any(is_auth_state(state) for state in path[1:-1]):
                                # Path bypasses auth (excluding source and target)
                                path_bypass = 1.0
                                break
                    except Exception:
                        pass
            except Exception:
                pass
        features[idx, 10] = path_bypass
        
        # Feature 12: lock_signal_asserted (state name contains LOCK)
        features[idx, 11] = 1.0 if is_lock_state(node) else 0.0
        
        # Feature 13: privilege_escalation (direct transition to privileged state)
        privilege_escalation = 0.0
        # Check if this node has an outgoing edge to a privileged state
        for successor in G.successors(node):
            if is_privileged_state(successor):
                privilege_escalation = 1.0
                break
        features[idx, 12] = privilege_escalation
    
    return features


def convert_to_pyg(
    G: nx.DiGraph, 
    feature_matrix: np.ndarray, 
    node_map: Dict[str, int]
) -> Data:
    """
    Convert NetworkX graph and features to PyTorch Geometric Data object.
    
    Args:
        G: NetworkX DiGraph
        feature_matrix: NumPy array of shape [num_states, num_features]
        node_map: Dictionary mapping state names to node indices
    
    Returns:
        PyTorch Geometric Data object with x (node features) and edge_index
    """
    # Create reverse mapping (index to state name)
    idx_to_state = {idx: state for state, idx in node_map.items()}
    
    # Build edge_index tensor [2, num_edges]
    edge_list = []
    for src, dst in G.edges():
        src_idx = node_map[src]
        dst_idx = node_map[dst]
        edge_list.append([src_idx, dst_idx])
    
    # Convert to tensor
    if edge_list:
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
    else:
        # Handle case with no edges
        edge_index = torch.empty((2, 0), dtype=torch.long)
    
    # Convert feature matrix to tensor
    x = torch.tensor(feature_matrix, dtype=torch.float32)
    
    # Create PyTorch Geometric Data object
    data = Data(x=x, edge_index=edge_index)
    
    return data


def pipeline_stage2_stage3(fsm_data: Dict[str, Any]) -> Data:
    """
    Complete pipeline for Stage 2 and Stage 3.
    
    This is the main entry point that orchestrates:
    1. Graph construction from FSM data
    2. Feature computation for all states
    3. Conversion to PyTorch Geometric format
    
    Args:
        fsm_data: Dictionary containing FSM information:
            - "states": List of state names
            - "transitions": List of transition dicts
            - "reset_state": Name of reset state
    
    Returns:
        PyTorch Geometric Data object ready for GNN processing
    
    Example:
        >>> fsm_data = {
        ...     "states": ["IDLE", "AUTH", "ACCESS"],
        ...     "transitions": [
        ...         {"src": "IDLE", "dst": "AUTH", "condition": "login"},
        ...         {"src": "AUTH", "dst": "ACCESS", "condition": "valid"}
        ...     ],
        ...     "reset_state": "IDLE"
        ... }
        >>> data = pipeline_stage2_stage3(fsm_data)
        >>> print(data.x.shape)  # [3, 13]
    """
    # Stage 2: Build graph
    G, node_map = build_fsm_graph(fsm_data)
    
    # Stage 3: Compute features
    reset_state = fsm_data.get("reset_state", "")
    feature_matrix = compute_features(G, reset_state)
    
    # Convert to PyTorch Geometric Data
    data = convert_to_pyg(G, feature_matrix, node_map)
    
    return data


# Example usage and testing
if __name__ == "__main__":
    # Test with the provided example FSM
    fsm_data = {
        "states": ["IDLE", "AUTH", "CHECK", "ACCESS", "LOCK"],
        "transitions": [
            {"src": "IDLE", "dst": "AUTH", "condition": "login_req"},
            {"src": "AUTH", "dst": "CHECK", "condition": "password_ok"},
            {"src": "CHECK", "dst": "ACCESS", "condition": "auth_valid"},
            {"src": "ACCESS", "dst": "IDLE", "condition": "logout"},
            {"src": "AUTH", "dst": "LOCK", "condition": "auth_fail"},
            {"src": "LOCK", "dst": "LOCK", "condition": "retry"}
        ],
        "reset_state": "IDLE"
    }
    
    print("=" * 70)
    print("FSMGuard - Stage 2 & 3 Pipeline Test")
    print("=" * 70)
    
    # Run the pipeline
    data = pipeline_stage2_stage3(fsm_data)
    
    print(f"\n✓ Graph Construction Complete")
    print(f"  - Number of states: {len(fsm_data['states'])}")
    print(f"  - Number of transitions: {len(fsm_data['transitions'])}")
    
    print(f"\n✓ Feature Generation Complete")
    print(f"  - Feature matrix shape: {data.x.shape}")
    print(f"  - Edge index shape: {data.edge_index.shape}")
    
    print(f"\n✓ PyTorch Geometric Data Created")
    print(f"  - Node features (x): {data.x.shape}")
    print(f"  - Edge index: {data.edge_index.shape}")
    
    print(f"\n{'State':<12} {'InDeg':<7} {'OutDeg':<7} {'SelfLoop':<9} {'ResetDist':<10} {'Terminal':<9} {'Privilege':<9} {'Lock':<6}")
    print("-" * 70)
    
    for idx, state in enumerate(fsm_data["states"]):
        in_deg = int(data.x[idx, 0])
        out_deg = int(data.x[idx, 1])
        self_loop = int(data.x[idx, 2])
        reset_dist = int(data.x[idx, 3])
        terminal = int(data.x[idx, 5])
        privilege = int(data.x[idx, 7])
        lock = int(data.x[idx, 11])
        
        print(f"{state:<12} {in_deg:<7} {out_deg:<7} {self_loop:<9} {reset_dist:<10} {terminal:<9} {privilege:<9} {lock:<6}")
    
    print("\n" + "=" * 70)
    print("Pipeline execution successful!")
    print("=" * 70)
