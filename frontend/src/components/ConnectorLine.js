import { jsx as _jsx } from "react/jsx-runtime";
import { motion } from "framer-motion";
export default function ConnectorLine({ active, index }) {
    return (_jsx(motion.div, { initial: { scaleY: 0 }, animate: { scaleY: 1 }, transition: { delay: index * 0.08 + 0.04, duration: 0.3 }, className: "flex justify-center", children: _jsx("div", { className: `h-8 w-0.5 origin-top ${active ? "bg-primary shadow-[0_0_8px_var(--color-primary)]" : "bg-border"}` }) }));
}
