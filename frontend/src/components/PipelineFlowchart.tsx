import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  Loader2,
  Circle,
  Cpu,
  BrainCircuit,
  Wrench,
  FileInput,
  Zap,
  ChevronRight,
} from "lucide-react";

/* ────────── stage data ────────── */
const stages = [
  {
    key: "INPUT",
    label: "Input & Parsing",
    icon: FileInput,
    color: "hsl(160 100% 45%)",
    glowVar: "--neon-glow",
    description:
      "Parse Verilog via PyVerilog, extract AST, build FSM graph with NetworkX, and generate per-node feature vectors.",
    tech: ["PyVerilog", "NetworkX", "NumPy"],
    duration: 3000,
  },
  {
    key: "GYMNASIUM",
    label: "Gymnasium Environment",
    icon: Cpu,
    color: "hsl(195 100% 45%)",
    glowVar: "--cyan-glow",
    description:
      "GNN classifier (GCN/GAT) flags vulnerable states, isolates subgraph, and wraps it as a Gymnasium RL environment.",
    tech: ["PyTorch Geometric", "GCN/GAT", "Gymnasium"],
    duration: 3500,
  },
  {
    key: "RL_AGENT",
    label: "RL Agent — PPO",
    icon: BrainCircuit,
    color: "hsl(280 80% 55%)",
    glowVar: "--accent-glow",
    description:
      "PPO agent selects optimal fix actions per flagged state using a policy network trained via Stable Baselines3.",
    tech: ["PPO", "Stable Baselines3", "Policy Net"],
    duration: 4000,
  },
  {
    key: "PATCH_VERIFY",
    label: "Patch + Verify + Report",
    icon: Wrench,
    color: "hsl(160 100% 45%)",
    glowVar: "--neon-glow",
    description:
      "Generate patched Verilog, verify with SymbiYosys + Z3, compute reward, and update RL policy weights.",
    tech: ["SymbiYosys", "Z3", "Jinja2"],
    duration: 3000,
  },
];

/* ────────── particle burst component ────────── */
const ParticleBurst = ({ color }: { color: string }) => {
  const particles = useMemo(
    () =>
      Array.from({ length: 8 }, (_, i) => ({
        id: i,
        angle: (i / 8) * 360,
        distance: 30 + Math.random() * 20,
        size: 2 + Math.random() * 3,
        delay: Math.random() * 0.15,
      })),
    []
  );

  return (
    <div className="absolute inset-0 pointer-events-none overflow-visible">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          initial={{ opacity: 1, scale: 1, x: 0, y: 0 }}
          animate={{
            opacity: 0,
            scale: 0,
            x: Math.cos((p.angle * Math.PI) / 180) * p.distance,
            y: Math.sin((p.angle * Math.PI) / 180) * p.distance,
          }}
          transition={{ duration: 0.6, delay: p.delay, ease: "easeOut" }}
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: p.size,
            height: p.size,
            borderRadius: "50%",
            backgroundColor: color,
            boxShadow: `0 0 6px ${color}`,
          }}
        />
      ))}
    </div>
  );
};

/* ────────── animated connector ────────── */
const Connector = ({
  isCompleted,
  color,
}: {
  isCompleted: boolean;
  color: string;
}) => (
  <div className="flex flex-col items-center py-0.5 relative" style={{ height: 32 }}>
    {/* track */}
    <div className="w-px flex-1 bg-border" />
    {/* animated fill overlay */}
    <motion.div
      className="w-px absolute top-0 left-1/2 -translate-x-1/2"
      initial={{ height: 0 }}
      animate={{ height: isCompleted ? "calc(100% - 10px)" : 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      style={{ backgroundColor: color }}
    />
    {/* arrow at bottom */}
    <AnimatePresence>
      {isCompleted && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 500, damping: 20, delay: 0.25 }}
          className="absolute bottom-0 flex items-center justify-center"
          style={{
            color: color,
            filter: `drop-shadow(0 0 4px ${color})`,
          }}
        >
          <svg width="12" height="8" viewBox="0 0 12 8" fill="none">
            <path
              d="M1 1L6 6L11 1"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </motion.div>
      )}
    </AnimatePresence>
    {/* glow dot traveling down */}
    {isCompleted && (
      <motion.div
        className="absolute rounded-full left-1/2"
        initial={{ top: 0, opacity: 1 }}
        animate={{ top: "70%", opacity: 0 }}
        transition={{ duration: 0.4, ease: "easeIn" }}
        style={{
          width: 6,
          height: 6,
          backgroundColor: color,
          boxShadow: `0 0 10px ${color}, 0 0 20px ${color}`,
          marginLeft: -3,
        }}
      />
    )}
  </div>
);

/* ────────── overall progress bar ────────── */
const OverallProgress = ({
  activeStep,
  completedSteps,
}: {
  activeStep: number;
  completedSteps: number[];
}) => {
  const total = stages.length;
  const done = completedSteps.length;
  const inProgress = activeStep >= 0 && !completedSteps.includes(activeStep) ? 1 : 0;
  const pct = Math.min(100, Math.round(((done + inProgress * 0.5) / total) * 100));

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 text-primary" />
          <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            RL Protection Pipeline
          </span>
        </div>
        <span className="font-mono text-xs tabular-nums neon-text">{pct}%</span>
      </div>
      <div className="h-1 rounded-full bg-muted overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          style={{
            background:
              "linear-gradient(90deg, hsl(160 100% 45%), hsl(195 100% 45%), hsl(280 80% 55%))",
            boxShadow:
              "0 0 12px hsl(160 100% 45% / 0.5), 0 0 24px hsl(195 100% 45% / 0.3)",
          }}
        />
      </div>
    </div>
  );
};

/* ────────── stage card ────────── */
const StageCard = ({
  stage,
  index,
  isActive,
  isCompleted,
  isPending,
}: {
  stage: (typeof stages)[0];
  index: number;
  isActive: boolean;
  isCompleted: boolean;
  isPending: boolean;
}) => {
  const Icon = stage.icon;
  const [showParticles, setShowParticles] = useState(false);

  useEffect(() => {
    if (isCompleted) {
      setShowParticles(true);
      const t = setTimeout(() => setShowParticles(false), 800);
      return () => clearTimeout(t);
    }
  }, [isCompleted]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.12, type: "spring", stiffness: 260, damping: 22 }}
      whileHover={!isPending ? { scale: 1.015 } : undefined}
      className="relative"
    >
      {/* outer glow ring when active */}
      {isActive && (
        <motion.div
          className="absolute -inset-px rounded-xl pointer-events-none"
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.4, 0.8, 0.4] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          style={{
            border: `1px solid ${stage.color}`,
            boxShadow: `0 0 16px ${stage.color}40, inset 0 0 16px ${stage.color}10`,
          }}
        />
      )}

      <div
        className={`relative rounded-xl border overflow-hidden transition-all duration-300 ${
          isActive
            ? "bg-card/90 backdrop-blur-sm"
            : isCompleted
            ? "bg-card/70"
            : "bg-card/40 opacity-60"
        }`}
        style={{
          borderColor: isActive
            ? `${stage.color}60`
            : isCompleted
            ? `${stage.color}30`
            : "hsl(160 40% 18% / 0.4)",
        }}
      >
        {/* header row */}
        <div className="flex items-center gap-3 px-4 py-3">
          {/* status icon with particle burst */}
          <div className="relative shrink-0">
            <AnimatePresence mode="wait">
              {isCompleted ? (
                <motion.div
                  key="done"
                  initial={{ scale: 0, rotate: -90 }}
                  animate={{ scale: 1, rotate: 0 }}
                  transition={{ type: "spring", stiffness: 400, damping: 15 }}
                >
                  <CheckCircle2
                    className="w-5 h-5"
                    style={{ color: stage.color }}
                  />
                </motion.div>
              ) : isActive ? (
                <motion.div
                  key="active"
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring" }}
                >
                  <Loader2
                    className="w-5 h-5 animate-spin"
                    style={{ color: stage.color }}
                  />
                </motion.div>
              ) : (
                <motion.div key="pending">
                  <Circle className="w-5 h-5 text-muted-foreground/30" />
                </motion.div>
              )}
            </AnimatePresence>
            {showParticles && <ParticleBurst color={stage.color} />}
          </div>

          {/* stage icon */}
          <div
            className="shrink-0 p-1.5 rounded-md"
            style={{
              backgroundColor: isActive || isCompleted
                ? `${stage.color}15`
                : "transparent",
            }}
          >
            <Icon
              className="w-4 h-4 transition-colors"
              style={{
                color: isActive || isCompleted
                  ? stage.color
                  : "hsl(160 20% 55%)",
              }}
            />
          </div>

          {/* label + step number */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span
                className="font-mono text-[10px] px-1.5 py-0.5 rounded"
                style={{
                  backgroundColor:
                    isActive || isCompleted ? `${stage.color}15` : "hsl(220 15% 14%)",
                  color:
                    isActive || isCompleted
                      ? stage.color
                      : "hsl(160 20% 55%)",
                }}
              >
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                className={`font-mono text-sm font-semibold transition-colors ${
                  isCompleted
                    ? "text-foreground"
                    : isActive
                    ? "text-foreground"
                    : "text-muted-foreground"
                }`}
                style={
                  isActive
                    ? {
                        textShadow: `0 0 8px ${stage.color}90`,
                      }
                    : undefined
                }
              >
                {stage.label}
              </span>
            </div>
          </div>

          {/* status badge */}
          <div className="shrink-0">
            {isCompleted ? (
              <span
                className="font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: `${stage.color}20`,
                  color: stage.color,
                  border: `1px solid ${stage.color}30`,
                }}
              >
                Complete
              </span>
            ) : isActive ? (
              <motion.span
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full"
                style={{
                  backgroundColor: `${stage.color}15`,
                  color: stage.color,
                  border: `1px solid ${stage.color}25`,
                }}
              >
                Running
              </motion.span>
            ) : (
              <span className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground/40 px-2 py-0.5">
                Queued
              </span>
            )}
          </div>
        </div>

        {/* expandable detail section */}
        <AnimatePresence>
          {(isActive || isCompleted) && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="overflow-hidden"
            >
              <div className="px-4 pb-3 space-y-2.5">
                {/* description */}
                <div className="flex items-start gap-2">
                  <ChevronRight
                    className="w-3 h-3 mt-0.5 shrink-0"
                    style={{ color: stage.color }}
                  />
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {stage.description}
                  </p>
                </div>

                {/* tech badges */}
                <div className="flex gap-1.5 flex-wrap pl-5">
                  {stage.tech.map((t, ti) => (
                    <motion.span
                      key={t}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: ti * 0.06 }}
                      className="text-[10px] font-mono px-2 py-0.5 rounded-md border"
                      style={{
                        backgroundColor: `${stage.color}08`,
                        borderColor: `${stage.color}20`,
                        color: stage.color,
                      }}
                    >
                      {t}
                    </motion.span>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* progress bar — only while active */}
        {isActive && (
          <div className="relative h-1">
            <div className="absolute inset-0 bg-muted/30" />
            <motion.div
              className="absolute top-0 left-0 h-full"
              initial={{ width: "0%" }}
              animate={{ width: "100%" }}
              transition={{
                duration: stage.duration / 1000,
                ease: "linear",
              }}
              style={{
                background: `linear-gradient(90deg, ${stage.color}80, ${stage.color})`,
                boxShadow: `0 0 12px ${stage.color}60`,
              }}
            />
            {/* shimmer sweep */}
            <motion.div
              className="absolute top-0 h-full w-12"
              initial={{ left: "-10%" }}
              animate={{ left: "110%" }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                ease: "linear",
              }}
              style={{
                background: `linear-gradient(90deg, transparent, ${stage.color}40, transparent)`,
              }}
            />
          </div>
        )}

        {/* completed shimmer line */}
        {isCompleted && (
          <div className="h-px" style={{ backgroundColor: `${stage.color}25` }} />
        )}
      </div>
    </motion.div>
  );
};

