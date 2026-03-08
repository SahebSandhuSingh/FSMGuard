# FSMGuard AI — FSM Security Pipeline with RL Protection

**Automated vulnerability detection and patching for Finite State Machines (FSMs) in Verilog designs using Graph Neural Networks and Reinforcement Learning.**

---

## 🔹 Project Overview

FSMGuard AI analyzes hardware FSMs and automatically identifies and patches potential security weaknesses in digital designs. The system combines **static hardware analysis, graph-based learning, and reinforcement learning** to detect vulnerable states and propose secure modifications to the FSM logic.

The pipeline performs the following stages:

1. **Static Analysis**
   Verilog files are parsed using **PyVerilog** to generate an Abstract Syntax Tree (AST). The AST is analyzed to identify FSM structures such as state registers, transitions, and control logic.

2. **FSM Extraction**
   The detected FSM is reconstructed by identifying states and transition conditions from `case` statements and sequential logic blocks.

3. **Graph Representation**
   The FSM is converted into a graph using **NetworkX**, where:

   * **Nodes** represent FSM states
   * **Edges** represent transitions
   * Additional features store conditions, reset behavior, and transition guards.

4. **Weak State Detection (GNN)**
   A **Graph Neural Network (GCN/GAT)** analyzes the FSM graph to identify suspicious or vulnerable states such as:

   * Unprotected transitions
   * Dead-end states
   * Unsafe reset paths
   * Privilege escalation paths

5. **Subgraph Isolation**
   Vulnerable states and their surrounding transitions are extracted as subgraphs to focus the repair process on the problematic FSM region.

6. **RL-Based Security Repair**
   A **Gymnasium environment** simulates FSM modifications.
   A **PPO agent (Stable-Baselines3)** learns to apply security fixes such as:

   * Adding transition guards
   * Redirecting illegal states to trap states
   * Removing unsafe transitions
   * Hardening reset paths

7. **Patch Generation**
   Based on the selected actions, FSMGuard generates **patched Verilog code** that incorporates the suggested fixes while preserving original functionality.

8. **Formal Verification**
   The patched design is verified using **SymbiYosys with SMT solvers (e.g., Z3)** to ensure:

   * Functional correctness
   * Absence of security violations
   * No new unreachable or deadlock states

9. **Visualization Interface**
   A frontend visualizes:

   * The FSM graph
   * Detected vulnerable states
   * Recommended fixes
   * Before/after FSM structure

---

## 🔹 Architecture Pipeline

```
Verilog Source
      │
      ▼
PyVerilog Parsing
(AST Generation)
      │
      ▼
FSM Extraction
(states, transitions)
      │
      ▼
NetworkX Graph Construction
      │
      ▼
Graph Neural Network
(GCN / GAT)
Weak State Detection
      │
      ▼
Vulnerable Subgraph Extraction
      │
      ▼
Gymnasium RL Environment
(FSM modification simulation)
      │
      ▼
PPO Agent (Stable-Baselines3)
Learns optimal security fixes
      │
      ▼
Patch Generator
(Patched Verilog FSM)
      │
      ▼
Formal Verification
SymbiYosys + Z3
      │
      ▼
Verified Secure FSM
      │
      ▼
Frontend Visualization
```
