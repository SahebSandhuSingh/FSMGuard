import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert, Bug, Wrench, Activity, CheckCircle2, Shield, BrainCircuit } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";
import type { AnalysisResults } from "@/types/pipeline";
import FsmGraph from "./FsmGraph";
import type { FsmGraphResponse } from "@/lib/api";

interface Props {
  results: AnalysisResults;
  fsmGraph: FsmGraphResponse | null;
}

const AnalysisResultsView = ({ results, fsmGraph }: Props) => {
  const riskData = results.states.map((s) => ({
    name: s.name,
    risk: s.riskScore,
    flagged: s.flagged,
  }));

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="Total States"
          value={results.totalStates}
          color="primary"
        />
        <StatCard
          icon={<Bug className="h-4 w-4" />}
          label="Flagged Weak"
          value={results.flaggedCount}
          color="destructive"
        />
        <StatCard
          icon={<ShieldCheck className="h-4 w-4" />}
          label="Security Score"
          value={`${results.securityScore}%`}
          color={results.securityScore >= 70 ? "primary" : "warning"}
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="Patch Verified"
          value={results.patchVerified ? "PASS" : "FAIL"}
          color={results.patchVerified ? "primary" : "destructive"}
        />
      </div>

      {/* GNN Vulnerability Identification Section */}
      <div className="rounded-xl border border-primary/20 bg-card/30 p-5 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 border-b border-border/60 pb-3">
          <BrainCircuit className="h-5 w-5 text-primary" />
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground font-mono">
              GNN Vulnerability Identification
            </h2>
            <p className="text-[10px] text-muted-foreground font-mono leading-tight">
              Graph Neural Network topology analysis flags high-risk states and maps control-flow vulnerabilities.
            </p>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid gap-4 lg:grid-cols-2">
          {/* Risk Score Bar Chart */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              Per-State Risk Scores (GNN Output)
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
                <XAxis dataKey="name" tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <YAxis domain={[0, 1]} tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(220 18% 10%)",
                    border: "1px solid hsl(220 15% 18%)",
                    borderRadius: 6,
                    fontFamily: "JetBrains Mono",
                    fontSize: 12,
                    color: "hsl(160 40% 90%)",
                  }}
                />
                <Bar dataKey="risk" radius={[3, 3, 0, 0]}>
                  {riskData.map((entry, idx) => (
                    <Cell
                      key={idx}
                      fill={entry.flagged ? "hsl(0 72% 51%)" : "hsl(160 100% 40%)"}
                      opacity={0.85}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* FSM Graph inside GNN Section */}
          {fsmGraph ? (
            <FsmGraph data={fsmGraph} />
          ) : (
            <div className="flex h-[280px] items-center justify-center rounded-lg border border-border bg-card/50 font-mono text-xs text-muted-foreground">
              Awaiting graph structural mapping...
            </div>
          )}
        </div>
      </div>

      {/* RL Protection Agent Section */}
      <div className="rounded-xl border border-accent/20 bg-card/30 p-5 space-y-4 shadow-xl">
        <div className="flex items-center gap-2 border-b border-border/60 pb-3">
          <Shield className="h-5 w-5 text-accent" />
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-foreground font-mono">
              RL Protection Agent (PPO)
            </h2>
            <p className="text-[10px] text-muted-foreground font-mono leading-tight">
              Policy network trained via PPO converges on optimal mitigations to secure vulnerable states.
            </p>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          {/* RL Reward Curve */}
          <div className="rounded-lg border border-border bg-card p-4">
            <h3 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              RL Agent Reward Convergence (PPO)
            </h3>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={results.rewardHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
                <XAxis dataKey="episode" tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <YAxis domain={[0, 1]} tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                <Tooltip
                  contentStyle={{
                    background: "hsl(220 18% 10%)",
                    border: "1px solid hsl(220 15% 18%)",
                    borderRadius: 6,
                    fontFamily: "JetBrains Mono",
                    fontSize: 12,
                    color: "hsl(160 40% 90%)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="reward"
                  stroke="hsl(280 80% 55%)"
                  strokeWidth={2}
                  dot={{ fill: "hsl(280 80% 55%)", r: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Agent Specifications Panel */}
          <div className="rounded-lg border border-border bg-card p-4 flex flex-col justify-between font-mono text-xs space-y-3">
            <h3 className="font-semibold uppercase tracking-widest text-muted-foreground text-[11px]">
              Agent Specifications
            </h3>
            <div className="space-y-2 text-[11px] flex-1 mt-2">
              <div className="flex justify-between border-b border-border/50 pb-1.5">
                <span className="text-muted-foreground">Algorithm</span>
                <span className="text-foreground font-semibold">PPO (Proximal Policy Optimization)</span>
              </div>
              <div className="flex justify-between border-b border-border/50 pb-1.5">
                <span className="text-muted-foreground">Framework</span>
                <span className="text-foreground font-semibold">Stable Baselines3</span>
              </div>
              <div className="flex justify-between border-b border-border/50 pb-1.5">
                <span className="text-muted-foreground">Observation Space</span>
                <span className="text-foreground font-semibold">Box(30) (Topology + CWE features)</span>
              </div>
              <div className="flex justify-between border-b border-border/50 pb-1.5">
                <span className="text-muted-foreground">Action Space</span>
                <span className="text-foreground font-semibold">MultiDiscrete [4×3×2]</span>
              </div>
              <div className="flex justify-between pb-1">
                <span className="text-muted-foreground">Formal Proof Solver</span>
                <span className="text-primary font-semibold">SymbiYosys / Z3 SMT</span>
              </div>
            </div>
            <div className="rounded bg-accent/5 border border-accent/15 p-2.5 text-[10px] text-accent/90 leading-relaxed font-sans mt-2">
              <strong>Agent Strategy:</strong> PPO agent evaluates the isolated state-transition subgraph to apply optimal countermeasures (Guard input, Prune transition, Re-encode registers, Deadlock trap) maximizing reward under formal constraints.
            </div>
          </div>
        </div>

        {/* State Details Table */}
        <div className="rounded-lg border border-border bg-card">
          <div className="border-b border-border px-4 py-3 bg-muted/20">
            <h3 className="font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
              State Patching & Verification Details
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full font-mono text-xs">
              <thead>
                <tr className="border-b border-border text-left text-muted-foreground">
                  <th className="px-4 py-2">State</th>
                  <th className="px-4 py-2">Risk</th>
                  <th className="px-4 py-2">Status</th>
                  <th className="px-4 py-2">In°</th>
                  <th className="px-4 py-2">Out°</th>
                  <th className="px-4 py-2">Self-Loop</th>
                  <th className="px-4 py-2">Reset Dist</th>
                  <th className="px-4 py-2">RL Fix</th>
                </tr>
              </thead>
              <tbody>
                {results.states.map((state, i) => (
                  <motion.tr
                    key={state.name}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="border-b border-border/50 hover:bg-secondary/30"
                  >
                    <td className="px-4 py-2 font-semibold text-card-foreground">{state.name}</td>
                    <td className="px-4 py-2">
                      <span className={state.flagged ? "text-destructive" : "text-primary"}>
                        {state.riskScore.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-2">
                      {state.flagged ? (
                        <span className="inline-flex items-center gap-1 text-destructive">
                          <ShieldAlert className="h-3 w-3" /> WEAK
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-primary">
                          <ShieldCheck className="h-3 w-3" /> SAFE
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-card-foreground">{state.inDegree}</td>
                    <td className="px-4 py-2 text-card-foreground">{state.outDegree}</td>
                    <td className="px-4 py-2 text-card-foreground">{state.selfLoop ? "Yes" : "No"}</td>
                    <td className="px-4 py-2 text-card-foreground">{state.resetDistance}</td>
                    <td className="px-4 py-2">
                      {state.fix ? (
                        <span className="inline-flex items-center gap-1 text-accent">
                          <Wrench className="h-3 w-3" /> {state.fix}
                        </span>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

function StatCard({
  icon,
  label,
  value,
  color,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    primary: "border-primary/30 text-primary",
    destructive: "border-destructive/30 text-destructive",
    warning: "border-warning/30 text-warning",
  };

  return (
    <div className={`rounded-lg border bg-card p-3 ${colorMap[color] || colorMap.primary}`}>
      <div className="mb-1 flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="font-mono text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <p className="font-display text-2xl font-bold">{value}</p>
    </div>
  );
}

export default AnalysisResultsView;
