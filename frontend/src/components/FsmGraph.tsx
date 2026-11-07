import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { GitBranch, Info } from "lucide-react";
import type { FsmGraphResponse, FsmStateNode } from "@/lib/api";

interface Props {
  data: FsmGraphResponse;
}

interface PositionedNode extends FsmStateNode {
  x: number;
  y: number;
}

/**
 * Compact, deterministic FSM state-transition graph.
 * Nodes arranged on a circle; flagged states glow red.
 * Edges drawn as quadratic curves with arrowheads; self-loops as small arcs.
 */
export default function FsmGraph({ data }: Props) {
  const [hovered, setHovered] = useState<string | null>(null);

  const width = 720;
  const height = 460;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) / 2 - 70;
  const nodeR = 34;

  const positioned: PositionedNode[] = useMemo(() => {
    const n = data.states.length;
    if (n === 0) return [];
    // Place reset state at the top
    const resetIdx = Math.max(
      0,
      data.states.findIndex((s) => s.name === data.reset_state)
    );
    return data.states.map((s, i) => {
      const idx = (i - resetIdx + n) % n;
      const angle = (idx / n) * 2 * Math.PI - Math.PI / 2;
      return {
        ...s,
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });
  }, [data, cx, cy, radius]);

  const byName = useMemo(() => {
    const map = new Map<string, PositionedNode>();
    positioned.forEach((n) => map.set(n.name, n));
    return map;
  }, [positioned]);

  // Group parallel edges so they fan out instead of overlapping
  const edges = useMemo(() => {
    const buckets = new Map<string, number>();
    return data.transitions.map((t) => {
      const key = `${t.src}->${t.dst}`;
      const idx = buckets.get(key) ?? 0;
      buckets.set(key, idx + 1);
      return { ...t, parallelIdx: idx };
    });
  }, [data.transitions]);

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-primary" />
          <span className="font-mono text-xs uppercase tracking-widest text-muted-foreground">
            FSM State Graph
          </span>
        </div>
        <div className="flex items-center gap-3 font-mono text-[10px] text-muted-foreground">
          <Legend color="hsl(160 100% 45%)" label="Safe" />
          <Legend color="hsl(0 72% 51%)" label="Flagged" />
          <Legend color="hsl(195 100% 55%)" label="Reset" stroke />
        </div>
      </div>
      <div className="overflow-x-auto p-2">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ maxHeight: 460 }}>
          <defs>
            <marker
              id="arrow-safe"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="hsl(160 100% 45%)" />
            </marker>
            <marker
              id="arrow-flagged"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M0,0 L10,5 L0,10 z" fill="hsl(0 72% 51%)" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((e, i) => {
            const src = byName.get(e.src);
            const dst = byName.get(e.dst);
            if (!src || !dst) return null;
            const isFlagged = src.flagged && dst.flagged;
            const stroke = isFlagged ? "hsl(0 72% 51%)" : "hsl(160 100% 35%)";
            const marker = isFlagged ? "url(#arrow-flagged)" : "url(#arrow-safe)";
            const isHi = hovered && (hovered === e.src || hovered === e.dst);

            if (e.src === e.dst) {
              // Self-loop: small arc above the node
              const lx = src.x;
              const ly = src.y - nodeR - 4;
              return (
                <g key={i} opacity={hovered && !isHi ? 0.2 : 1}>
                  <path
                    d={`M ${lx - 10} ${ly} C ${lx - 28} ${ly - 32}, ${lx + 28} ${ly - 32}, ${lx + 10} ${ly}`}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={isHi ? 2 : 1.2}
                    markerEnd={marker}
                  />
                  {e.condition && e.condition !== "always" && (
                    <text
                      x={lx}
                      y={ly - 30}
                      textAnchor="middle"
                      className="font-mono"
                      fontSize="9"
                      fill="hsl(220 10% 65%)"
                    >
                      {e.condition}
                    </text>
                  )}
                </g>
              );
            }

            // Compute curve offset for parallel edges
            const dx = dst.x - src.x;
            const dy = dst.y - src.y;
            const len = Math.hypot(dx, dy) || 1;
            // Unit normal
            const nx = -dy / len;
            const ny = dx / len;
            const offset = 26 * (e.parallelIdx % 2 === 0 ? e.parallelIdx / 2 + 0.4 : -(Math.floor(e.parallelIdx / 2) + 0.4));
            // Shrink endpoints so arrowhead lands on node border
            const ux = dx / len;
            const uy = dy / len;
            const sx = src.x + ux * nodeR;
            const sy = src.y + uy * nodeR;
            const tx = dst.x - ux * (nodeR + 4);
            const ty = dst.y - uy * (nodeR + 4);
            const mx = (sx + tx) / 2 + nx * offset;
            const my = (sy + ty) / 2 + ny * offset;
            const labelX = mx;
            const labelY = my - 4;

            return (
              <g key={i} opacity={hovered && !isHi ? 0.18 : 1}>
                <path
                  d={`M ${sx} ${sy} Q ${mx} ${my} ${tx} ${ty}`}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={isHi ? 2.2 : 1.4}
                  markerEnd={marker}
                />
                {e.condition && e.condition !== "always" && (
                  <text
                    x={labelX}
                    y={labelY}
                    textAnchor="middle"
                    className="font-mono"
                    fontSize="9"
                    fill="hsl(220 10% 65%)"
                  >
                    {e.condition.length > 18 ? e.condition.slice(0, 17) + "…" : e.condition}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {positioned.map((n) => {
            const isReset = n.name === data.reset_state;
            const isHi = hovered === n.name;
            const fill = n.flagged ? "hsl(0 72% 51% / 0.18)" : "hsl(160 100% 40% / 0.14)";
            const stroke = n.flagged ? "hsl(0 72% 51%)" : "hsl(160 100% 45%)";
            return (
              <motion.g
                key={n.name}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
                onMouseEnter={() => setHovered(n.name)}
                onMouseLeave={() => setHovered(null)}
                style={{ cursor: "pointer" }}
              >
                {isReset && (
                  <circle
                    cx={n.x}
                    cy={n.y}
                    r={nodeR + 5}
                    fill="none"
                    stroke="hsl(195 100% 55%)"
                    strokeWidth={1}
                    strokeDasharray="4 3"
                  />
                )}
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={nodeR}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={isHi ? 2.4 : 1.6}
                  style={{
                    filter: n.flagged
                      ? "drop-shadow(0 0 8px hsl(0 72% 51% / 0.55))"
                      : isHi
                        ? "drop-shadow(0 0 6px hsl(160 100% 45% / 0.45))"
                        : undefined,
                  }}
                />
                <text
                  x={n.x}
                  y={n.y - 2}
                  textAnchor="middle"
                  className="font-mono"
                  fontSize="11"
                  fontWeight="600"
                  fill={n.flagged ? "hsl(0 72% 70%)" : "hsl(160 80% 80%)"}
                >
                  {n.name.length > 9 ? n.name.slice(0, 8) + "…" : n.name}
                </text>
                <text
                  x={n.x}
                  y={n.y + 11}
                  textAnchor="middle"
                  className="font-mono"
                  fontSize="9"
                  fill="hsl(220 10% 60%)"
                >
                  r={n.risk_score.toFixed(2)}
                </text>
              </motion.g>
            );
          })}
        </svg>
      </div>

      {hovered && byName.get(hovered) && (
        <div className="flex items-start gap-2 border-t border-border px-4 py-2 text-xs font-mono text-muted-foreground">
          <Info className="h-3 w-3 mt-0.5 shrink-0" />
          <NodeHoverDetails node={byName.get(hovered)!} />
        </div>
      )}
    </div>
  );
}

function NodeHoverDetails({ node }: { node: PositionedNode }) {
  return (
    <span>
      <strong className="text-foreground">{node.name}</strong>
      {" · "}
      risk {node.risk_score.toFixed(3)}
      {" · "}
      in° {node.in_degree} / out° {node.out_degree}
      {node.self_loop ? " · self-loop" : ""}
      {node.flagged && node.cwe ? ` · ${node.cwe}: ${node.cwe_label}` : ""}
      {node.flagged && node.recommended_fix ? ` · fix: ${node.recommended_fix}` : ""}
    </span>
  );
}

function Legend({ color, label, stroke }: { color: string; label: string; stroke?: boolean }) {
  return (
    <span className="inline-flex items-center gap-1">
      <span
        className="inline-block h-2.5 w-2.5 rounded-full"
        style={
          stroke
            ? { border: `1.5px dashed ${color}`, background: "transparent" }
            : { background: color }
        }
      />
      {label}
    </span>
  );
}
