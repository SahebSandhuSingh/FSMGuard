import { useState, useEffect, useRef } from "react";

// ── Colour tokens ──────────────────────────────────────────────────────────────
const C = {
  bg:       "#080c10",
  surface:  "#0d1117",
  border:   "#1e2d3d",
  borderHi: "#2a9d8f",
  primary:  "#2a9d8f",
  accent:   "#e76f51",
  warn:     "#e9c46a",
  muted:    "#4a6075",
  fg:       "#cdd9e5",
  fgDim:    "#7a9bb5",
  green:    "#4caf87",
};

// ── Tiny helpers ───────────────────────────────────────────────────────────────
const cx = (...cls) => cls.filter(Boolean).join(" ");

// ── Global CSS (injected once) ─────────────────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: ${C.bg};
    color: ${C.fg};
    font-family: 'Share Tech Mono', monospace;
    min-height: 100vh;
  }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: ${C.bg}; }
  ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 2px; }

  @keyframes scanline {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
  }
  @keyframes blink { 0%,49%{opacity:1} 50%,100%{opacity:0} }
  @keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0 ${C.primary}55; }
    70%  { box-shadow: 0 0 0 8px transparent; }
    100% { box-shadow: 0 0 0 0 transparent; }
  }
  @keyframes fadein {
    from { opacity:0; transform:translateY(12px); }
    to   { opacity:1; transform:translateY(0); }
  }
  @keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes growbar { from { width:0; } }

  .scan-overlay {
    pointer-events: none;
    position: fixed; inset: 0; z-index: 9999; overflow: hidden;
  }
  .scan-overlay::after {
    content: '';
    position: absolute; left: 0; top: 0;
    width: 100%; height: 60px;
    background: linear-gradient(to bottom, transparent, ${C.primary}08, transparent);
    animation: scanline 6s linear infinite;
  }

  .glow-text {
    text-shadow: 0 0 12px ${C.primary}88, 0 0 28px ${C.primary}44;
  }
  .glow-accent {
    text-shadow: 0 0 10px ${C.accent}aa;
  }
  .glow-box {
    box-shadow: 0 0 0 1px ${C.primary}33, 0 0 20px ${C.primary}18;
  }
  .fadein { animation: fadein 0.45s ease both; }

  textarea:focus { outline: none; }
  button:focus-visible { outline: 2px solid ${C.primary}; outline-offset: 2px; }

  .bar-anim { animation: growbar 0.8s ease both; }
