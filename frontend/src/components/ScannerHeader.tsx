import { Shield, Activity } from "lucide-react";
import { motion } from "framer-motion";

const ScannerHeader = () => (
  <motion.header
    initial={{ opacity: 0, y: -20 }}
    animate={{ opacity: 1, y: 0 }}
    className="flex items-center gap-4 py-6"
  >
    <div className="relative">
      <Shield className="w-10 h-10 text-primary" />
      <Activity className="w-4 h-4 text-secondary absolute -bottom-1 -right-1" />
    </div>
    <div>
      <h1 className="text-2xl font-bold neon-text font-mono tracking-wider">
        FSM SECURITY PIPELINE
      </h1>
      <p className="text-sm text-muted-foreground font-mono">
        Analyzer + RL Protection Agent
      </p>
    </div>
  </motion.header>
);

export default ScannerHeader;