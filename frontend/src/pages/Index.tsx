import { useState } from "react";
import PipelineSidebar from "@/components/PipelineSidebar";
import PipelineCanvas from "@/components/PipelineCanvas";

const Index = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      
      <PipelineCanvas />
    </div>
  );
};

export default Index;