`;


function useGlobalCss(css: string): void {
  useEffect(() => {
    const el = document.createElement("style");
    el.textContent = css;
    document.head.appendChild(el);

    return () => {
      document.head.removeChild(el);
    };
  }, [css]);
}

// ── Pipeline stage definitions ─────────────────────────────────────────────────
const STAGES = [
  { id: 1, label: "PARSE",       desc: "Tokenise Verilog AST" },
  { id: 2, label: "EXTRACT",     desc: "Identify FSM states & transitions" },
  { id: 3, label: "GRAPH",       desc: "Build GNN state graph" },
  { id: 4, label: "EMBED",       desc: "Node feature embedding" },
  { id: 5, label: "INFER",       desc: "GNN forward pass" },
  { id: 6, label: "SCORE",       desc: "Risk scoring per state" },
  { id: 7, label: "RL INIT",     desc: "Initialise protection agent" },
  { id: 8, label: "POLICY",      desc: "Run RL policy optimisation" },
  { id: 9, label: "PATCH",       desc: "Apply countermeasures" },
  { id: 10, label: "VERIFY",     desc: "Formal patch verification" },
];

// ── Mock result generator ──────────────────────────────────────────────────────
function generateResults(code) {
  const names = ["IDLE","INIT","AUTH","PROCESS","WAIT","TRANSMIT","DONE","ERROR","RESET","LOCKED"];
  const count = Math.max(5, (code.match(/\bS\d+|IDLE|INIT|READY|WAIT|DONE|ERROR/gi)||[]).length);
  const states = Array.from({ length: Math.min(count, 10) }, (_, i) => {
    const risk = parseFloat((Math.random()).toFixed(2));
    return {
      name: names[i % names.length],
      riskScore: risk,
      flagged: risk > 0.6,
      inDegree:  Math.floor(Math.random() * 5) + 1,
      outDegree: Math.floor(Math.random() * 5) + 1,
      selfLoop:  Math.random() > 0.7,
      resetDist: Math.floor(Math.random() * 4),
      fix: risk > 0.6
        ? ["Guard Insertion","Deadlock Trap","Re-encoding","Transition Pruning"][Math.floor(Math.random()*4)]
        : null,
    };
  });
  return {
    states,
    totalStates: states.length,
    flaggedCount: states.filter(s => s.flagged).length,
    securityScore: Math.round((1 - states.filter(s=>s.flagged).length / states.length) * 100),
    patchVerified: true,
    rewardHistory: Array.from({length:20},(_,i)=>({
      episode: i+1,
      reward: Math.min(0.97, 0.18 + i*0.042 + (Math.random()-0.5)*0.08),
    })),
  };
}

// ─────────────────────────────────────────────────────────────────────────────
//  Sub-components
// ─────────────────────────────────────────────────────────────────────────────

// ── Header ────────────────────────────────────────────────────────────────────
function Header({ status }) {
  const statusMap = {
    idle:     { label: "AWAITING INPUT",    color: C.muted },
    running:  { label: "ANALYZING ···",     color: C.warn },
    complete: { label: "ANALYSIS COMPLETE", color: C.green },
  };
  const s = statusMap[status];
  return (
    <header style={{
      borderBottom: `1px solid ${C.border}`,
      background: `${C.surface}cc`,
      backdropFilter: "blur(8px)",
      position: "sticky", top: 0, zIndex: 100,
      padding: "14px 24px",
    }}>
      <div style={{ maxWidth: 1200, margin: "0 auto", display:"flex", alignItems:"center", gap:14 }}>
        {/* Logo mark */}
        <div style={{
          width: 40, height: 40, borderRadius: 8,
          border: `1px solid ${C.primary}55`,
          background: `${C.primary}18`,
          display:"flex", alignItems:"center", justifyContent:"center",
          animation: "pulse-ring 2.5s infinite",
        }}>
          <ShieldIcon size={18} color={C.primary} />
        </div>

        <div>
          <div style={{
            fontFamily:"'Orbitron',sans-serif",
            fontWeight:900, fontSize:15, letterSpacing:"0.08em",
            color: C.fg,
          }} className="glow-text">
            FSM SECURITY PIPELINE
          </div>
          <div style={{ fontSize:10, color: C.fgDim, letterSpacing:"0.12em" }}>
            GNN ANALYZER · RL PROTECTION AGENT
          </div>
        </div>

        <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:8 }}>
          <span style={{
            width:7, height:7, borderRadius:"50%",
            background: s.color,
            boxShadow: `0 0 6px ${s.color}`,
            display:"inline-block",
            animation: status==="running" ? "blink 1s infinite" : "none",
          }}/>
          <span style={{ fontSize:11, color: s.color, letterSpacing:"0.1em" }}>{s.label}</span>
        </div>
      </div>
    </header>
  );
}

// ── Verilog Input ─────────────────────────────────────────────────────────────
const PLACEHOLDER = `// Paste your Verilog FSM here
module traffic_light (
  input clk, rst,
  output reg [1:0] state
);
  parameter IDLE=0, GREEN=1, YELLOW=2, RED=3;
  always @(posedge clk)
    if (rst) state <= IDLE;
    else case(state)
      IDLE:   state <= GREEN;
      GREEN:  state <= YELLOW;
      YELLOW: state <= RED;
      RED:    state <= IDLE;
    endcase
