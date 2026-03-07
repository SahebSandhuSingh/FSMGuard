import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";

const STAGES = [
  { id: 1, name: "Input & Parsing", tech: "PyVerilog" },
  { id: 2, name: "Graph Construction", tech: "NetworkX" },
  { id: 3, name: "Feature Generation", tech: "NumPy" },
  { id: 4, name: "GNN Detection", tech: "GCN/GAT" },
  { id: 5, name: "Subgraph Isolation", tech: "NetworkX" },
  { id: 6, name: "RL Env Setup", tech: "Gymnasium" },
  { id: 7, name: "RL Agent", tech: "PPO" },
  { id: 8, name: "Patch Generation", tech: "Jinja2" },
  { id: 9, name: "Formal Verify", tech: "SymbiYosys" },
  { id: 10, name: "Reward Loop", tech: "SB3" },
];

interface Props {
  currentStage: number;
}

const PipelineStages = ({ currentStage }: Props) => {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h2 className="mb-4 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
        Pipeline Progress
      </h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5 lg:grid-cols-10">
        {STAGES.map((stage) => {
          const isDone = currentStage >= stage.id;
          const isActive = currentStage === stage.id - 1;

          return (
            <motion.div
              key={stage.id}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: stage.id * 0.05 }}
              className={`relative flex flex-col items-center rounded-md border p-2 text-center transition-all duration-300 ${
                isDone
                  ? "border-primary/40 bg-primary/5"
                  : isActive
                  ? "border-accent/50 bg-accent/5 glow-accent"
                  : "border-border bg-background"
              }`}
            >
              <div
                className={`mb-1 flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                  isDone
                    ? "bg-primary text-primary-foreground"
                    : isActive
                    ? "bg-accent text-accent-foreground"
                    : "bg-secondary text-muted-foreground"
                }`}
              >
                {isDone ? (
                  <Check className="h-3 w-3" />
                ) : isActive ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  stage.id
                )}
              </div>
              <span className="font-mono text-[10px] font-medium leading-tight text-card-foreground">
                {stage.name}
              </span>
              <span className="mt-0.5 font-mono text-[9px] text-muted-foreground">
                {stage.tech}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineStages;
