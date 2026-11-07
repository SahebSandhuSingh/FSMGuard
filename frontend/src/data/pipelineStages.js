export const pipelineStages = [
    {
        id: 1,
        title: "INPUT",
        description: "GNN weak states, 13 features, fix history, remaining states, CWE + risk score",
        tech: ["GNN", "NumPy", "CWE DB"],
        category: "input",
        outputs: ["Weak States", "Feature Matrix"],
    },
    {
        id: 2,
        title: "GYMNASIUM ENVIRONMENT",
        description: "Observation space (30 values), MultiDiscrete [4×3×2], step function (apply + reward), reset function, sequential multi-state",
        tech: ["Gymnasium", "MultiDiscrete", "Box(30)"],
        category: "environment",
        outputs: ["Obs Vector", "Reward Signal"],
    },
    {
        id: 3,
        title: "RL AGENT — PPO  /  ACTION SPACE",
        description: "Policy network (PyTorch), PPO algorithm (SB3), fix specification (Cat+Param+Strict) — actions: Guard, Prune, Re-encode, Deadlock",
        tech: ["PyTorch", "SB3", "PPO", "Guard", "Prune", "Re-encode", "Deadlock"],
        category: "ai",
        outputs: ["Fix Actions", "Patched RTL"],
    },
    {
        id: 4,
        title: "PATCH + VERIFY + REPORT",
        description: "Stage 08 patch Verilog, Stage 09 Icarus verify, Stage 10 report generator → patched_fsm.v + fsm_report.txt",
        tech: ["Jinja2", "Icarus Verilog", "Reporter"],
        category: "patch",
        outputs: ["patched_fsm.v", "fsm_report.txt"],
    },
];
