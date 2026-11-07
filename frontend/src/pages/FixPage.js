import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import PipelineCanvas from "@/components/PipelineCanvas";
import PipelineSidebar from "@/components/PipelineSidebar";
import PatchedOutput from "@/components/PatchedOutput";
import FsmGraph from "@/components/FsmGraph";
const FixPage = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { vulnerabilities = [], jobId, fsmGraph, initialVerilog } = location.state || {};
    const [completed, setCompleted] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const handleComplete = useCallback(() => {
        setCompleted(true);
    }, []);
    if (!vulnerabilities.length) {
        return (_jsx("div", { className: "min-h-screen bg-background grid-bg flex items-center justify-center", children: _jsxs("div", { className: "text-center space-y-4", children: [_jsx("p", { className: "text-muted-foreground font-mono", children: "No vulnerabilities loaded" }), _jsxs(Button, { onClick: () => navigate("/"), variant: "ghost", className: "font-mono text-primary", children: [_jsx(ArrowLeft, { className: "w-4 h-4 mr-2" }), " Back to Scanner"] })] }) }));
    }
    return (_jsxs("div", { className: "min-h-screen bg-background grid-bg relative flex flex-col h-screen overflow-hidden", children: [_jsx("div", { className: "scan-line fixed inset-0 pointer-events-none z-50 opacity-20" }), _jsxs("div", { className: "relative z-10 flex flex-col flex-1 overflow-hidden", children: [_jsxs("div", { className: "border-b border-border bg-card/80 backdrop-blur px-6 py-3 flex items-center justify-between shrink-0", children: [_jsxs(Button, { onClick: () => navigate("/"), variant: "ghost", size: "sm", className: "font-mono text-xs text-muted-foreground hover:text-primary pl-14", children: [_jsx(ArrowLeft, { className: "w-3 h-3 mr-1.5" }), " Back"] }), _jsx("span", { className: "font-mono text-xs uppercase tracking-widest neon-text", children: "RL Protection Agent" }), _jsx("div", {})] }), _jsxs("div", { className: "flex flex-1 relative overflow-hidden", children: [_jsx(PipelineSidebar, { open: sidebarOpen, onToggle: () => setSidebarOpen(!sidebarOpen), vulnerabilities: vulnerabilities }), _jsxs("div", { className: `flex-1 overflow-y-auto p-6 space-y-6 transition-all duration-300 ${sidebarOpen ? "pl-76" : "pl-16"}`, children: [_jsx(PipelineCanvas, { jobId: jobId, onComplete: handleComplete, initialVerilog: initialVerilog }), fsmGraph && _jsx(FsmGraph, { data: fsmGraph }), completed && _jsx(PatchedOutput, { vulnerabilities: vulnerabilities, jobId: jobId })] })] })] })] }));
};
export default FixPage;
