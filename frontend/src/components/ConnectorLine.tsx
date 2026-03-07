import { motion } from "framer-motion";

interface ConnectorLineProps {
  active: boolean;
  index: number;
}

export default function ConnectorLine({ active, index }: ConnectorLineProps) {
  return (
    <motion.div
      initial={{ scaleY: 0 }}
      animate={{ scaleY: 1 }}
      transition={{ delay: index * 0.08 + 0.04, duration: 0.3 }}
      className="flex justify-center"
    >
      <div className={`h-8 w-0.5 origin-top ${active ? "connector-line" : "bg-border"}`} />
    </motion.div>
  );
}
