import { motion } from "framer-motion";
import {
  Activity,
  Bug,
  ShieldCheck,
  ShieldAlert,
  Wrench,
  CheckCircle2,
} from "lucide-react";
import {
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { FsmGraphResponse } from "@/lib/api";

interface Props {
  data: FsmGraphResponse;
}

export default function AnalysisDashboard({ data }: Props) {
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="space-y-5"
    >
      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="Total States"
          value={total}
          tone="primary"
        />
        <StatCard
          icon={<Bug className="h-4 w-4" />}
          label="Flagged Weak"
          value={flagged}
          tone={flagged > 0 ? "destructive" : "primary"}
        />
        <StatCard
          icon={<ShieldCheck className="h-4 w-4" />}
          label="Security Score"
          value={`${securityScore}%`}
          tone={securityScore >= 70 ? "primary" : "destructive"}
        />
        <StatCard
          icon={<CheckCircle2 className="h-4 w-4" />}
          label="Module"
          value={data.module || "FSM"}
          tone="primary"
        />
      </div>

      {/* Risk bar chart */}
      <div className="rounded-lg border border-border bg-card p-4">
        <h3 className="mb-3 font-mono text-xs font-semibold uppercase tracking-widest text-muted-foreground">
          Per-State Risk Scores (GNN Output)
        </h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={riskData}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 15% 18%)" />
            <XAxis
              dataKey="name"
              tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "ui-monospace" }}
            />
            <YAxis
              domain={[0, 1]}
              tick={{ fill: "hsl(220 10% 50%)", fontSize: 10, fontFamily: "ui-monospace" }}
            />
            <Tooltip
              contentStyle={{
                background: "hsl(220 18% 10%)",
                border: "1px solid hsl(220 15% 18%)",
                borderRadius: 6,
                fontFamily: "ui-monospace",
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

      {/* State details table */}
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
              {data.states.map((s, i) => (
                <motion.tr
                  key={s.name}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="border-b border-border/50 hover:bg-secondary/30"
                >
                  <td className="px-4 py-2 font-semibold text-foreground">{s.name}</td>
                  <td className="px-4 py-2">
                    <span className={s.flagged ? "text-destructive" : "text-primary"}>
                      {s.risk_score.toFixed(2)}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    {s.flagged ? (
                      <span className="inline-flex items-center gap-1 text-destructive">
                        <ShieldAlert className="h-3 w-3" /> WEAK
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-primary">
                        <ShieldCheck className="h-3 w-3" /> SAFE
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-foreground">{s.in_degree}</td>
                  <td className="px-4 py-2 text-foreground">{s.out_degree}</td>
                  <td className="px-4 py-2 text-foreground">{s.self_loop ? "Yes" : "No"}</td>
                  <td className="px-4 py-2 text-foreground">{s.reset_distance}</td>
                  <td className="px-4 py-2">
                    {s.recommended_fix ? (
                      <span className="inline-flex items-center gap-1 text-secondary">
                        <Wrench className="h-3 w-3" /> {s.recommended_fix}
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
    </motion.div>
  );
}

function StatCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  tone: "primary" | "destructive";
}) {
  const toneCls =
    tone === "destructive"
      ? "border-destructive/30 text-destructive"
      : "border-primary/30 text-primary";

  return (
    <div className={`rounded-lg border bg-card p-3 ${toneCls}`}>
      <div className="mb-1 flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="font-mono text-[10px] uppercase tracking-wider">{label}</span>
      </div>
      <p className="font-mono text-2xl font-bold truncate">{value}</p>
    </div>
  );
}
