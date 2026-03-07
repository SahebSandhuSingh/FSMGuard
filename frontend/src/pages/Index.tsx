import PipelineSidebar from "@/components/PipelineSidebar";
import PipelineCanvas from "@/components/PipelineCanvas";

const Index = () => {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <PipelineSidebar />
      <PipelineCanvas />
    </div>
  );
};

export default Index;
