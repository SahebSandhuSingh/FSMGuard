import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PanelLeftClose, PanelLeft, MessageSquare, Shield } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";

interface PipelineSidebarProps {
  open: boolean;
  onToggle: () => void;
}

export default function PipelineSidebar({ open, onToggle }: PipelineSidebarProps) {
  const [prompt, setPrompt] = useState("");

  return (
    <>
      {/* Toggle button — always visible */}
      <Button
        size="icon"
        variant="ghost"
        onClick={onToggle}
        className="absolute left-3 top-3 z-30 h-8 w-8 text-muted-foreground hover:text-foreground"
      >
        {open ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
      </Button>

      <AnimatePresence>
        {open && (
          <motion.aside
            initial={{ x: -300, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -300, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="absolute left-0 top-0 z-20 flex h-full w-72 flex-col border-r border-border bg-sidebar shadow-2xl"
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3 pt-12">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Tools
              </span>
            </div>

            <Tabs defaultValue="fsm" className="flex flex-1 flex-col overflow-hidden">
              <TabsList className="mx-3 mt-3 bg-secondary">
                <TabsTrigger value="prompt" className="flex items-center gap-1.5 text-xs">
                  <MessageSquare className="h-3 w-3" /> Prompt
                </TabsTrigger>
                <TabsTrigger value="fsm" className="flex items-center gap-1.5 text-xs">
                  <Shield className="h-3 w-3" /> FSM Security
                </TabsTrigger>
              </TabsList>

              <TabsContent value="prompt" className="flex flex-1 flex-col gap-3 overflow-hidden px-3 pb-4">
                <p className="text-[11px] text-muted-foreground">
                  Describe what you want to analyze or generate using natural language.
                </p>
                <Textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="e.g. Find all unreachable states in my FSM..."
                  className="flex-1 resize-none bg-secondary border-border text-xs font-mono"
                />
                <Button size="sm" className="h-8 text-xs bg-primary text-primary-foreground">
                  Send Prompt
                </Button>
              </TabsContent>

              <TabsContent value="fsm" className="flex flex-1 flex-col gap-3 overflow-hidden px-3 pb-4">
                <p className="text-[11px] text-muted-foreground">
                  Automated FSM vulnerability detection and patching pipeline.
                </p>
                <div className="space-y-2 text-xs">
                  {[
                    { icon: "🔍", title: "Graph Analysis", desc: "Build & analyze FSM state graph" },
                    { icon: "🧠", title: "GNN Detection", desc: "Flag vulnerable states via GCN/GAT" },
                    { icon: "🤖", title: "RL Patching", desc: "PPO agent generates optimal fixes" },
                    { icon: "✅", title: "Verification", desc: "Formal proof + simulation scoring" },
                  ].map((item) => (
                    <div
                      key={item.title}
                      className="flex items-start gap-2.5 rounded-md bg-secondary/60 p-2.5"
                    >
                      <span className="text-sm">{item.icon}</span>
                      <div>
                        <p className="font-semibold text-foreground">{item.title}</p>
                        <p className="text-muted-foreground text-[10px]">{item.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </motion.aside>
        )}
      </AnimatePresence>
    </>
  );
}
