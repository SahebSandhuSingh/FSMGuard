import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from "framer-motion";
import { CheckCircle, Loader2, AlertTriangle, Circle } from "lucide-react";
const categoryColors = {
    input: "border-primary/60",
    environment: "border-secondary/60",
    ai: "border-accent/60",
    patch: "border-destructive/60",
};
const categoryGlow = {
    input: "shadow-primary/25",
    environment: "shadow-secondary/25",
    ai: "shadow-accent/25",
    patch: "shadow-destructive/25",
};
export default function PipelineNode({ stage, status, index }) {
    const borderClass = categoryColors[stage.category];
    const glowClass = categoryGlow[stage.category];
    return (_jsxs(motion.div, { initial: { opacity: 0, y: 30 }, animate: { opacity: 1, y: 0 }, transition: { delay: index * 0.08, duration: 0.4 }, className: `relative w-[340px] rounded-lg border bg-card p-4 ${borderClass} ${status === "processing" ? `shadow-lg ${glowClass} animate-pulse-glow` : ""} ${status === "complete" ? "opacity-90" : ""}`, children: [status === "processing" && (_jsx("div", { className: "pointer-events-none absolute inset-0 overflow-hidden rounded-lg", children: _jsx("div", { className: "animate-scan absolute inset-x-0 h-8 bg-linear-to-b from-primary/10 to-transparent" }) })), _jsxs("div", { className: "flex items-center justify-between gap-2", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(StatusIcon, { status: status }), _jsx("span", { className: "text-sm font-semibold text-foreground", children: stage.title })] }), _jsxs("span", { className: "rounded bg-secondary px-2 py-0.5 font-mono text-[10px] text-muted-foreground", children: ["STAGE ", String(stage.id).padStart(2, "0")] })] }), _jsx("p", { className: "mt-1.5 text-xs text-muted-foreground leading-relaxed", children: stage.description }), _jsx("div", { className: "mt-3 flex flex-wrap gap-1.5", children: stage.tech.map((t) => (_jsx("span", { className: "rounded-sm bg-secondary px-1.5 py-0.5 text-[10px] font-medium text-secondary-foreground", children: t }, t))) }), stage.outputs && status === "complete" && (_jsx("div", { className: "mt-2 flex gap-1.5", children: stage.outputs.map((o) => (_jsxs("span", { className: "rounded bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary", children: ["\u22A4 ", o] }, o))) }))] }));
}
function StatusIcon({ status }) {
    switch (status) {
        case "processing":
            return _jsx(Loader2, { className: "h-4 w-4 animate-spin text-primary" });
        case "complete":
            return _jsx(CheckCircle, { className: "h-4 w-4 text-primary" });
        case "error":
            return _jsx(AlertTriangle, { className: "h-4 w-4 text-destructive" });
        default:
            return _jsx(Circle, { className: "h-4 w-4 text-muted-foreground" });
    }
}
