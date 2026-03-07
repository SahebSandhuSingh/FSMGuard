import { useState, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ShieldAlert, AlertTriangle, Info, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Vulnerability } from "@/lib/mockData";
import PipelineFlowchart from "@/components/PipelineFlowchart";
import PatchedOutput from "@/components/PatchedOutput";

const severityIcon: Record<string, React.ElementType> = {
  critical: ShieldAlert,
  high: AlertTriangle,
  medium: Info,
  low: ShieldCheck,
};

const severityBadge: Record<string, string> = {
  critical: "bg-destructive/20 text-destructive border-destructive/40",
  high: "bg-destructive/10 text-destructive/80 border-destructive/30",
  medium: "bg-secondary/20 text-secondary border-secondary/40",
  low: "bg-primary/20 text-primary border-primary/40",
};

const FixPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { vulnerabilities = [] } = (location.state as { vulnerabilities: Vulnerability[] }) || {};
  const [completed, setCompleted] = useState(false);

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
    <div className="min-h-screen bg-background grid-bg relative">
      <div className="scan-line fixed inset-0 pointer-events-none z-50 opacity-20" />
      <div className="relative z-10">
        {/* Top bar */}
        <div className="border-b border-border bg-card/80 backdrop-blur px-6 py-3 flex items-center justify-between">
          <Button
            onClick={() => navigate("/")}
            variant="ghost"
            size="sm"
            className="font-mono text-xs text-muted-foreground hover:text-primary"
          >
            <ArrowLeft className="w-3 h-3 mr-1.5" /> Back
          </Button>
          <span className="font-mono text-xs uppercase tracking-widest neon-text">
            RL Protection Agent
          </span>
          <div />
        </div>

        {/* Split layout */}
        <div className="flex min-h-[calc(100vh-53px)]">
          {/* Left — Vulnerabilities */}
          <div className="w-80 shrink-0 border-r border-border bg-card/50 overflow-y-auto p-4 space-y-3">
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              Detected Vulnerabilities ({vulnerabilities.length})
            </span>
            {vulnerabilities.map((v, i) => {
              const Icon = severityIcon[v.severity];
              return (
                <motion.div
                  key={v.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="border border-border rounded-md bg-card p-3 space-y-2"
                >
                  <div className="flex items-start gap-2">
                    <Icon className="w-4 h-4 mt-0.5 shrink-0 text-muted-foreground" />
                    <span className="font-mono text-xs font-semibold text-foreground leading-tight">
                      {v.title}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className={`text-[10px] font-mono uppercase ${severityBadge[v.severity]}`}>
                      {v.severity}
                    </Badge>
                    <span className="text-[10px] font-mono text-muted-foreground">Line {v.line}</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground leading-relaxed">{v.description}</p>
                </motion.div>
              );
            })}
          </div>

          {/* Right — Pipeline + Output */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            <PipelineFlowchart onComplete={handleComplete} />
            {completed && <PatchedOutput vulnerabilities={vulnerabilities} />}
          </div>
        </div>
      </div>
    </div>
  );
};

export default FixPage;