import { motion } from "framer-motion";
import { ShieldCheck, ShieldAlert, Bug, Wrench, Activity, CheckCircle2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from "recharts";
import type { AnalysisResults } from "@/types/pipeline";

interface Props {
  results: AnalysisResults;
}

const AnalysisResultsView = ({ results }: Props) => {
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
      </div>

      {/* State Details Table */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
            State Analysis Detail
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
                    <span className={state.flagged ? "text-destructive" : "text-safe"}>
                      {state.riskScore.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {state.flagged ? (
                      <span className="inline-flex items-center gap-1 text-destructive">
                        <ShieldAlert className="h-3 w-3" /> WEAK
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-safe">
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
