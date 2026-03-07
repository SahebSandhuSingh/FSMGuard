import { useState } from "react";
import { motion } from "framer-motion";
import { Play, RotateCcw, FileCode } from "lucide-react";
import { Button } from "@/components/ui/button";

const SAMPLE_VERILOG = `module fsm_controller (
  input clk, rst, req, ack,
  output reg grant, error
);
  parameter IDLE = 3'b000,
            AUTH = 3'b001,
            PROCESS = 3'b010,
            WAIT = 3'b011,
            TRANSMIT = 3'b100,
            DONE = 3'b101,
            ERROR = 3'b110;

  reg [2:0] state, next_state;

  always @(posedge clk or posedge rst) begin
    if (rst) state <= IDLE;
    else state <= next_state;
  end

  always @(*) begin
    case (state)
      IDLE:    next_state = req ? AUTH : IDLE;
      AUTH:    next_state = ack ? PROCESS : ERROR;
      PROCESS: next_state = WAIT;
      WAIT:   next_state = ack ? TRANSMIT : WAIT;
      TRANSMIT: next_state = DONE;
      DONE:   next_state = IDLE;
      ERROR:  next_state = IDLE;
      default: next_state = IDLE;
    endcase
  end
endmodule`;

interface Props {
  onSubmit: (code: string) => void;
  isRunning: boolean;
}

const VerilogInput = ({ onSubmit, isRunning }: Props) => {
  const [code, setCode] = useState("");

  const loadSample = () => setCode(SAMPLE_VERILOG);

  return (
    <div className="rounded-lg border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <div className="flex items-center gap-2">
          <FileCode className="h-4 w-4 text-primary" />
          <span className="font-mono text-sm font-medium text-card-foreground">
            Verilog RTL Input
          </span>
        </div>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={loadSample}
            className="font-mono text-xs text-muted-foreground hover:text-foreground hover:bg-secondary"
          >
            Load Sample
          </Button>
        </div>
      </div>

      <div className="p-4">
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="// Paste your Verilog FSM design here..."
          className="min-h-[240px] w-full resize-y rounded-md border border-border bg-background p-4 font-mono text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
          spellCheck={false}
        />
      </div>

      <div className="flex items-center justify-between border-t border-border px-4 py-3">
        <p className="font-mono text-xs text-muted-foreground">
          {code.length > 0 ? `${code.split("\n").length} lines` : "No input"}
        </p>
        <div className="flex gap-2">
          {code.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCode("")}
              className="font-mono text-xs text-muted-foreground hover:text-foreground hover:bg-secondary"
            >
              <RotateCcw className="mr-1 h-3 w-3" /> Clear
            </Button>
          )}
          <Button
            size="sm"
            onClick={() => onSubmit(code)}
            disabled={code.length === 0 || isRunning}
            className="gap-1.5 bg-primary font-mono text-sm font-semibold text-primary-foreground hover:bg-primary/90 glow-primary disabled:opacity-40"
          >
            <Play className="h-3.5 w-3.5" />
            {isRunning ? "Running..." : "Analyze FSM"}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default VerilogInput;
