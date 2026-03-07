import { motion } from "framer-motion";
import { Shield, AlertTriangle, ChevronRight, ShieldAlert, ShieldCheck, Info } from "lucide-react";
import { Vulnerability } from "@/lib/mockData";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const severityConfig = {
  critical: { icon: ShieldAlert, className: "bg-destructive/20 text-destructive border-destructive/40" },
  high: { icon: AlertTriangle, className: "bg-destructive/10 text-destructive/80 border-destructive/30" },
  medium: { icon: Info, className: "bg-secondary/20 text-secondary border-secondary/40" },
  low: { icon: ShieldCheck, className: "bg-primary/20 text-primary border-primary/40" },
};

interface ScanResultsProps {
  vulnerabilities: Vulnerability[];
  onFix: () => void;
}

const ScanResults = ({ vulnerabilities, onFix }: ScanResultsProps) => {
  const criticalCount = vulnerabilities.filter((v) => v.severity === "critical").length;
  const highCount = vulnerabilities.filter((v) => v.severity === "high").length;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="space-y-4 mt-8"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-destructive" />
          <span className="font-mono text-sm uppercase tracking-widest text-muted-foreground">
            Scan Results
          </span>
        </div>
        <div className="flex items-center gap-3 font-mono text-xs">
          <span className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-destructive" />
            <span className="danger-text">{criticalCount} critical</span>
          </span>
          <span className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-destructive/60" />
            <span className="text-destructive/80">{highCount} high</span>
          </span>
          <span className="text-muted-foreground">{vulnerabilities.length} total</span>
        </div>
      </div>

      <div className="space-y-3">
        {vulnerabilities.map((vuln, i) => {
          const config = severityConfig[vuln.severity];
          const Icon = config.icon;
          return (
            <motion.div
              key={vuln.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.15 }}
              className="border border-border rounded-lg bg-card p-4 space-y-3"
            >
              <div className="flex items-start gap-3">
                <Icon className="w-5 h-5 mt-0.5 shrink-0" />
                <div>
                  <h3 className="font-mono text-sm font-semibold text-foreground">{vuln.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge variant="outline" className={`text-xs font-mono uppercase ${config.className}`}>
                      {vuln.severity}
                    </Badge>
                    <span className="text-xs font-mono text-muted-foreground">
                      State: {vuln.state}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground">
                      Line {vuln.line}
                    </span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{vuln.description}</p>
            </motion.div>
          );
        })}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: vulnerabilities.length * 0.15 + 0.3 }}
        className="flex justify-center pt-4"
      >
        <Button
          onClick={onFix}
          size="lg"
          className="font-mono text-sm uppercase tracking-wider bg-primary text-primary-foreground hover:bg-primary/80 px-8"
        >
          Fix & Patch All Vulnerabilities
          <ChevronRight className="w-4 h-4 ml-2" />
        </Button>
      </motion.div>
    </motion.div>
  );
};

export default ScanResults;
