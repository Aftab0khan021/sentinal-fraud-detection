import { ArrowRight } from "lucide-react";

export const Architecture = () => {
  return (
    <section className="container mx-auto px-4 py-20">
      <div className="mx-auto max-w-5xl">
        <h2 className="text-3xl font-bold mb-4 text-center text-foreground">
          How It Works
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          A three-stage pipeline that goes beyond individual transaction analysis to detect coordinated fraud rings
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          <div className="relative">
            <div className="rounded-xl border border-border bg-card p-6 h-full">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 text-primary font-bold text-xl mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold mb-3 text-card-foreground">Data Generation</h3>
              <p className="text-muted-foreground mb-4">
                Synthetic financial graph with realistic transaction patterns and deliberately injected fraud rings
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-graph-safe">•</span>
                  User nodes with risk features
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-graph-safe">•</span>
                  Transaction edges with metadata
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-graph-fraud">•</span>
                  Cyclic fraud patterns (4-5 nodes)
                </li>
              </ul>
            </div>
            <div className="hidden md:block absolute -right-4 top-1/2 -translate-y-1/2 z-10">
              <ArrowRight className="h-8 w-8 text-primary" />
            </div>
          </div>
          
          <div className="relative">
            <div className="rounded-xl border border-border bg-card p-6 h-full">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10 text-primary font-bold text-xl mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold mb-3 text-card-foreground">GNN Detection</h3>
              <p className="text-muted-foreground mb-4">
                R-GCN model learns to identify suspicious patterns in the transaction graph
              </p>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-start gap-2">
                  <span className="text-graph-safe">•</span>
                  Relational convolutions per edge type
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-graph-safe">•</span>
                  Handles class imbalance
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-graph-fraud">•</span>
                  Outputs fraud probability per node
                </li>
              </ul>
            </div>
            <div className="hidden md:block absolute -right-4 top-1/2 -translate-y-1/2 z-10">
              <ArrowRight className="h-8 w-8 text-primary" />
            </div>
          </div>
          
          <div className="rounded-xl border border-border bg-card p-6 h-full">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-accent/10 text-accent font-bold text-xl mb-4">
              3
            </div>
            <h3 className="text-xl font-semibold mb-3 text-card-foreground">Agent Explanation</h3>
            <p className="text-muted-foreground mb-4">
              LangChain agent queries graph context and explains fraud patterns in natural language
            </p>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <span className="text-graph-safe">•</span>
                Extracts k-hop subgraph
              </li>
              <li className="flex items-start gap-2">
                <span className="text-graph-safe">•</span>
                Local Ollama (Llama3/Mistral)
              </li>
              <li className="flex items-start gap-2">
                <span className="text-accent">•</span>
                Plain-English compliance report
              </li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};
