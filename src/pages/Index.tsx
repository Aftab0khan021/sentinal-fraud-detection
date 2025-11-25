import { Hero } from "@/components/Hero";
import { Architecture } from "@/components/Architecture";
import { TechStack } from "@/components/TechStack";
import { Modules } from "@/components/Modules";
import { GraphDemo } from "@/components/GraphDemo";

const Index = () => {
  return (
    <div className="min-h-screen bg-background">
      <Hero />
      <Architecture />
      <GraphDemo />
      <Modules />
      <TechStack />
    </div>
  );
};

export default Index;
