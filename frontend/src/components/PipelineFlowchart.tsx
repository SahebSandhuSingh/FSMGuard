import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Loader2, Circle, Cpu, BrainCircuit, Wrench, FileInput } from "lucide-react";

const stages = [
  {
    key: "INPUT",
    label: "Input & Parsing",
    icon: FileInput,
    color: "text-primary",
    description: "Parse Verilog via PyVerilog, extract AST, build FSM graph with NetworkX, and generate per-node feature vectors.",
    duration: 3000,
  },
  {
    key: "GYMNASIUM",
    label: "Gymnasium Environment",
    icon: Cpu,
    color: "text-secondary",
    description: "GNN classifier (GCN/GAT) flags vulnerable states, isolates subgraph, and wraps it as a Gymnasium RL environment.",
    duration: 3500,
  },
  {
    key: "RL_AGENT",
    label: "RL Agent — PPO",
    icon: BrainCircuit,
    color: "text-accent",
    description: "PPO agent selects optimal fix actions per flagged state using a policy network trained via Stable Baselines3.",
    duration: 4000,
  },
  {
    key: "PATCH_VERIFY",
    label: "Patch + Verify + Report",
    icon: Wrench,
    color: "text-primary",
    description: "Generate patched Verilog, verify with SymbiYosys + Z3, compute reward, and update RL policy weights.",
    duration: 3000,
  },
];

interface PipelineFlowchartProps {
  onComplete: () => void;
}

const PipelineFlowchart = ({ onComplete }: PipelineFlowchartProps) => {
  const [activeStep, setActiveStep] = useState(-1);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  useEffect(() => {
    let step = 0;
    const runStep = () => {
      if (step >= stages.length) {
        onComplete();
        return;
      }
      setActiveStep(step);
      setTimeout(() => {
        setCompletedSteps((prev) => [...prev, step]);
        step++;
        runStep();
      }, stages[step].duration);
    };
    runStep();
  }, [onComplete]);

  return (
    <div className="space-y-4">
      <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        RL Protection Pipeline
      </span>
      <div className="space-y-3">
        {stages.map((stage, i) => {
          const isActive = activeStep === i;
          const isCompleted = completedSteps.includes(i);
          const Icon = stage.icon;

          return (
            <div key={stage.key}>
              <motion.div
                initial={{ opacity: 0, x: 30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`relative border rounded-lg bg-card overflow-hidden transition-all ${
                  isActive
                    ? "border-primary/40 bg-primary/5"
                    : isCompleted
                    ? "border-primary/20 bg-primary/5"
                    : "border-border"
                }`}
              >
                <div className="flex items-center gap-3 px-4 py-3">
                  <div className="shrink-0">
                    {isCompleted ? (
                      <CheckCircle2 className="w-5 h-5 text-primary" />
                    ) : isActive ? (
                      <Loader2 className="w-5 h-5 text-primary animate-spin" />
                    ) : (
                      <Circle className="w-5 h-5 text-muted-foreground/40" />
                    )}
                  </div>
                  <Icon className={`w-4 h-4 ${stage.color} shrink-0`} />
                  <div className="flex-1 min-w-0">
                    <span
                      className={`font-mono text-sm font-semibold ${
                        isCompleted ? "text-foreground" : isActive ? "neon-text" : "text-muted-foreground"
                      }`}
                    >
                      {stage.label}
                    </span>
                    {(isActive || isCompleted) && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="text-xs text-muted-foreground mt-1"
                      >
                        {stage.description}
                      </motion.p>
                    )}
                  </div>
                </div>
                {isActive && (
                  <motion.div
                    initial={{ width: "0%" }}
                    animate={{ width: "100%" }}
                    transition={{ duration: stage.duration / 1000, ease: "linear" }}
                    className="h-0.5 bg-primary/40"
                  />
                )}
              </motion.div>
              {i < stages.length - 1 && (
                <div className="flex justify-center py-1">
                  <div className={`w-px h-4 ${isCompleted ? "bg-primary/40" : "bg-border"}`} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineFlowchart;