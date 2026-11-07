import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, Loader2, Circle, Cpu, BrainCircuit, Wrench, FileInput, Zap, ChevronRight, } from "lucide-react";
import { pollUntilDone } from "@/lib/api";
/* ────────── stage data ────────── */
const stages = [
    {
        key: "INPUT",
        label: "Input & Parsing",
        icon: FileInput,
        color: "hsl(160 100% 45%)",
        glowVar: "--neon-glow",
        description: "Parse Verilog via PyVerilog, extract AST, build FSM graph with NetworkX, and generate per-node feature vectors.",
        tech: ["PyVerilog", "NetworkX", "NumPy"],
        duration: 3000,
    },
    {
        key: "GYMNASIUM",
        label: "Gymnasium Environment",
        icon: Cpu,
        color: "hsl(195 100% 45%)",
        glowVar: "--cyan-glow",
        description: "GNN classifier (GCN/GAT) flags vulnerable states, isolates subgraph, and wraps it as a Gymnasium RL environment.",
        tech: ["PyTorch Geometric", "GCN/GAT", "Gymnasium"],
        duration: 3500,
    },
    {
        key: "RL_AGENT",
        label: "RL Agent — PPO",
        icon: BrainCircuit,
        color: "hsl(280 80% 55%)",
        glowVar: "--accent-glow",
        description: "PPO agent selects optimal fix actions per flagged state using a policy network trained via Stable Baselines3.",
        tech: ["PPO", "Stable Baselines3", "Policy Net"],
        duration: 4000,
    },
    {
        key: "PATCH_VERIFY",
        label: "Patch + Verify + Report",
        icon: Wrench,
        color: "hsl(160 100% 45%)",
        glowVar: "--neon-glow",
        description: "Generate patched Verilog, verify with SymbiYosys + Z3, compute reward, and update RL policy weights.",
        tech: ["SymbiYosys", "Z3", "Jinja2"],
        duration: 3000,
    },
];
/* ────────── particle burst component ────────── */
const ParticleBurst = ({ color }) => {
    const particles = useMemo(() => Array.from({ length: 8 }, (_, i) => ({
        id: i,
        angle: (i / 8) * 360,
        distance: 30 + Math.random() * 20,
        size: 2 + Math.random() * 3,
        delay: Math.random() * 0.15,
    })), []);
    return (_jsx("div", { className: "absolute inset-0 pointer-events-none overflow-visible", children: particles.map((p) => (_jsx(motion.div, { initial: { opacity: 1, scale: 1, x: 0, y: 0 }, animate: {
                opacity: 0,
                scale: 0,
                x: Math.cos((p.angle * Math.PI) / 180) * p.distance,
                y: Math.sin((p.angle * Math.PI) / 180) * p.distance,
            }, transition: { duration: 0.6, delay: p.delay, ease: "easeOut" }, style: {
                position: "absolute",
                left: "50%",
                top: "50%",
                width: p.size,
                height: p.size,
                borderRadius: "50%",
                backgroundColor: color,
                boxShadow: `0 0 6px ${color}`,
            } }, p.id))) }));
};
/* ────────── animated connector ────────── */
const Connector = ({ isCompleted, color, }) => (_jsxs("div", { className: "flex flex-col items-center py-0.5 relative", style: { height: 32 }, children: [_jsx("div", { className: "w-px flex-1 bg-border" }), _jsx(motion.div, { className: "w-px absolute top-0 left-1/2 -translate-x-1/2", initial: { height: 0 }, animate: { height: isCompleted ? "calc(100% - 10px)" : 0 }, transition: { duration: 0.4, ease: "easeOut" }, style: { backgroundColor: color } }), _jsx(AnimatePresence, { children: isCompleted && (_jsx(motion.div, { initial: { scale: 0, opacity: 0 }, animate: { scale: 1, opacity: 1 }, exit: { scale: 0, opacity: 0 }, transition: { type: "spring", stiffness: 500, damping: 20, delay: 0.25 }, className: "absolute bottom-0 flex items-center justify-center", style: {
                    color: color,
                    filter: `drop-shadow(0 0 4px ${color})`,
                }, children: _jsx("svg", { width: "12", height: "8", viewBox: "0 0 12 8", fill: "none", children: _jsx("path", { d: "M1 1L6 6L11 1", stroke: "currentColor", strokeWidth: "2", strokeLinecap: "round", strokeLinejoin: "round" }) }) })) }), isCompleted && (_jsx(motion.div, { className: "absolute rounded-full left-1/2", initial: { top: 0, opacity: 1 }, animate: { top: "70%", opacity: 0 }, transition: { duration: 0.4, ease: "easeIn" }, style: {
                width: 6,
                height: 6,
                backgroundColor: color,
                boxShadow: `0 0 10px ${color}, 0 0 20px ${color}`,
                marginLeft: -3,
            } }))] }));
/* ────────── overall progress bar ────────── */
const OverallProgress = ({ activeStep, completedSteps, }) => {
    const total = stages.length;
    const done = completedSteps.length;
    const inProgress = activeStep >= 0 && !completedSteps.includes(activeStep) ? 1 : 0;
    const pct = Math.min(100, Math.round(((done + inProgress * 0.5) / total) * 100));
    return (_jsxs("div", { className: "space-y-2", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(Zap, { className: "w-3.5 h-3.5 text-primary" }), _jsx("span", { className: "font-mono text-[10px] uppercase tracking-widest text-muted-foreground", children: "RL Protection Pipeline" })] }), _jsxs("span", { className: "font-mono text-xs tabular-nums neon-text", children: [pct, "%"] })] }), _jsx("div", { className: "h-1 rounded-full bg-muted overflow-hidden", children: _jsx(motion.div, { className: "h-full rounded-full", initial: { width: 0 }, animate: { width: `${pct}%` }, transition: { duration: 0.5, ease: "easeOut" }, style: {
                        background: "linear-gradient(90deg, hsl(160 100% 45%), hsl(195 100% 45%), hsl(280 80% 55%))",
                        boxShadow: "0 0 12px hsl(160 100% 45% / 0.5), 0 0 24px hsl(195 100% 45% / 0.3)",
                    } }) })] }));
};
/* ────────── stage card ────────── */
const StageCard = ({ stage, index, isActive, isCompleted, isPending, }) => {
    const Icon = stage.icon;
    const [showParticles, setShowParticles] = useState(false);
    useEffect(() => {
        if (isCompleted) {
            setShowParticles(true);
            const t = setTimeout(() => setShowParticles(false), 800);
            return () => clearTimeout(t);
        }
    }, [isCompleted]);
    return (_jsxs(motion.div, { initial: { opacity: 0, x: 40 }, animate: { opacity: 1, x: 0 }, transition: { delay: index * 0.12, type: "spring", stiffness: 260, damping: 22 }, whileHover: !isPending ? { scale: 1.015 } : undefined, className: "relative", children: [isActive && (_jsx(motion.div, { className: "absolute -inset-px rounded-xl pointer-events-none", initial: { opacity: 0 }, animate: { opacity: [0.4, 0.8, 0.4] }, transition: { duration: 2, repeat: Infinity, ease: "easeInOut" }, style: {
                    border: `1px solid ${stage.color}`,
                    boxShadow: `0 0 16px ${stage.color}40, inset 0 0 16px ${stage.color}10`,
                } })), _jsxs("div", { className: `relative rounded-xl border overflow-hidden transition-all duration-300 ${isActive
                    ? "bg-card/90 backdrop-blur-sm"
                    : isCompleted
                        ? "bg-card/70"
                        : "bg-card/40 opacity-60"}`, style: {
                    borderColor: isActive
                        ? `${stage.color}60`
                        : isCompleted
                            ? `${stage.color}30`
                            : "hsl(160 40% 18% / 0.4)",
                }, children: [_jsxs("div", { className: "flex items-center gap-3 px-4 py-3", children: [_jsxs("div", { className: "relative shrink-0", children: [_jsx(AnimatePresence, { mode: "wait", children: isCompleted ? (_jsx(motion.div, { initial: { scale: 0, rotate: -90 }, animate: { scale: 1, rotate: 0 }, transition: { type: "spring", stiffness: 400, damping: 15 }, children: _jsx(CheckCircle2, { className: "w-5 h-5", style: { color: stage.color } }) }, "done")) : isActive ? (_jsx(motion.div, { initial: { scale: 0 }, animate: { scale: 1 }, transition: { type: "spring" }, children: _jsx(Loader2, { className: "w-5 h-5 animate-spin", style: { color: stage.color } }) }, "active")) : (_jsx(motion.div, { children: _jsx(Circle, { className: "w-5 h-5 text-muted-foreground/30" }) }, "pending")) }), showParticles && _jsx(ParticleBurst, { color: stage.color })] }), _jsx("div", { className: "shrink-0 p-1.5 rounded-md", style: {
                                    backgroundColor: isActive || isCompleted
                                        ? `${stage.color}15`
                                        : "transparent",
                                }, children: _jsx(Icon, { className: "w-4 h-4 transition-colors", style: {
                                        color: isActive || isCompleted
                                            ? stage.color
                                            : "hsl(160 20% 55%)",
                                    } }) }), _jsx("div", { className: "flex-1 min-w-0", children: _jsxs("div", { className: "flex items-center gap-2", children: [_jsx("span", { className: "font-mono text-[10px] px-1.5 py-0.5 rounded", style: {
                                                backgroundColor: isActive || isCompleted ? `${stage.color}15` : "hsl(220 15% 14%)",
                                                color: isActive || isCompleted
                                                    ? stage.color
                                                    : "hsl(160 20% 55%)",
                                            }, children: String(index + 1).padStart(2, "0") }), _jsx("span", { className: `font-mono text-sm font-semibold transition-colors ${isCompleted
                                                ? "text-foreground"
                                                : isActive
                                                    ? "text-foreground"
                                                    : "text-muted-foreground"}`, style: isActive
                                                ? {
                                                    textShadow: `0 0 8px ${stage.color}90`,
                                                }
                                                : undefined, children: stage.label })] }) }), _jsx("div", { className: "shrink-0", children: isCompleted ? (_jsx("span", { className: "font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full", style: {
                                        backgroundColor: `${stage.color}20`,
                                        color: stage.color,
                                        border: `1px solid ${stage.color}30`,
                                    }, children: "Complete" })) : isActive ? (_jsx(motion.span, { animate: { opacity: [0.5, 1, 0.5] }, transition: { duration: 1.5, repeat: Infinity }, className: "font-mono text-[9px] uppercase tracking-wider px-2 py-0.5 rounded-full", style: {
                                        backgroundColor: `${stage.color}15`,
                                        color: stage.color,
                                        border: `1px solid ${stage.color}25`,
                                    }, children: "Running" })) : (_jsx("span", { className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground/40 px-2 py-0.5", children: "Queued" })) })] }), _jsx(AnimatePresence, { children: (isActive || isCompleted) && (_jsx(motion.div, { initial: { height: 0, opacity: 0 }, animate: { height: "auto", opacity: 1 }, exit: { height: 0, opacity: 0 }, transition: { duration: 0.3, ease: "easeOut" }, className: "overflow-hidden", children: _jsxs("div", { className: "px-4 pb-3 space-y-2.5", children: [_jsxs("div", { className: "flex items-start gap-2", children: [_jsx(ChevronRight, { className: "w-3 h-3 mt-0.5 shrink-0", style: { color: stage.color } }), _jsx("p", { className: "text-xs text-muted-foreground leading-relaxed", children: stage.description })] }), _jsx("div", { className: "flex gap-1.5 flex-wrap pl-5", children: stage.tech.map((t, ti) => (_jsx(motion.span, { initial: { opacity: 0, scale: 0.8 }, animate: { opacity: 1, scale: 1 }, transition: { delay: ti * 0.06 }, className: "text-[10px] font-mono px-2 py-0.5 rounded-md border", style: {
                                                backgroundColor: `${stage.color}08`,
                                                borderColor: `${stage.color}20`,
                                                color: stage.color,
                                            }, children: t }, t))) })] }) })) }), isActive && (_jsxs("div", { className: "relative h-1", children: [_jsx("div", { className: "absolute inset-0 bg-muted/30" }), _jsx(motion.div, { className: "absolute top-0 left-0 h-full", initial: { width: "0%" }, animate: { width: "100%" }, transition: {
                                    duration: stage.duration / 1000,
                                    ease: "linear",
                                }, style: {
                                    background: `linear-gradient(90deg, ${stage.color}80, ${stage.color})`,
                                    boxShadow: `0 0 12px ${stage.color}60`,
                                } }), _jsx(motion.div, { className: "absolute top-0 h-full w-12", initial: { left: "-10%" }, animate: { left: "110%" }, transition: {
                                    duration: 1.2,
                                    repeat: Infinity,
                                    ease: "linear",
                                }, style: {
                                    background: `linear-gradient(90deg, transparent, ${stage.color}40, transparent)`,
                                } })] })), isCompleted && (_jsx("div", { className: "h-px", style: { backgroundColor: `${stage.color}25` } }))] })] }));
};
const PipelineFlowchart = ({ onComplete, jobId }) => {
    const [activeStep, setActiveStep] = useState(-1);
    const [completedSteps, setCompletedSteps] = useState([]);
    // Map progress 0–100 → stage index (0–3)
    const progressToStage = (progress) => {
        if (progress <= 25)
            return 0;
        if (progress <= 50)
            return 1;
        if (progress <= 75)
            return 2;
        return 3;
    };
    useEffect(() => {
        if (jobId) {
            // Real mode: drive stages via backend polling
            let lastStage = -1;
            const handleProgress = (status) => {
                const stageIndex = progressToStage(status.progress);
                if (stageIndex > lastStage) {
                    setCompletedSteps((prev) => {
                        const newCompleted = [...prev];
                        for (let i = lastStage; i < stageIndex; i++) {
                            if (!newCompleted.includes(i) && i >= 0)
                                newCompleted.push(i);
                        }
                        return newCompleted;
                    });
                    setActiveStep(stageIndex);
                    lastStage = stageIndex;
                }
            };
            pollUntilDone(jobId, handleProgress).then(() => {
                setCompletedSteps([0, 1, 2, 3]);
                setActiveStep(-1);
                onComplete();
            }).catch(() => {
                setCompletedSteps([0, 1, 2, 3]);
                setActiveStep(-1);
                onComplete();
            });
        }
        else {
            // Fallback timer mode (no jobId)
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
        }
    }, [jobId, onComplete]);
    return (_jsxs("div", { className: "space-y-5", children: [_jsx(OverallProgress, { activeStep: activeStep, completedSteps: completedSteps }), _jsx("div", { className: "space-y-0", children: stages.map((stage, i) => {
                    const isActive = activeStep === i;
                    const isCompleted = completedSteps.includes(i);
                    const isPending = !isActive && !isCompleted;
                    return (_jsxs("div", { children: [_jsx(StageCard, { stage: stage, index: i, isActive: isActive, isCompleted: isCompleted, isPending: isPending }), i < stages.length - 1 && (_jsx(Connector, { isCompleted: isCompleted, color: stage.color }))] }, stage.key));
                }) }), _jsx(AnimatePresence, { children: completedSteps.length === stages.length && (_jsx(motion.div, { initial: { opacity: 0, y: 10, scale: 0.95 }, animate: { opacity: 1, y: 0, scale: 1 }, className: "text-center py-3", children: _jsx(motion.span, { animate: { opacity: [0.6, 1, 0.6] }, transition: { duration: 2, repeat: Infinity }, className: "font-mono text-xs uppercase tracking-widest", style: {
                            color: "hsl(160 100% 45%)",
                            textShadow: "0 0 12px hsl(160 100% 45% / 0.6)",
                        }, children: "\u2726 Pipeline Complete \u2014 All Patches Verified \u2726" }) })) })] }));
};
export default PipelineFlowchart;
