# FSMGuard AI — FSM Security Pipeline with RL Protection

**Automated vulnerability detection and patching for Finite State Machines in Verilog designs using Graph Neural Networks and Reinforcement Learning.**

---

## 🔹 Project Overview

FSMGuard AI analyzes hardware FSMs and automatically suggests security patches. It combines:

1. **Static Analysis** — Extract FSM from Verilog using PyVerilog.
2. **Graph Representation** — Convert FSM to a graph (states = nodes, transitions = edges).
3. **Weak State Detection** — Use a GNN (GCN/GAT) to flag risky states.
4. **RL-Based Fixes** — PPO agent decides best remediation (guards, traps, pruning).
5. **Patch Generation** — Produces patched, valid Verilog.
6. **Formal Verification** — Ensures fixes maintain functionality and security using SymbiYosys + SMT solvers.
7. **Frontend Visualization** — Shows FSM, vulnerable states, and suggested fixes interactively.

---

## 🔹 Architecture

```text
Verilog → PyVerilog → NetworkX Graph → GNN Flags →
Subgraph → Gymnasium RL → PPO Agent → Patched Verilog →
SymbiYosys + Z3 → Reward → Back to RL
