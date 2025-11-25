import { Shield, Brain, Network } from "lucide-react";
import { Button } from "./ui/button";

export const Hero = () => {
  return (
    <section className="relative overflow-hidden border-b border-border">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-accent/5" />
      
      <div className="container relative mx-auto px-4 py-20 sm:py-32">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-6 flex items-center justify-center gap-3">
            <Shield className="h-12 w-12 text-primary" />
            <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl">
              SentinAL
            </h1>
          </div>
          
          <p className="mb-4 text-xl text-muted-foreground sm:text-2xl">
            Agentic Fraud Ring Detection with GraphRAG
          </p>
          
          <p className="mb-8 mx-auto max-w-2xl text-lg text-muted-foreground">
            An intelligent system combining Graph Neural Networks and LLM agents to detect complex money laundering rings and explain fraud patterns in plain English.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button size="lg" className="gap-2">
              <Network className="h-5 w-5" />
              View Demo
            </Button>
            <Button size="lg" variant="outline" className="gap-2">
              <Brain className="h-5 w-5" />
              Explore Architecture
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mx-auto max-w-3xl">
            <div className="rounded-lg border border-border bg-card p-6 text-left">
              <Network className="h-8 w-8 text-primary mb-3" />
              <h3 className="font-semibold mb-2 text-card-foreground">Graph Neural Networks</h3>
              <p className="text-sm text-muted-foreground">
                R-GCN architecture detects cyclic patterns in transaction networks
              </p>
            </div>
            
            <div className="rounded-lg border border-border bg-card p-6 text-left">
              <Brain className="h-8 w-8 text-accent mb-3" />
              <h3 className="font-semibold mb-2 text-card-foreground">LLM Agent Explainer</h3>
              <p className="text-sm text-muted-foreground">
                Local Ollama models explain fraud patterns to compliance teams
              </p>
            </div>
            
            <div className="rounded-lg border border-border bg-card p-6 text-left">
              <Shield className="h-8 w-8 text-graph-safe mb-3" />
              <h3 className="font-semibold mb-2 text-card-foreground">Privacy-First</h3>
              <p className="text-sm text-muted-foreground">
                All processing happens locally—no data leaves your environment
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
