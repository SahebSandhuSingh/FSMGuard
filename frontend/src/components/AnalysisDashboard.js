import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from "framer-motion";
import { Activity, Bug, ShieldCheck, ShieldAlert, Wrench, CheckCircle2, } from "lucide-react";
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, } from "recharts";
export default function AnalysisDashboard({ data }) {
    const flagged = data.flagged_count;
    const total = data.total_states;
    const securityScore = total > 0
        ? Math.round(((total - flagged) / total) * 100)
        : 100;
    const riskData = data.states.map((s) => ({
        name: s.name,
        risk: Number(s.risk_score.toFixed(3)),
        flagged: s.flagged,
    }));
    return (_jsxs(motion.div, { initial: { opacity: 0, y: 12 }, animate: { opacity: 1, y: 0 }, transition: { duration: 0.4 }, className: "space-y-5", children: [_jsxs("div", { className: "grid grid-cols-2 gap-3 sm:grid-cols-4", children: [_jsx(StatCard, { icon: _jsx(Activity, { className: "h-4 w-4" }), label: "Total States", value: total, tone: "primary" }), _jsx(StatCard, { icon: _jsx(Bug, { className: "h-4 w-4" }), label: "Flagged Weak", value: flagged, tone: flagged > 0 ? "destructive" : "primary" }), _jsx(StatCard, { icon: _jsx(ShieldCheck, { className: "h-4 w-4" }), label: "Security Score", value: `${securityScore}%`, tone: securityScore >= 70 ? "primary" : "destructive" }), _jsx(StatCard, { icon: _jsx(CheckCircle2, { className: "h-4 w-4" }), label: "Module", value: data.module || "FSM", tone: "primary" })] }), _jsxs("div", { className: "rounded-lg border border-border bg-card p-4", children: [_jsx("h3", { className: "mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground", children: "Per-State Risk Scores (GNN Output)" }), _jsx(ResponsiveContainer, { width: "100%", height: 220, children: _jsxs(BarChart, { data: riskData, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "hsl(220 15% 18%)" }), _jsx(XAxis, { dataKey: "name", tick: { fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "ui-monospace" } }), _jsx(YAxis, { domain: [0, 1], tick: { fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "ui-monospace" } }), _jsx(Tooltip, { contentStyle: {
                                        background: "hsl(220 18% 10%)",
                                        border: "1px solid hsl(220 15% 18%)",
                                        borderRadius: 6,
                                        fontFamily: "ui-monospace",
                                        fontSize: 12,
                                        color: "hsl(160 40% 90%)",
                                    } }), _jsx(Bar, { dataKey: "risk", radius: [3, 3, 0, 0], children: riskData.map((entry, idx) => (_jsx(Cell, { fill: entry.flagged ? "hsl(0 72% 51%)" : "hsl(160 100% 40%)", opacity: 0.85 }, idx))) })] }) })] }), _jsxs("div", { className: "rounded-lg border border-border bg-card", children: [_jsx("div", { className: "border-b border-border px-4 py-3", children: _jsx("h3", { className: "font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground", children: "State Analysis Detail" }) }), _jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "w-full font-mono text-xs", children: [_jsx("thead", { children: _jsxs("tr", { className: "border-b border-border text-left text-muted-foreground", children: [_jsx("th", { className: "px-4 py-2", children: "State" }), _jsx("th", { className: "px-4 py-2", children: "Risk" }), _jsx("th", { className: "px-4 py-2", children: "Status" }), _jsx("th", { className: "px-4 py-2", children: "In\u00B0" }), _jsx("th", { className: "px-4 py-2", children: "Out\u00B0" }), _jsx("th", { className: "px-4 py-2", children: "Self-Loop" }), _jsx("th", { className: "px-4 py-2", children: "Reset Dist" }), _jsx("th", { className: "px-4 py-2", children: "RL Fix" })] }) }), _jsx("tbody", { children: data.states.map((s, i) => (_jsxs(motion.tr, { initial: { opacity: 0, x: -8 }, animate: { opacity: 1, x: 0 }, transition: { delay: i * 0.04 }, className: "border-b border-border/50 hover:bg-secondary/30", children: [_jsx("td", { className: "px-4 py-2 font-semibold text-foreground", children: s.name }), _jsx("td", { className: "px-4 py-2", children: _jsx("span", { className: s.flagged ? "text-destructive" : "text-primary", children: s.risk_score.toFixed(2) }) }), _jsx("td", { className: "px-4 py-2", children: s.flagged ? (_jsxs("span", { className: "inline-flex items-center gap-1 text-destructive", children: [_jsx(ShieldAlert, { className: "h-3 w-3" }), " WEAK"] })) : (_jsxs("span", { className: "inline-flex items-center gap-1 text-primary", children: [_jsx(ShieldCheck, { className: "h-3 w-3" }), " SAFE"] })) }), _jsx("td", { className: "px-4 py-2 text-foreground", children: s.in_degree }), _jsx("td", { className: "px-4 py-2 text-foreground", children: s.out_degree }), _jsx("td", { className: "px-4 py-2 text-foreground", children: s.self_loop ? "Yes" : "No" }), _jsx("td", { className: "px-4 py-2 text-foreground", children: s.reset_distance }), _jsx("td", { className: "px-4 py-2", children: s.recommended_fix ? (_jsxs("span", { className: "inline-flex items-center gap-1 text-secondary", children: [_jsx(Wrench, { className: "h-3 w-3" }), " ", s.recommended_fix] })) : (_jsx("span", { className: "text-muted-foreground", children: "\u2014" })) })] }, s.name))) })] }) })] })] }));
}
function StatCard({ icon, label, value, tone, }) {
    const toneCls = tone === "destructive"
        ? "border-destructive/30 text-destructive"
        : "border-primary/30 text-primary";
    return (_jsxs("div", { className: `rounded-lg border bg-card p-3 ${toneCls}`, children: [_jsxs("div", { className: "mb-1 flex items-center gap-1.5 text-muted-foreground", children: [icon, _jsx("span", { className: "font-mono text-[10px] uppercase tracking-wider", children: label })] }), _jsx("p", { className: "font-mono text-2xl font-bold truncate", children: value })] }));
}