endmodule`;

function VerilogInput({ onSubmit, isRunning }) {
  const [code, setCode] = useState("");
  const lineCount = (code || PLACEHOLDER).split("\n").length;

  return (
    <Card>
      <CardLabel>VERILOG SOURCE</CardLabel>

      <div style={{ display:"flex", gap:0, position:"relative" }}>
        {/* Line numbers */}
        <div style={{
          padding:"12px 10px",
          borderRight: `1px solid ${C.border}`,
          color: C.muted, fontSize:12, lineHeight:"1.6em",
          userSelect:"none", minWidth:40, textAlign:"right",
          background: `${C.bg}88`,
        }}>
          {Array.from({length:lineCount},(_,i)=>(
            <div key={i}>{i+1}</div>
          ))}
        </div>

        <textarea
          value={code}
          onChange={e => setCode(e.target.value)}
          placeholder={PLACEHOLDER}
          rows={12}
          style={{
            flex:1, padding:"12px 14px",
            background:"transparent",
            color: C.fg, fontSize:12.5,
            lineHeight:"1.6em", resize:"vertical",
            border:"none", fontFamily:"inherit",
            caretColor: C.primary,
          }}
        />
      </div>

      <div style={{
        borderTop: `1px solid ${C.border}`,
        padding:"10px 14px",
        display:"flex", alignItems:"center", justifyContent:"space-between",
      }}>
        <span style={{ fontSize:11, color: C.muted }}>
          {code.length > 0 ? `${code.split("\n").length} lines · ${code.length} chars` : "ready"}
        </span>
        <button
          onClick={() => onSubmit(code || PLACEHOLDER)}
          disabled={isRunning}
          style={{
            padding:"8px 22px",
            background: isRunning ? C.muted : C.primary,
            border:"none", borderRadius:4,
            color: C.bg, fontFamily:"inherit",
            fontSize:12, fontWeight:700,
            letterSpacing:"0.1em", cursor: isRunning ? "default" : "pointer",
            transition:"all 0.2s",
            display:"flex", alignItems:"center", gap:8,
          }}
        >
          {isRunning ? (
            <><SpinIcon size={13}/> ANALYZING</>
          ) : (
            <><PlayIcon size={13}/> RUN ANALYSIS</>
          )}
        </button>
      </div>
    </Card>
  );
}

// ── Pipeline Stages ───────────────────────────────────────────────────────────
function PipelineStages({ currentStage }) {
  return (
    <Card>
      <CardLabel>PIPELINE EXECUTION</CardLabel>
      <div style={{
        display:"grid",
        gridTemplateColumns:"repeat(5,1fr)",
        gap:8, padding:"4px 0 8px",
      }}>
        {STAGES.map(s => {
          const done    = currentStage > s.id;
          const active  = currentStage === s.id;
          const pending = currentStage < s.id;
          return (
            <div key={s.id} style={{
              padding:"10px 10px 8px",
              borderRadius:6,
              border: `1px solid ${active ? C.primary : done ? C.primary+"44" : C.border}`,
              background: active ? `${C.primary}14` : done ? `${C.primary}08` : "transparent",
              transition:"all 0.35s",
              position:"relative", overflow:"hidden",
            }}>
              {/* Active shimmer */}
              {active && (
                <div style={{
                  position:"absolute", inset:0,
                  background:`linear-gradient(90deg, transparent 0%, ${C.primary}22 50%, transparent 100%)`,
                  backgroundSize:"200% 100%",
                  animation:"shimmer 1.4s linear infinite",
                }}/>
              )}

              <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:4 }}>
                <div style={{
                  width:18, height:18, borderRadius:"50%",
                  border:`1px solid ${done?C.primary:active?C.primary:C.border}`,
                  background: done?C.primary:active?`${C.primary}33`:"transparent",
                  display:"flex", alignItems:"center", justifyContent:"center",
                  fontSize:9, color: done?C.bg:active?C.primary:C.muted,
                  flexShrink:0,
                }}>
                  {done ? "✓" : s.id}
                </div>
                <span style={{
                  fontSize:10, fontWeight:700, letterSpacing:"0.08em",
                  color: done ? C.primary : active ? C.primary : C.muted,
                  fontFamily:"'Orbitron',sans-serif",
                }}>{s.label}</span>
              </div>
              <div style={{ fontSize:9.5, color: pending ? C.muted+"88" : C.fgDim, lineHeight:"1.4em" }}>
                {s.desc}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

// ── Results ───────────────────────────────────────────────────────────────────
function AnalysisResults({ results }) {
  const { states, totalStates, flaggedCount, securityScore, patchVerified, rewardHistory } = results;
  const scoreColor = securityScore >= 70 ? C.green : securityScore >= 40 ? C.warn : C.accent;

  return (
    <div className="fadein" style={{ display:"flex", flexDirection:"column", gap:16 }}>
      {/* Scorecard row */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:12 }}>
        {[
          { label:"SECURITY SCORE",  value:`${securityScore}%`,  color:scoreColor },
          { label:"TOTAL STATES",    value:totalStates,           color:C.primary },
          { label:"FLAGGED STATES",  value:flaggedCount,          color:flaggedCount>0?C.accent:C.green },
          { label:"PATCH VERIFIED",  value:patchVerified?"PASS":"FAIL", color:patchVerified?C.green:C.accent },
        ].map(m => (
          <Card key={m.label} style={{ textAlign:"center", padding:"18px 12px" }}>
            <div style={{ fontSize:9.5, color:C.muted, letterSpacing:"0.14em", marginBottom:8 }}>{m.label}</div>
            <div style={{
              fontFamily:"'Orbitron',sans-serif", fontWeight:900,
              fontSize:28, color:m.color,
              textShadow:`0 0 18px ${m.color}88`,
            }}>{m.value}</div>
          </Card>
        ))}
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        {/* State risk table */}
        <Card>
          <CardLabel>STATE RISK ANALYSIS</CardLabel>
          <div style={{ overflowX:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11.5 }}>
              <thead>
                <tr style={{ borderBottom:`1px solid ${C.border}` }}>
                  {["STATE","RISK","IN","OUT","LOOP","DIST","FIX"].map(h=>(
                    <th key={h} style={{
                      padding:"6px 8px", textAlign:"left",
                      color:C.muted, fontWeight:700,
                      letterSpacing:"0.1em", fontSize:10,
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {states.map((s,i) => {
                  const rc = s.riskScore > 0.6 ? C.accent : s.riskScore > 0.35 ? C.warn : C.green;
                  return (
                    <tr key={i} style={{
                      borderBottom:`1px solid ${C.border}44`,
                      background: s.flagged ? `${C.accent}08` : "transparent",
                      transition:"background 0.2s",
                    }}>
                      <td style={{ padding:"7px 8px", color:C.fg, fontWeight:700 }}>{s.name}</td>
                      <td style={{ padding:"7px 8px" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:6 }}>
                          <div style={{
                            height:4, width:52, background:C.border, borderRadius:2,
                          }}>
                            <div style={{
                              height:"100%", width:`${s.riskScore*100}%`,
                              background:rc, borderRadius:2,
                            }} className="bar-anim"/>
                          </div>
                          <span style={{ color:rc, fontSize:10 }}>{(s.riskScore*100).toFixed(0)}%</span>
                        </div>
                      </td>
                      <td style={{ padding:"7px 8px", color:C.fgDim }}>{s.inDegree}</td>
                      <td style={{ padding:"7px 8px", color:C.fgDim }}>{s.outDegree}</td>
                      <td style={{ padding:"7px 8px", color:s.selfLoop?C.warn:C.muted }}>{s.selfLoop?"●":"○"}</td>
                      <td style={{ padding:"7px 8px", color:C.fgDim }}>{s.resetDist}</td>
                      <td style={{ padding:"7px 8px" }}>
                        {s.fix
                          ? <span style={{
                              fontSize:9.5, padding:"2px 6px", borderRadius:3,
                              background:`${C.accent}22`, color:C.accent,
                              border:`1px solid ${C.accent}44`,
                            }}>{s.fix}</span>
                          : <span style={{ color:C.muted, fontSize:10 }}>—</span>
                        }
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>

        {/* RL Reward chart */}
        <Card>
          <CardLabel>RL AGENT REWARD HISTORY</CardLabel>
          <RewardChart data={rewardHistory} />
          <div style={{
            marginTop:12, padding:"10px 12px",
            background:`${C.primary}0d`, borderRadius:6,
            border:`1px solid ${C.primary}22`,
            fontSize:11, color:C.fgDim, lineHeight:"1.6em",
          }}>
            <span style={{ color:C.primary, fontWeight:700 }}>CONVERGENCE ·</span>{" "}
            Agent reached peak reward of{" "}
            <span style={{ color:C.green }}>
              {(Math.max(...rewardHistory.map(r=>r.reward))*100).toFixed(1)}%
            </span>{" "}
            at episode{" "}
            <span style={{ color:C.green }}>
              {rewardHistory.reduce((best,r,i)=>r.reward>rewardHistory[best].reward?i:best,0)+1}
            </span>.
            Countermeasures applied and formally verified.
          </div>
        </Card>
      </div>
    </div>
  );
}

// ── Reward sparkline chart (pure SVG) ─────────────────────────────────────────
function RewardChart({ data }) {
  const W=480, H=140, PAD={top:12,right:12,bottom:28,left:34};
  const iw=W-PAD.left-PAD.right, ih=H-PAD.top-PAD.bottom;
  const xs = i => PAD.left + (i/(data.length-1))*iw;
  const ys = v => PAD.top + ih - (v*ih);
  const pts = data.map((d,i)=>`${xs(i)},${ys(d.reward)}`).join(" ");
  const area = `M${xs(0)},${ys(0)} ` + data.map((d,i)=>`L${xs(i)},${ys(d.reward)}`).join(" ")
    + ` L${xs(data.length-1)},${PAD.top+ih} L${xs(0)},${PAD.top+ih} Z`;

  // y axis ticks
  const yTicks = [0,0.25,0.5,0.75,1.0];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width:"100%", height:"auto" }}>
      <defs>
        <linearGradient id="rg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={C.primary} stopOpacity="0.35"/>
          <stop offset="100%" stopColor={C.primary} stopOpacity="0"/>
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {yTicks.map(t=>(
        <g key={t}>
          <line x1={PAD.left} x2={W-PAD.right}
            y1={ys(t)} y2={ys(t)}
            stroke={C.border} strokeWidth="1" strokeDasharray="3 4"/>
          <text x={PAD.left-6} y={ys(t)+4} textAnchor="end"
            fill={C.muted} fontSize="9" fontFamily="Share Tech Mono">
            {t.toFixed(2)}
          </text>
        </g>
      ))}

      {/* X axis labels */}
      {[1,5,10,15,20].map(ep=>(
        <text key={ep}
          x={xs(ep-1)} y={H-6}
          textAnchor="middle" fill={C.muted} fontSize="9" fontFamily="Share Tech Mono">
          {ep}
        </text>
      ))}

      {/* Area fill */}
      <path d={area} fill="url(#rg)"/>

      {/* Line */}
      <polyline points={pts} fill="none" stroke={C.primary} strokeWidth="2"
        strokeLinejoin="round" strokeLinecap="round"/>

      {/* Dots for each point */}
      {data.map((d,i)=>(
        <circle key={i} cx={xs(i)} cy={ys(d.reward)} r="2.5"
          fill={C.bg} stroke={C.primary} strokeWidth="1.5"/>
      ))}

      {/* Peak marker */}
      {(() => {
        const peak = data.reduce((b,d,i)=>d.reward>data[b].reward?i:b,0);
        return (
          <g>
            <circle cx={xs(peak)} cy={ys(data[peak].reward)} r="5"
              fill="none" stroke={C.green} strokeWidth="1.5"/>
            <text x={xs(peak)} y={ys(data[peak].reward)-9}
              textAnchor="middle" fill={C.green} fontSize="9" fontFamily="Share Tech Mono">
              PEAK
            </text>
          </g>
        );
      })()}
    </svg>
  );
}

// ── Shared Card ───────────────────────────────────────────────────────────────
function Card({ children, style={} }) {
  return (
    <div className="glow-box" style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: 8,
      overflow: "hidden",
      ...style,
    }}>
      {children}
    </div>
  );
}

function CardLabel({ children }) {
  return (
    <div style={{
      padding:"9px 14px",
      borderBottom:`1px solid ${C.border}`,
      fontFamily:"'Orbitron',sans-serif",
      fontSize:10, fontWeight:700,
      letterSpacing:"0.14em",
      color: C.primary,
      background:`${C.primary}08`,
    }}>
      {children}
    </div>
  );
}

// ── Tiny icon shims ───────────────────────────────────────────────────────────
function ShieldIcon({ size=16, color="currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
  );
}
function PlayIcon({ size=14, color="currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color}>
      <polygon points="5,3 19,12 5,21"/>
    </svg>
  );
}
function SpinIcon({ size=14, color="currentColor" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke={color} strokeWidth="2.5"
      style={{ animation:"spin 0.8s linear infinite" }}>
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
//  Root App
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  useGlobalCss(GLOBAL_CSS);

  const [status,       setStatus]       = useState("idle");
  const [currentStage, setCurrentStage] = useState(0);
  const [results,      setResults]      = useState(null);

  const runAnalysis = (code) => {
    setStatus("running");
    setCurrentStage(0);
    setResults(null);

    let stage = 0;
    const iv = setInterval(() => {
      stage++;
      if (stage >= 10) {
        clearInterval(iv);
        setCurrentStage(10);
        setStatus("complete");
        setResults(generateResults(code));
      } else {
        setCurrentStage(stage);
      }
    }, 550);
  };

  return (
    <>
      <div className="scan-overlay" />
      <div style={{ minHeight:"100vh", background:C.bg }}>
        <Header status={status} />

        <main style={{ maxWidth:1200, margin:"0 auto", padding:"24px 20px", display:"flex", flexDirection:"column", gap:16 }}>
          <VerilogInput onSubmit={runAnalysis} isRunning={status==="running"} />

          {status !== "idle" && (
            <div className="fadein">
              <PipelineStages currentStage={currentStage} />
            </div>
          )}

          {status === "complete" && results && (
            <AnalysisResults results={results} />
          )}
        </main>
      </div>
    </>
  );
}