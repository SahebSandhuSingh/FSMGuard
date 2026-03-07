export interface Vulnerability {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  state: string;
  description: string;
  line: number;
  patchedCode: string;
  solution: string;
}

export const SAMPLE_VERILOG = `module fsm_controller (
  input clk, reset, start, mode,
  output reg [1:0] state,
  output reg done, error
);

  parameter IDLE   = 2'b00;
  parameter ACTIVE = 2'b01;
  parameter WAIT   = 2'b10;
  // WARNING: state 2'b11 is undefined

  always @(posedge clk or posedge reset) begin
    if (reset)
      state <= IDLE;
    else begin
      case (state)
        IDLE: begin
          if (start)
            state <= ACTIVE;
        end
        ACTIVE: begin
          if (mode)
            state <= WAIT;
          else
            state <= IDLE;
        end
        WAIT: begin
          done <= 1;
          state <= IDLE;
        end
        // No default case — vulnerable!
      endcase
    end
  end
endmodule`;

export const MOCK_VULNERABILITIES: Vulnerability[] = [
  {
    id: "vuln-001",
    title: "Undefined State Transition (2'b11)",
    severity: "critical",
    state: "UNKNOWN (2'b11)",
    description: "State encoding 2'b11 has no defined behavior. An attacker could force the FSM into this state via glitching, causing undefined output behavior and potential control flow hijack.",
    line: 11,
    patchedCode: `default: begin
  state <= IDLE;
  error <= 1'b1;
end`,
    solution: "Added a default case that transitions to IDLE and raises an error flag, preventing the FSM from entering an undefined state."
  },
  {
    id: "vuln-002",
    title: "Missing Default Case in State Machine",
    severity: "high",
    state: "ALL",
    description: "The case statement lacks a default handler. If the FSM enters an unlisted state due to SEU or fault injection, execution falls through silently with no recovery mechanism.",
    line: 28,
    patchedCode: `default: begin
  state <= IDLE;
  error <= 1'b1;
  done  <= 1'b0;
end`,
    solution: "Inserted a default clause that resets the FSM to the IDLE state and signals an error, ensuring graceful recovery from any unexpected state."
  },
  {
    id: "vuln-003",
    title: "No Deadlock Detection on WAIT State",
    severity: "medium",
    state: "WAIT",
    description: "The WAIT state unconditionally transitions to IDLE on every clock cycle. There is no timeout or watchdog — if the transition condition changes in future revisions, the FSM could deadlock.",
    line: 24,
    patchedCode: `WAIT: begin
  if (wait_counter >= TIMEOUT) begin
    state <= IDLE;
    error <= 1'b1;
  end else begin
    wait_counter <= wait_counter + 1;
    done <= 1'b1;
  end
end`,
    solution: "Added a watchdog counter with a configurable timeout threshold. If the WAIT state persists beyond the timeout, the FSM resets to IDLE and flags an error."
  },
  {
    id: "vuln-004",
    title: "Unguarded Output Assignment in WAIT",
    severity: "low",
    state: "WAIT",
    description: "The 'done' signal is assigned inside the WAIT state without a guard condition. This could cause unintended output assertion if the state is entered spuriously.",
    line: 25,
    patchedCode: `WAIT: begin
  if (valid_entry) begin
    done <= 1'b1;
  end
  state <= IDLE;
end`,
    solution: "Wrapped the 'done' assignment with a valid_entry guard to ensure it is only asserted when the state is entered through a legitimate transition path."
  }
];

export const PIPELINE_STAGES = [
  {
    id: 1,
    group: "INPUT",
    title: "Input & Parsing",
    description: "Parse Verilog via PyVerilog, extract AST and FSM structure",
    tech: ["PyVerilog", "AST"],
    duration: 2000,
  },
  {
    id: 2,
    group: "INPUT",
    title: "Graph Construction",
    description: "Convert FSM to directed graph — states as nodes, transitions as edges",
    tech: ["NetworkX", "PyTorch Geometric"],
    duration: 1500,
  },
  {
    id: 3,
    group: "INPUT",
    title: "Feature Generation",
    description: "Compute per-node features: degree, self-loops, reset distance",
    tech: ["NetworkX", "NumPy"],
    duration: 1800,
  },
  {
    id: 4,
    group: "GYMNASIUM",
    title: "GNN Weak State Detection",
    description: "GCN/GAT classifier flags vulnerable states with risk scores",
    tech: ["GCN", "GAT", "PyTorch Geometric"],
    duration: 2500,
  },
  {
    id: 5,
    group: "GYMNASIUM",
    title: "Subgraph Isolation",
    description: "Extract flagged states and neighbors into focused subgraph",
    tech: ["NetworkX", "PyTorch Geometric"],
    duration: 1200,
  },
  {
    id: 6,
    group: "GYMNASIUM",
    title: "RL Environment Setup",
    description: "Wrap subgraph as Gymnasium env with custom action/observation spaces",
    tech: ["Gymnasium", "Custom Env"],
    duration: 1500,
  },
  {
    id: 7,
    group: "RL_AGENT",
    title: "RL Agent — PPO Decision",
    description: "PPO agent selects optimal fix per flagged state via policy network",
    tech: ["PPO", "Stable Baselines3", "PyTorch"],
    duration: 3000,
  },
  {
    id: 8,
    group: "PATCH_VERIFY",
    title: "Patch Generation",
    description: "Translate fix action into valid Verilog AST modifications",
    tech: ["PyVerilog AST", "Jinja2"],
    duration: 2000,
  },
  {
    id: 9,
    group: "PATCH_VERIFY",
    title: "Formal Verification",
    description: "Prove patch correctness via SymbiYosys + Z3 SMT solver",
    tech: ["SymbiYosys", "Z3", "SVA"],
    duration: 2500,
  },
  {
    id: 10,
    group: "PATCH_VERIFY",
    title: "Reward & Feedback Loop",
    description: "Score patch and update RL policy weights via backpropagation",
    tech: ["Custom Reward", "Icarus Verilog", "SB3"],
    duration: 1500,
  },
];
