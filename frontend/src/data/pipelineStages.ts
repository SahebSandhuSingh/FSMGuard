export interface PipelineStage {
  id: number;
  title: string;
  description: string;
  tech: string[];
  category: "analysis" | "ai" | "fix" | "verify";
  outputs?: string[];
}

export const pipelineStages: PipelineStage[] = [
  {
    id: 1,
    title: "FSM Analysis & Graph Construction",
    description: "Parses Verilog RTL, extracts FSM structure, builds state graph, and computes structural features",
    tech: ["PyVerilog", "NetworkX", "NumPy", "AST"],
    category: "analysis",
    outputs: ["FSM Graph", "Feature Matrix"],
  },
  {
    id: 2,
    title: "GNN Vulnerability Detection",
    description: "GCN/GAT classifier analyzes graph features and flags weak/vulnerable states with risk scores",
    tech: ["PyTorch Geometric", "GCN/GAT", "Binary Classifier"],
    category: "ai",
    outputs: ["Risk Scores", "Flagged States"],
  },
  {
    id: 3,
    title: "RL-Driven Patch Generation",
    description: "PPO agent selects optimal fixes for flagged states and generates patched Verilog code",
    tech: ["PPO", "Stable Baselines3", "Gymnasium", "Jinja2"],
    category: "fix",
    outputs: ["Patched Verilog", "Fix Actions"],
  },
  {
    id: 4,
    title: "Formal Verification & Scoring",
    description: "Proves patch correctness, simulates against testbench, and computes security/area/functionality scores",
    tech: ["SymbiYosys", "Z3", "Icarus Verilog", "SVA"],
    category: "verify",
    outputs: ["Proof Result", "Security Score"],
  },
];
