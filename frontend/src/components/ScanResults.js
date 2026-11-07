import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from "framer-motion";
import { Shield, AlertTriangle, ChevronRight, ShieldAlert, ShieldCheck, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
const severityConfig = {
    critical: { icon: ShieldAlert, className: "bg-destructive/20 text-destructive border-destructive/40" },
    high: { icon: AlertTriangle, className: "bg-destructive/10 text-destructive/80 border-destructive/30" },
    medium: { icon: Info, className: "bg-secondary/20 text-secondary border-secondary/40" },
    low: { icon: ShieldCheck, className: "bg-primary/20 text-primary border-primary/40" },
};
const ScanResults = ({ vulnerabilities, onFix }) => {
    const criticalCount = vulnerabilities.filter((v) => v.severity === "critical").length;
    const highCount = vulnerabilities.filter((v) => v.severity === "high").length;
    return (_jsxs(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, transition: { delay: 0.3 }, className: "space-y-4 mt-8", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(Shield, { className: "w-4 h-4 text-destructive" }), _jsx("span", { className: "font-mono text-sm uppercase tracking-widest text-muted-foreground", children: "Scan Results" })] }), _jsxs("div", { className: "flex items-center gap-3 font-mono text-xs", children: [_jsxs("span", { className: "flex items-center gap-1", children: [_jsx(AlertTriangle, { className: "w-3 h-3 text-destructive" }), _jsxs("span", { className: "danger-text", children: [criticalCount, " critical"] })] }), _jsxs("span", { className: "flex items-center gap-1", children: [_jsx(AlertTriangle, { className: "w-3 h-3 text-destructive/60" }), _jsxs("span", { className: "text-destructive/80", children: [highCount, " high"] })] }), _jsxs("span", { className: "text-muted-foreground", children: [vulnerabilities.length, " total"] })] })] }), _jsx("div", { className: "space-y-3", children: vulnerabilities.map((vuln, i) => {
                    const config = severityConfig[vuln.severity];
                    const Icon = config.icon;
                    return (_jsxs(motion.div, { initial: { opacity: 0, x: -20 }, animate: { opacity: 1, x: 0 }, transition: { delay: i * 0.15 }, className: "border border-border rounded-lg bg-card p-4 space-y-3", children: [_jsxs("div", { className: "flex items-start gap-3", children: [_jsx(Icon, { className: "w-5 h-5 mt-0.5 shrink-0" }), _jsxs("div", { children: [_jsx("h3", { className: "font-mono text-sm font-semibold text-foreground", children: vuln.title }), _jsxs("div", { className: "flex items-center gap-2 mt-1", children: [_jsx(Badge, { variant: "outline", className: `text-xs font-mono uppercase ${config.className}`, children: vuln.severity }), _jsxs("span", { className: "text-xs font-mono text-muted-foreground", children: ["State: ", vuln.state] }), _jsxs("span", { className: "text-xs font-mono text-muted-foreground", children: ["Line ", vuln.line] })] })] })] }), _jsx("p", { className: "text-xs text-muted-foreground leading-relaxed", children: vuln.description })] }, vuln.id));
                }) }), _jsx(motion.div, { initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 }, transition: { delay: vulnerabilities.length * 0.15 + 0.3 }, className: "flex justify-center pt-4", children: _jsxs(Button, { onClick: onFix, size: "lg", className: "font-mono text-sm uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/80 px-8", children: ["Fix & Patch All Vulnerabilities", _jsx(ChevronRight, { className: "w-4 h-4 ml-2" })] }) })] }));
};
export default ScanResults;
