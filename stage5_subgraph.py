"""
FSMGuard - Stage 5: Subgraph Isolation
======================================

Extracts local neighborhoods around weak states flagged by Stage 04.
Each weak state's immediate predecessors and successors are isolated
to create focused subgraphs for Stage 06 RL environment.

Author: FSMGuard Team
Date: 2026-03-07
"""

import networkx as nx
import json
import os
from typing import Dict, List, Any, Tuple


def extract_subgraph(G: nx.DiGraph, weak_state_name: str) -> Dict[str, List[str]]:
    """
    Extract 1-hop neighborhood around a weak state.
    
    Extracts:
      - All states with edges INTO the weak state (predecessors)
      - All states the weak state transitions OUT to (successors)
    
    Args:
        G: Full NetworkX DiGraph of FSM (with state names as nodes)
        weak_state_name: Name of the weak state
    
    Returns:
        Dictionary with:
          - "neighbors_in": List of predecessor state names
          - "neighbors_out": List of successor state names
    """
    # Initialize empty neighbor lists
    neighbors_in = []
    neighbors_out = []
    
    # Check if node exists in graph
    if weak_state_name not in G.nodes():
        print(f"Warning: State '{weak_state_name}' not found in graph")
        return {"neighbors_in": neighbors_in, "neighbors_out": neighbors_out}
    
    # Extract immediate predecessors (states with edges INTO weak state)
    predecessors = list(G.predecessors(weak_state_name))
    neighbors_in = sorted(predecessors)  # Sort for consistency
    
    # Extract immediate successors (states weak state transitions OUT to)
    successors = list(G.successors(weak_state_name))
    neighbors_out = sorted(successors)   # Sort for consistency
    
    return {
        "neighbors_in": neighbors_in,
        "neighbors_out": neighbors_out
    }


def stage5_pipeline(full_graph: nx.DiGraph, flagged_states: List[Dict[str, Any]], 
                    state_names: List[str]) -> List[Dict[str, Any]]:
    """
    Isolate subgraphs for all flagged weak states from Stage 04.
    
    For each flagged state:
      1. Extract 1-hop neighborhood from graph
      2. Combine with Stage 04 metadata
    
    Args:
        full_graph: Complete FSM graph from Stage 02 (nodes are state names)
        flagged_states: List of weak states from Stage 04 report
        state_names: List of all state names (for validation)
    
    Returns:
        List of dictionaries ready for Stage 06 RL environment.
        Each dict contains: state_name, risk_score, cwe, features,
                           neighbors_in, neighbors_out
    """
    # Handle empty input gracefully
    if not flagged_states or len(flagged_states) == 0:
        print("No weak states to isolate.")
        return []
    
    isolated_states = []
    
    # Process each weak state
    for weak_state in flagged_states:
        state_name = weak_state.get("state_name")
        
        # Validate state exists in state_names
        if state_name not in state_names:
            print(f"Warning: State '{state_name}' not found in state_names list. Skipping.")
            continue
        
        # Extract subgraph (1-hop neighbors) - now uses state name directly
        subgraph_data = extract_subgraph(full_graph, state_name)
        
        # Combine Stage 04 metadata with subgraph neighbors
        isolated_state = {
            "state_name": state_name,
            "risk_score": weak_state.get("risk_score", 0.0),
            "cwe": weak_state.get("cwe", ""),
            "features": weak_state.get("features", []),
            "neighbors_in": subgraph_data["neighbors_in"],
            "neighbors_out": subgraph_data["neighbors_out"]
        }
        
        isolated_states.append(isolated_state)
    
    # Save output to JSON file
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_path = os.path.join(output_dir, "stage5_output.json")
    with open(output_path, 'w') as f:
        json.dump(isolated_states, f, indent=2)
    
    # Print confirmation
    print(f"Stage 05 complete. [{len(isolated_states)}] weak states isolated.")
    print(f"Saved to {output_path}")
    
    return isolated_states


# ============================================================================
# VALIDATION TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("FSMGuard Stage 05 - Validation Test")
    print("=" * 60)
    
    # Sample state names
    state_names = ["IDLE", "AUTH", "MEM_ACC", "DEBUG", "HALT"]
    
    # Build sample graph
    # Edges: IDLE→AUTH, IDLE→MEM_ACC, AUTH→MEM_ACC, MEM_ACC→HALT, DEBUG→MEM_ACC
    G = nx.DiGraph()
    G.add_nodes_from(range(len(state_names)))
    G.add_edge(0, 1)  # IDLE → AUTH
    G.add_edge(0, 2)  # IDLE → MEM_ACC
    G.add_edge(1, 2)  # AUTH → MEM_ACC
    G.add_edge(2, 4)  # MEM_ACC → HALT
    G.add_edge(3, 2)  # DEBUG → MEM_ACC
    
    print("\nTest Graph:")
    print("  States:", state_names)
    print("  Edges:")
    for src, dst in G.edges():
        print(f"    {state_names[src]} → {state_names[dst]}")
    
    # Sample flagged states from Stage 04
    flagged_states = [
        {
            "state_name": "MEM_ACC",
            "risk_score": 0.87,
            "cwe": "CWE-1245",
            "features": [4, 1, 0, 2, 0.76, 0, 0, 1, 1, 0, 1, 0, 1]
        }
    ]
    
    print("\nFlagged States:")
    for state in flagged_states:
        print(f"  {state['state_name']} (risk: {state['risk_score']})")
    
    # Run Stage 05 pipeline
    print("\n" + "-" * 60)
    print("Running Stage 05 Pipeline...")
    print("-" * 60)
    isolated = stage5_pipeline(G, flagged_states, state_names)
    
    # Validate output
    print("\n" + "-" * 60)
    print("Validation Results")
    print("-" * 60)
    
    expected_neighbors_in = ["AUTH", "DEBUG", "IDLE"]  # Sorted
    expected_neighbors_out = ["HALT"]
    
    if len(isolated) != 1:
        print(f"❌ FAIL: Expected 1 isolated state, got {len(isolated)}")
    else:
        result = isolated[0]
        
        # Check state name
        if result["state_name"] != "MEM_ACC":
            print(f"❌ FAIL: Expected state_name 'MEM_ACC', got '{result['state_name']}'")
        else:
            print(f"✅ PASS: state_name = {result['state_name']}")
        
        # Check risk score
        if result["risk_score"] != 0.87:
            print(f"❌ FAIL: Expected risk_score 0.87, got {result['risk_score']}")
        else:
            print(f"✅ PASS: risk_score = {result['risk_score']}")
        
        # Check CWE
        if result["cwe"] != "CWE-1245":
            print(f"❌ FAIL: Expected cwe 'CWE-1245', got '{result['cwe']}'")
        else:
            print(f"✅ PASS: cwe = {result['cwe']}")
        
        # Check neighbors_in
        if result["neighbors_in"] != expected_neighbors_in:
            print(f"❌ FAIL: neighbors_in mismatch")
            print(f"   Expected: {expected_neighbors_in}")
            print(f"   Got:      {result['neighbors_in']}")
        else:
            print(f"✅ PASS: neighbors_in = {result['neighbors_in']}")
        
        # Check neighbors_out
        if result["neighbors_out"] != expected_neighbors_out:
            print(f"❌ FAIL: neighbors_out mismatch")
            print(f"   Expected: {expected_neighbors_out}")
            print(f"   Got:      {result['neighbors_out']}")
        else:
            print(f"✅ PASS: neighbors_out = {result['neighbors_out']}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
    
    # Display full output
    print("\nFull Output (stage5_output.json):")
    print(json.dumps(isolated, indent=2))
