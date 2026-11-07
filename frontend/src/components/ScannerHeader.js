import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { Shield, Activity } from "lucide-react";
import { motion } from "framer-motion";
const ScannerHeader = () => (_jsxs(motion.header, { initial: { opacity: 0, y: -20 }, animate: { opacity: 1, y: 0 }, className: "flex items-center gap-4 py-6", children: [_jsxs("div", { className: "relative", children: [_jsx(Shield, { className: "w-10 h-10 text-primary" }), _jsx(Activity, { className: "w-4 h-4 text-secondary absolute -bottom-1 -right-1" })] }), _jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-bold neon-text font-mono tracking-wider", children: "FSM SECURITY PIPELINE" }), _jsx("p", { className: "text-sm text-muted-foreground font-mono", children: "Analyzer + RL Protection Agent" })] })] }));
export default ScannerHeader;
