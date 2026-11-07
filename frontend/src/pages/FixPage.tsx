import { useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Vulnerability } from "@/lib/mockData";
import PipelineCanvas from "@/components/PipelineCanvas";
import PipelineSidebar from "@/components/PipelineSidebar";
import PatchedOutput from "@/components/PatchedOutput";
import FsmGraph from "@/components/FsmGraph";
import type { FsmGraphResponse } from "@/lib/api";

const FixPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { vulnerabilities = [], jobId, fsmGraph, initialVerilog } = (location.state as {
    vulnerabilities: Vulnerability[];
    jobId?: string;
    fsmGraph?: FsmGraphResponse | null;
    initialVerilog?: string;
  }) || {};
  const [completed, setCompleted] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleComplete = useCallback(() => {
    setCompleted(true);
  }, []);

  if (!vulnerabilities.length) {
    return (
      <div className="min-h-screen bg-background grid-bg flex items-center justify-center">
        <div className="text-center space-y-4">
          <p className="text-muted-foreground font-mono">No vulnerabilities loaded</p>
          <Button onClick={() => navigate("/")} variant="ghost" className="font-mono text-primary">
            <ArrowLeft className="w-4 h-4 mr-2" /> Back to Scanner
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background grid-bg relative flex flex-col h-screen overflow-hidden">
      <div className="scan-line fixed inset-0 pointer-events-none z-50 opacity-20" />
      <div className="relative z-10 flex flex-col flex-1 overflow-hidden">
        {/* Top bar */}
        <div className="border-b border-border bg-card/80 backdrop-blur px-6 py-3 flex items-center justify-between shrink-0">
          <Button
            onClick={() => navigate("/")}
            variant="ghost"
            size="sm"
            className="font-mono text-xs text-muted-foreground hover:text-primary pl-14"
          >
            <ArrowLeft className="w-3 h-3 mr-1.5" /> Back
          </Button>
          <span className="font-mono text-xs uppercase tracking-widest neon-text">
            RL Protection Agent
          </span>
          <div />
        </div>

        {/* Split layout */}
        <div className="flex flex-1 relative overflow-hidden">
          <PipelineSidebar open={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} vulnerabilities={vulnerabilities} />
          
          <div className={`flex-1 overflow-y-auto p-6 space-y-6 transition-all duration-300 ${sidebarOpen ? "pl-76" : "pl-16"}`}>
            <PipelineCanvas jobId={jobId} onComplete={handleComplete} initialVerilog={initialVerilog} />
            {fsmGraph && <FsmGraph data={fsmGraph} />}
            {completed && <PatchedOutput vulnerabilities={vulnerabilities} jobId={jobId} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FixPage;