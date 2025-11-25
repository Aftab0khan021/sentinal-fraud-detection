import { Code2, Database, MessageSquare } from "lucide-react";
import { Card } from "./ui/card";

export const Modules = () => {
  return (
    <section className="container mx-auto px-4 py-20">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-3xl font-bold mb-4 text-center text-foreground">
          Technical Modules
        </h2>
        <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
          Three core Python modules implementing the complete fraud detection pipeline
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="p-6 bg-card hover:shadow-lg transition-shadow">
            <Database className="h-10 w-10 text-primary mb-4" />
            <h3 className="text-xl font-semibold mb-3 text-card-foreground">
              data_gen.py
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Synthetic Financial Graph Generator
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Creates realistic user nodes with features (account age, risk score)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Generates transaction edges with amounts, timestamps, types
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-fraud flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Injects cyclic fraud patterns (4-5 node rings)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Outputs NetworkX graph and PyG Data object
                </span>
              </div>
            </div>
          </Card>
          
          <Card className="p-6 bg-card hover:shadow-lg transition-shadow">
            <svg className="h-10 w-10 text-primary mb-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3"/>
              <circle cx="12" cy="5" r="1"/>
              <circle cx="12" cy="19" r="1"/>
              <circle cx="5" cy="12" r="1"/>
              <circle cx="19" cy="12" r="1"/>
              <line x1="12" y1="9" x2="12" y2="15"/>
              <line x1="9" y1="12" x2="15" y2="12"/>
            </svg>
            <h3 className="text-xl font-semibold mb-3 text-card-foreground">
              gnn_train.py
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              R-GCN Fraud Detector
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Implements Relational Graph Convolutional Network
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Handles multiple edge types (payment, transfer, withdrawal)
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-fraud flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Addresses class imbalance with weighted loss
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Outputs fraud probability per node
                </span>
              </div>
            </div>
          </Card>
          
          <Card className="p-6 bg-card hover:shadow-lg transition-shadow">
            <MessageSquare className="h-10 w-10 text-accent mb-4" />
            <h3 className="text-xl font-semibold mb-3 text-card-foreground">
              agent_explainer.py
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              GraphRAG Compliance Agent
            </p>
            <div className="space-y-2 text-sm">
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  LangChain agent with custom graph query tools
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Extracts k-hop subgraph around suspicious nodes
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-accent flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Uses local Ollama (Llama3/Mistral) for privacy
                </span>
              </div>
              <div className="flex items-start gap-2">
                <Code2 className="h-4 w-4 text-graph-safe flex-shrink-0 mt-0.5" />
                <span className="text-muted-foreground">
                  Generates natural language compliance reports
                </span>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
};
