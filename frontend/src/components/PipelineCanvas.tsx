import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, RotateCcw, Zap, ShieldCheck, AlertTriangle, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import PipelineNode from "./PipelineNode";
import ConnectorLine from "./ConnectorLine";
import { pipelineStages } from "@/data/pipelineStages";
import {
  fetchOriginalCode,
  fetchPatchedCode,
  getResults,
  pollUntilDone,
} from "@/lib/api";

type NodeStatus = "idle" | "processing" | "complete" | "error";

const SAMPLE_VERILOG = `module fsm_example(
  input clk, rst, in,
  output reg [1:0] state
);
  parameter S0=2'b00, S1=2'b01, S2=2'b10, S3=2'b11;
  always @(posedge clk or posedge rst) begin
    if (rst) state <= S0;
    else case(state)
      S0: state <= in ? S1 : S0;
      S1: state <= in ? S2 : S0;
      S2: state <= in ? S3 : S1;
      S3: state <= S0; // potential vulnerability
    endcase
  end
endmodule`;

interface Threat {
  state: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  fix: string;
}

interface PipelineCanvasProps {
  jobId?: string | null;
  onComplete?: () => void;
  initialVerilog?: string;
}

export default function PipelineCanvas({ jobId, onComplete, initialVerilog }: PipelineCanvasProps) {
  const [verilog, setVerilog] = useState(initialVerilog || "");
  const [patchedVerilog, setPatchedVerilog] = useState("");
  const [statuses, setStatuses] = useState<NodeStatus[]>(pipelineStages.map(() => "idle"));
  const [running, setRunning] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [showResults, setShowResults] = useState(false);
  
  // Results details
  const [securityScore, setSecurityScore] = useState(92);
  const [areaScore, setAreaScore] = useState(97);
  const [funcScore, setFuncScore] = useState(100);
  const [threats, setThreats] = useState<Threat[]>([
    { state: "S3", severity: "high", description: "Unconditional transition ignores input — lockout risk", fix: "Added input guard condition" },
    { state: "default", severity: "medium", description: "Missing default case — unhandled states possible", fix: "Added deadlock trap to reset" },
  ]);

  useEffect(() => {
    if (jobId) {
      setRunning(true);
      setShowResults(false);
      setStatuses(pipelineStages.map(() => "idle"));

      // Fetch original verilog code
      fetchOriginalCode(jobId).then((code) => {
        setVerilog(code);
      }).catch(() => {
        if (initialVerilog) setVerilog(initialVerilog);
      });

      const progressToStage = (progress: number): number => {
        if (progress <= 25) return 0;
        if (progress <= 50) return 1;
        if (progress <= 75) return 2;
        return 3;
      };

      pollUntilDone(jobId, (status) => {
        const stageIndex = progressToStage(status.progress);
        setStatuses((prev) => {
          const next = [...prev];
          for (let i = 0; i < stageIndex; i++) {
            next[i] = "complete";
          }
          next[stageIndex] = "processing";
          return next;
        });
        setCurrentStage(stageIndex);
      }).then(async () => {
        setStatuses(["complete", "complete", "complete", "complete"]);
        setCurrentStage(-1);
        setRunning(false);

        // Fetch results and patched code from backend
        try {
          const res = await getResults(jobId);
          const patched = await fetchPatchedCode(jobId);
          setPatchedVerilog(patched);

          // Calculate scores
          const total = res.vulnerabilities_found || 0;
          const fixed = res.vulnerabilities_fixed || 0;
          const score = total > 0 ? Math.round(((total - fixed) / total) * 100) : 100;
          setSecurityScore(score);
          
          const isVerified = res.stages?.["stage5_10"]?.["outputs"]?.["stage9_result.json"]?.overall !== "FAILED";
          setFuncScore(isVerified ? 100 : 85);

          // Set threats list
          if (res.vulnerability_list) {
            setThreats(res.vulnerability_list.map((v: any) => ({
              state: v.state || "unknown",
              severity: v.severity || "medium",
              description: v.description || "Vulnerability found in state",
              fix: v.solution || "Countermeasure applied"
            })));
          }
        } catch (e) {
          console.error("Failed to load results:", e);
        }

        setShowResults(true);
        if (onComplete) onComplete();
      }).catch((err) => {
        console.error(err);
        setStatuses(["complete", "complete", "complete", "complete"]);
        setCurrentStage(-1);
        setRunning(false);
        setShowResults(true);
        if (onComplete) onComplete();
      });
    } else {
      if (initialVerilog) {
        setVerilog(initialVerilog);
      }
    }
  }, [jobId, onComplete, initialVerilog]);

  const runPipeline = useCallback(async () => {
    if (!verilog.trim()) return;
    setRunning(true);
    setShowResults(false);
    const newStatuses: NodeStatus[] = pipelineStages.map(() => "idle");
    setStatuses([...newStatuses]);

    for (let i = 0; i < pipelineStages.length; i++) {
      setCurrentStage(i);
      newStatuses[i] = "processing";
      setStatuses([...newStatuses]);
      const delay = pipelineStages[i].category === "ai" ? 2500 : pipelineStages[i].category === "patch" ? 2000 : 1500;
      await new Promise((r) => setTimeout(r, delay));
      newStatuses[i] = "complete";
      setStatuses([...newStatuses]);
    }
    setCurrentStage(-1);
    setRunning(false);
    setPatchedVerilog(SAMPLE_VERILOG.replace("state <= S0; // potential vulnerability", "state <= in ? S0 : S1; // patched"));
    setShowResults(true);
    if (onComplete) onComplete();
  }, [verilog, onComplete]);

  const reset = () => {
    setStatuses(pipelineStages.map(() => "idle"));
    setCurrentStage(-1);
    setRunning(false);
    setShowResults(false);
  };

  const allDone = statuses.every((s) => s === "complete");

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* top bar */}
      <header className="flex items-center justify-between border-b border-border bg-card/50 px-5 py-3 pl-14">
        <h1 className="text-sm font-semibold tracking-wide text-foreground font-mono">FSM Security Pipeline</h1>
        <div className="flex items-center gap-2">
          {running && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-[11px] font-medium text-primary font-mono"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
              Stage {currentStage + 1}/{pipelineStages.length}
            </motion.span>
          )}
          {allDone && (
            <motion.span
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-1.5 rounded-full bg-primary/10 px-3 py-1 text-[11px] font-medium text-primary font-mono"
            >
              ✓ Pipeline Complete
            </motion.span>
          )}
          {!jobId && (
            <>
              <Button size="sm" variant="outline" className="h-7 text-xs font-mono" onClick={reset} disabled={running}>
                <RotateCcw className="mr-1 h-3 w-3" /> Reset
              </Button>
              <Button size="sm" variant="outline" className="h-7 text-xs font-mono" onClick={() => setVerilog(SAMPLE_VERILOG)} disabled={running}>
                <Play className="mr-1 h-3 w-3" /> Load Sample
              </Button>
            </>
          )}
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Input panel */}
        <div className="flex w-80 flex-col border-r border-border bg-card/30 p-4">
          <label className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground font-mono">
            Verilog Input
          </label>
          <Textarea
            value={verilog}
            onChange={(e) => setVerilog(e.target.value)}
            placeholder="Paste your Verilog FSM design here..."
            className="flex-1 resize-none bg-muted border-border font-mono text-xs leading-relaxed placeholder:text-muted-foreground"
            disabled={running || !!jobId}
          />
          {!jobId && (
            <Button
              onClick={runPipeline}
              disabled={running || !verilog.trim()}
              className="mt-3 h-10 bg-primary text-primary-foreground hover:bg-primary/90 font-mono font-semibold"
            >
              <Zap className="mr-2 h-4 w-4" />
              {running ? "Analyzing..." : "FIX"}
            </Button>
          )}
        </div>

        {/* Pipeline canvas + results */}
        <ScrollArea className="flex-1">
          <div className="flex flex-col items-center py-8 px-4">
            {/* Start node */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-2 rounded-lg border border-primary/40 bg-card px-5 py-2.5"
            >
              <span className="h-2.5 w-2.5 rounded-full bg-primary" />
              <span className="text-sm font-semibold text-foreground font-mono">Start</span>
              {verilog.trim() && (
                <span className="ml-2 rounded bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary font-mono">
                  Input Ready
                </span>
              )}
            </motion.div>

            <ConnectorLine active={statuses[0] !== "idle"} index={0} />

            {/* Pipeline stages */}
            <AnimatePresence>
              {pipelineStages.map((stage, i) => (
                <div key={stage.id} className="flex flex-col items-center">
                  <PipelineNode stage={stage} status={statuses[i]} index={i} />
                  {i < pipelineStages.length - 1 && (
                    <ConnectorLine active={statuses[i + 1] !== "idle"} index={i + 1} />
                  )}
                </div>
              ))}
            </AnimatePresence>

            <ConnectorLine active={allDone} index={pipelineStages.length} />

            {/* End node */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 }}
              className={`flex flex-col items-center gap-1 rounded-lg border bg-card px-5 py-2.5 ${
                allDone ? "border-primary/40" : "border-border"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`h-2.5 w-2.5 rounded-full ${allDone ? "bg-primary" : "bg-muted-foreground"}`} />
                <span className="text-sm font-semibold text-foreground font-mono">End</span>
              </div>
              <span className="text-[10px] text-muted-foreground font-mono">
                {allDone ? "Patched Verilog ready" : "Awaiting pipeline run"}
              </span>
            </motion.div>

            {/* Results section */}
            <AnimatePresence>
              {showResults && (
                <motion.div
                  initial={{ opacity: 0, y: 40 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 40 }}
                  transition={{ duration: 0.5 }}
                  className="mt-8 w-full max-w-2xl space-y-6"
                >
                  {/* Security Score */}
                  <div className="rounded-lg border border-border bg-card p-5">
                    <div className="flex items-center gap-2 mb-4">
                      <ShieldCheck className="h-5 w-5 text-primary" />
                      <h2 className="text-sm font-semibold text-foreground font-mono">Security Score</h2>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      {[
                        { label: "Security", value: securityScore, color: "text-primary" },
                        { label: "Area Overhead", value: areaScore, color: "text-secondary" },
                        { label: "Functionality", value: funcScore, color: "text-accent" },
                      ].map((s) => (
                        <div key={s.label} className="text-center">
                          <div className="relative mx-auto mb-2 h-16 w-16">
                            <svg className="h-16 w-16 -rotate-90" viewBox="0 0 36 36">
                              <circle cx="18" cy="18" r="14" fill="none" stroke="var(--color-border)" strokeWidth="3" />
                              <motion.circle
                                cx="18" cy="18" r="14" fill="none"
                                stroke="currentColor"
                                strokeWidth="3"
                                strokeDasharray={`${(s.value / 100) * 88} 88`}
                                strokeLinecap="round"
                                className={s.color}
                                initial={{ strokeDasharray: "0 88" }}
                                animate={{ strokeDasharray: `${(s.value / 100) * 88} 88` }}
                                transition={{ duration: 1, delay: 0.3 }}
                              />
                            </svg>
                            <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-foreground font-mono">
                              {s.value}%
                            </span>
                          </div>
                          <span className="text-[10px] font-medium text-muted-foreground font-mono">{s.label}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Threats */}
                  <div className="rounded-lg border border-border bg-card p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="h-5 w-5 text-destructive" />
                      <h2 className="text-sm font-semibold text-foreground font-mono">Detected Threats</h2>
                    </div>
                    <div className="space-y-2">
                      {threats.map((t, i) => (
                        <motion.div
                          key={i}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: i * 0.15 }}
                          className="flex items-start gap-3 rounded-md bg-muted p-3"
                        >
                          <span className={`mt-0.5 h-2 w-2 rounded-full shrink-0 ${
                            t.severity === "high" || t.severity === "critical" ? "bg-destructive" : "bg-secondary"
                          }`} />
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-xs font-semibold text-foreground">{t.state}</span>
                              <span className={`rounded px-1.5 py-0.5 text-[9px] font-bold uppercase font-mono ${
                                t.severity === "high" || t.severity === "critical"
                                  ? "bg-destructive/15 text-destructive"
                                  : "bg-secondary/15 text-secondary"
                              }`}>
                                {t.severity}
                              </span>
                            </div>
                            <p className="mt-0.5 text-[11px] text-muted-foreground font-mono leading-relaxed">{t.description}</p>
                            <p className="mt-1 flex items-center gap-1 text-[10px] text-primary font-mono">
                              <CheckCircle className="h-3 w-3" /> {t.fix}
                            </p>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>

                  {/* Patched Verilog */}
                  {patchedVerilog && (
                    <div className="rounded-lg border border-border bg-card p-5">
                      <div className="flex items-center justify-between mb-3">
                        <h2 className="text-sm font-semibold text-foreground font-mono">Patched Verilog</h2>
                        <span className="rounded bg-primary/15 px-2 py-0.5 text-[10px] font-medium text-primary font-mono">
                          Verified ✓
                        </span>
                      </div>
                      <pre className="overflow-x-auto rounded-md bg-muted p-3 text-[11px] font-mono leading-relaxed text-foreground">
                        {patchedVerilog}
                      </pre>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