/* ────────── main component ────────── */
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
    <div className="space-y-5">
      {/* overall progress */}
      <OverallProgress activeStep={activeStep} completedSteps={completedSteps} />

      {/* stage cards */}
      <div className="space-y-0">
        {stages.map((stage, i) => {
          const isActive = activeStep === i;
          const isCompleted = completedSteps.includes(i);
          const isPending = !isActive && !isCompleted;

          return (
            <div key={stage.key}>
              <StageCard
                stage={stage}
                index={i}
                isActive={isActive}
                isCompleted={isCompleted}
                isPending={isPending}
              />
              {i < stages.length - 1 && (
                <Connector
                  isCompleted={isCompleted}
                  color={stage.color}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* completion flash */}
      <AnimatePresence>
        {completedSteps.length === stages.length && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            className="text-center py-3"
          >
            <motion.span
              animate={{ opacity: [0.6, 1, 0.6] }}
              transition={{ duration: 2, repeat: Infinity }}
              className="font-mono text-xs uppercase tracking-widest"
              style={{
                color: "hsl(160 100% 45%)",
                textShadow: "0 0 12px hsl(160 100% 45% / 0.6)",
              }}
            >
              ✦ Pipeline Complete — All Patches Verified ✦
            </motion.span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default PipelineFlowchart;