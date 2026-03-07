import { useState } from "react";
import { motion } from "framer-motion";
import { Scan, Terminal, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SAMPLE_VERILOG } from "@/lib/mockData";

interface VerilogInputProps {
  onScan: (code: string) => void;
  isScanning: boolean;
}

const VerilogInput = ({ onScan, isScanning }: VerilogInputProps) => {
  const [code, setCode] = useState("");

  const handleLoadSample = () => setCode(SAMPLE_VERILOG);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="space-y-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-primary" />
          <span className="text-sm font-mono text-muted-foreground uppercase tracking-widest">
            Verilog RTL Input
          </span>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleLoadSample}
          className="text-xs font-mono text-muted-foreground hover:text-primary hover:bg-muted"
        >
          Load Sample
        </Button>
      </div>

      <div className="relative rounded-lg border border-border bg-card overflow-hidden neon-border">
        <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-muted/50">
          <div className="w-2.5 h-2.5 rounded-full bg-destructive/60" />
          <div className="w-2.5 h-2.5 rounded-full bg-primary/40" />
          <div className="w-2.5 h-2.5 rounded-full bg-secondary/40" />
          <span className="ml-2 text-xs font-mono text-muted-foreground">fsm_controller.v</span>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="// Paste your Verilog FSM code here..."
          className="w-full h-72 p-4 bg-transparent text-foreground font-mono text-sm resize-none focus:outline-none placeholder:text-muted-foreground/40"
          spellCheck={false}
        />
        {isScanning && (
          <div className="absolute inset-0 bg-background/60 pointer-events-none">
            <div className="h-0.5 bg-primary/60 scan-line" />
          </div>
        )}
      </div>

      <Button
        onClick={() => onScan(code)}
        disabled={!code.trim() || isScanning}
        className="w-full font-mono uppercase tracking-widest bg-primary text-primary-foreground hover:bg-primary/80 transition-all"
        size="lg"
      >
        {isScanning ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Scanning FSM...
          </>
        ) : (
          <>
            <Scan className="w-4 h-4 mr-2" />
            Analyze Vulnerabilities
          </>
        )}
      </Button>
    </motion.div>
  );
};

export default VerilogInput;
