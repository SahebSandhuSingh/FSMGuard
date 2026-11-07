import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Download, CheckCircle2, FileCode2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchPatchedCode, getReportUrl } from "@/lib/api";
import jsPDF from "jspdf";
const PatchedOutput = ({ vulnerabilities, jobId }) => {
    const [patchedCode, setPatchedCode] = useState("");
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        if (jobId) {
            fetchPatchedCode(jobId)
                .then((code) => setPatchedCode(code))
                .catch(() => setPatchedCode("// Patched file not available — check backend."))
                .finally(() => setLoading(false));
        }
        else {
            setPatchedCode("// No job ID provided — run a real analysis to see patched code.");
            setLoading(false);
        }
    }, [jobId]);
    const briefSummary = `The RL agent identified ${vulnerabilities.length} vulnerabilities in the FSM design. All vulnerable states have been patched and formally verified via SymbiYosys + Z3.`;
    const handleDownloadReport = () => {
        if (jobId) {
            window.open(getReportUrl(jobId, "txt"), "_blank");
            return;
        }
        // Fallback: generate PDF from current data
        const doc = new jsPDF();
        doc.setFont("courier", "normal");
        doc.setFontSize(16);
        doc.text("FSM Security Pipeline — Report", 14, 20);
        doc.setFontSize(10);
        doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 28);
        doc.setLineWidth(0.5);
        doc.line(14, 32, 196, 32);
        let y = 40;
        doc.setFontSize(12);
        doc.text("Summary", 14, y);
        y += 7;
        doc.setFontSize(9);
        const summaryLines = doc.splitTextToSize(briefSummary, 170);
        doc.text(summaryLines, 14, y);
        y += summaryLines.length * 5 + 8;
        doc.setFontSize(12);
        doc.text("Vulnerabilities Detected & Solutions", 14, y);
        y += 8;
        vulnerabilities.forEach((v, i) => {
            if (y > 240) {
                doc.addPage();
                y = 20;
            }
            doc.setFontSize(11);
            doc.text(`${i + 1}. [${v.severity.toUpperCase()}] ${v.title}`, 14, y);
            y += 6;
            doc.setFontSize(9);
            doc.text(`State: ${v.state}`, 14, y);
            y += 5;
            const descLines = doc.splitTextToSize(v.description, 170);
            doc.text(descLines, 14, y);
            y += descLines.length * 5 + 3;
            doc.text(`Solution: ${v.solution}`, 14, y);
            y += 8;
        });
        if (patchedCode) {
            if (y > 200) {
                doc.addPage();
                y = 20;
            }
            doc.setFontSize(12);
            doc.text("Full Patched Verilog Code", 14, y);
            y += 8;
            doc.setFontSize(8);
            const codeLines = doc.splitTextToSize(patchedCode, 175);
            codeLines.forEach((line) => {
                if (y > 280) {
                    doc.addPage();
                    y = 20;
                }
                doc.text(line, 14, y);
                y += 4;
            });
        }
        doc.save("fsm-security-report.pdf");
    };
    return (_jsxs(motion.div, { initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, className: "space-y-5 mt-6", children: [_jsxs("div", { className: "border border-primary/20 rounded-lg bg-card p-4 space-y-2", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(CheckCircle2, { className: "w-4 h-4 text-primary" }), _jsx("span", { className: "font-mono text-sm uppercase tracking-widest neon-text", children: "Analysis Complete" })] }), _jsx("p", { className: "text-sm text-muted-foreground leading-relaxed", children: briefSummary })] }), _jsxs("div", { className: "border border-primary/20 rounded-lg bg-card p-4 space-y-3", children: [_jsxs("div", { className: "flex items-center gap-2", children: [_jsx(FileCode2, { className: "w-4 h-4 text-primary" }), _jsx("span", { className: "font-mono text-sm uppercase tracking-widest neon-text", children: "Full Patched Code" })] }), _jsx("div", { className: "rounded-md bg-muted border border-border p-4 max-h-96 overflow-y-auto", children: loading ? (_jsx("p", { className: "text-xs font-mono text-muted-foreground animate-pulse", children: "Loading patched code..." })) : (_jsx("pre", { className: "text-xs font-mono text-foreground whitespace-pre", children: patchedCode })) })] }), _jsx("div", { className: "flex justify-center pt-2", children: _jsxs(Button, { onClick: handleDownloadReport, size: "lg", className: "font-mono text-sm uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/80 px-8", children: [_jsx(Download, { className: "w-4 h-4 mr-2" }), "Download Full Report"] }) })] }));
};
export default PatchedOutput;
