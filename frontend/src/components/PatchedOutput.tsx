import { motion } from "framer-motion";
import { Download, CheckCircle2, FileCode2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Vulnerability, SAMPLE_VERILOG } from "@/lib/mockData";
import jsPDF from "jspdf";

interface PatchedOutputProps {
  vulnerabilities: Vulnerability[];
}

const generateFullPatchedCode = () => {
  return `module fsm_controller (
  input clk, reset, start, mode,
  output reg [1:0] state,
  output reg done, error
);

  parameter IDLE   = 2'b00;
  parameter ACTIVE = 2'b01;
  parameter WAIT   = 2'b10;
  parameter TIMEOUT = 8'd255;

  reg [7:0] wait_counter;

  always @(posedge clk or posedge reset) begin
    if (reset) begin
      state <= IDLE;
      done  <= 1'b0;
      error <= 1'b0;
      wait_counter <= 8'd0;
    end else begin
      case (state)
        IDLE: begin
          done  <= 1'b0;
          error <= 1'b0;
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
          if (wait_counter >= TIMEOUT) begin
            state <= IDLE;
            error <= 1'b1;
            wait_counter <= 8'd0;
          end else begin
            wait_counter <= wait_counter + 1;
            done <= 1'b1;
          end
        end
        default: begin
          state <= IDLE;
          error <= 1'b1;
          done  <= 1'b0;
        end
      endcase
    end
  end
endmodule`;
};

const PatchedOutput = ({ vulnerabilities }: PatchedOutputProps) => {
  const fullPatchedCode = generateFullPatchedCode();

  const briefSummary = `The RL agent identified ${vulnerabilities.length} vulnerabilities in the FSM design. A default case was added to handle undefined state 2'b11, preventing control-flow hijack. A watchdog counter with configurable timeout was introduced for the WAIT state to prevent deadlocks. Output assignments are now guarded to prevent spurious assertions. All patches have been formally verified via SymbiYosys + Z3.`;

  const handleDownloadPDF = () => {
    const doc = new jsPDF();
    doc.setFont("courier", "normal");
    doc.setFontSize(16);
    doc.text("FSM Security Pipeline — Report", 14, 20);
    doc.setFontSize(10);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 28);
    doc.setLineWidth(0.5);
    doc.line(14, 32, 196, 32);

    let y = 40;

    // Summary
    doc.setFontSize(12);
    doc.text("Summary", 14, y);
    y += 7;
    doc.setFontSize(9);
    const summaryLines = doc.splitTextToSize(briefSummary, 170);
    doc.text(summaryLines, 14, y);
    y += summaryLines.length * 5 + 8;

    // Vulnerabilities found
    doc.setFontSize(12);
    doc.text("Vulnerabilities Detected & Solutions", 14, y);
    y += 8;

    vulnerabilities.forEach((v, i) => {
      if (y > 240) { doc.addPage(); y = 20; }
      doc.setFontSize(11);
      doc.text(`${i + 1}. [${v.severity.toUpperCase()}] ${v.title}`, 14, y);
      y += 6;
      doc.setFontSize(9);
      doc.text(`State: ${v.state} | Line: ${v.line}`, 14, y);
      y += 5;
      const descLines = doc.splitTextToSize(v.description, 170);
      doc.text(descLines, 14, y);
      y += descLines.length * 5 + 3;
      doc.setFontSize(9);
      doc.text(`Solution: ${v.solution}`, 14, y);
      y += 8;
    });

    // Full patched code
    if (y > 200) { doc.addPage(); y = 20; }
    doc.setFontSize(12);
    doc.text("Full Patched Verilog Code", 14, y);
    y += 8;
    doc.setFontSize(8);
    const codeLines = doc.splitTextToSize(fullPatchedCode, 175);
    codeLines.forEach((line: string) => {
      if (y > 280) { doc.addPage(); y = 20; }
      doc.text(line, 14, y);
      y += 4;
    });

    doc.save("fsm-security-report.pdf");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-5 mt-6"
    >
      {/* Brief Summary */}
      <div className="border border-primary/20 rounded-lg bg-card p-4 space-y-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-primary" />
          <span className="font-mono text-sm uppercase tracking-widest neon-text">
            Analysis Complete
          </span>
        </div>
        <p className="text-sm text-muted-foreground leading-relaxed">{briefSummary}</p>
      </div>

      {/* Full Patched Code */}
      <div className="border border-primary/20 rounded-lg bg-card p-4 space-y-3">
        <div className="flex items-center gap-2">
          <FileCode2 className="w-4 h-4 text-primary" />
          <span className="font-mono text-sm uppercase tracking-widest neon-text">
            Full Patched Code
          </span>
        </div>
        <div className="rounded-md bg-muted border border-border p-4 max-h-96 overflow-y-auto">
          <pre className="text-xs font-mono text-foreground whitespace-pre">{fullPatchedCode}</pre>
        </div>
      </div>

      {/* Download Button */}
      <div className="flex justify-center pt-2">
        <Button
          onClick={handleDownloadPDF}
          size="lg"
          className="font-mono text-sm uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/80 px-8"
        >
          <Download className="w-4 h-4 mr-2" />
          Download Full Report
        </Button>
      </div>
    </motion.div>
  );
};

export default PatchedOutput;
