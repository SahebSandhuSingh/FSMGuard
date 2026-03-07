import { motion } from "framer-motion";
import { CheckCircle, Loader2, AlertTriangle, Circle } from "lucide-react";
import type { PipelineStage } from "@/data/pipelineStages";

type NodeStatus = "idle" | "processing" | "complete" | "error";

const categoryColors: Record<string, string> = {
  input: "border-blue-400/60",
  environment: "border-purple-400/60",
  ai: "border-green-400/60",
  patch: "border-red-400/60",
};

const categoryGlow: Record<string, string> = {
  input: "shadow-blue-400/20",
  environment: "shadow-purple-400/20",
  ai: "shadow-green-400/20",
  patch: "shadow-red-400/20",
};

interface PipelineNodeProps {
  stage: PipelineStage;
  status: NodeStatus;
  index: number;
}

export default function PipelineNode({ stage, status, index }: PipelineNodeProps) {
  const borderClass = categoryColors[stage.category];
  const glowClass = categoryGlow[stage.category];

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4 }}
      className={`relative w-[340px] rounded-lg border bg-card p-4 ${borderClass} ${
        status === "processing" ? `shadow-lg ${glowClass} animate-pulse-glow` : ""
      } ${status === "complete" ? "opacity-90" : ""}`}
    >
      {/* scan overlay when processing */}
      {status === "processing" && (
        <div className="pointer-events-none absolute inset-0 overflow-hidden rounded-lg">
          <div className="animate-scan absolute inset-x-0 h-8 bg-linear-to-b from-primary/10 to-transparent" />
        </div>
      )}

      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <StatusIcon status={status} />
          <span className="text-sm font-semibold text-foreground">{stage.title}</span>
        </div>
        <span className="rounded bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
          STAGE {String(stage.id).padStart(2, "0")}
        </span>
      </div>

      <p className="mt-1.5 text-xs text-muted-foreground leading-relaxed">{stage.description}</p>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {stage.tech.map((t) => (
          <span key={t} className="rounded-sm bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground">
            {t}
          </span>
        ))}
      </div>

      {stage.outputs && status === "complete" && (
        <div className="mt-2 flex gap-1.5">
          {stage.outputs.map((o) => (
            <span key={o} className="rounded bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary">
              ⊤ {o}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function StatusIcon({ status }: { status: NodeStatus }) {
  switch (status) {
    case "processing":
      return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
    case "complete":
      return <CheckCircle className="h-4 w-4 text-success" />;
    case "error":
      return <AlertTriangle className="h-4 w-4 text-danger" />;
    default:
      return <Circle className="h-4 w-4 text-muted-foreground" />;
  }
}
