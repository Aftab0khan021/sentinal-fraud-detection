import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { AlertCircle, CheckCircle } from "lucide-react";

export const GraphDemo = () => {
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  
  const nodes = [
    { id: 0, x: 200, y: 100, fraud: false, label: "User A" },
    { id: 1, x: 350, y: 100, fraud: false, label: "User B" },
    { id: 2, x: 200, y: 250, fraud: false, label: "User C" },
    { id: 3, x: 350, y: 250, fraud: true, label: "User D" },
    { id: 4, x: 275, y: 175, fraud: true, label: "User E" },
    { id: 5, x: 450, y: 175, fraud: true, label: "User F" },
  ];
  
  const edges = [
    { from: 0, to: 1, amount: "$500" },
    { from: 1, to: 2, amount: "$300" },
    { from: 3, to: 4, amount: "$1200", fraud: true },
    { from: 4, to: 5, amount: "$1150", fraud: true },
    { from: 5, to: 3, amount: "$1100", fraud: true },
    { from: 2, to: 3, amount: "$200" },
  ];
  
  return (
    <section className="bg-muted/30 py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-3xl font-bold mb-4 text-center text-foreground">
            Interactive Detection Example
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            Click on a node to see how the system identifies and explains fraud patterns
          </p>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <Card className="p-6 bg-card">
              <h3 className="font-semibold mb-4 text-card-foreground">Transaction Network</h3>
              <svg className="w-full h-80 border border-border rounded-lg bg-background" viewBox="0 0 500 300">
                {/* Render edges first */}
                {edges.map((edge, idx) => {
                  const fromNode = nodes.find(n => n.id === edge.from)!;
                  const toNode = nodes.find(n => n.id === edge.to)!;
                  return (
                    <g key={idx}>
                      <line
                        x1={fromNode.x}
                        y1={fromNode.y}
                        x2={toNode.x}
                        y2={toNode.y}
                        stroke={edge.fraud ? "hsl(var(--fraud-alert))" : "hsl(var(--graph-edge))"}
                        strokeWidth={edge.fraud ? "3" : "2"}
                        opacity={edge.fraud ? "0.8" : "0.5"}
                      />
                      <text
                        x={(fromNode.x + toNode.x) / 2}
                        y={(fromNode.y + toNode.y) / 2}
                        fill="hsl(var(--muted-foreground))"
                        fontSize="10"
                        textAnchor="middle"
                      >
                        {edge.amount}
                      </text>
                    </g>
                  );
                })}
                
                {/* Render nodes */}
                {nodes.map((node) => (
                  <g
                    key={node.id}
                    onClick={() => setSelectedNode(node.id)}
                    className="cursor-pointer"
                  >
                    <circle
                      cx={node.x}
                      cy={node.y}
                      r="20"
                      fill={node.fraud ? "hsl(var(--fraud-alert))" : "hsl(var(--graph-safe))"}
                      opacity={selectedNode === node.id ? "1" : "0.8"}
                      stroke={selectedNode === node.id ? "hsl(var(--primary))" : "transparent"}
                      strokeWidth="3"
                    />
                    <text
                      x={node.x}
                      y={node.y + 35}
                      fill="hsl(var(--foreground))"
                      fontSize="12"
                      textAnchor="middle"
                      fontWeight={selectedNode === node.id ? "bold" : "normal"}
                    >
                      {node.label}
                    </text>
                  </g>
                ))}
              </svg>
              <div className="mt-4 flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-graph-safe" />
                  <span className="text-muted-foreground">Normal User</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full bg-graph-fraud" />
                  <span className="text-muted-foreground">Flagged User</span>
                </div>
              </div>
            </Card>
            
            <Card className="p-6 bg-card">
              <h3 className="font-semibold mb-4 text-card-foreground">Analysis Result</h3>
              {selectedNode === null ? (
                <div className="flex items-center justify-center h-80 text-muted-foreground">
                  Select a node to see analysis
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    {nodes.find(n => n.id === selectedNode)?.fraud ? (
                      <AlertCircle className="h-6 w-6 text-graph-fraud flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="h-6 w-6 text-graph-safe flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="font-semibold mb-1 text-card-foreground">
                        {nodes.find(n => n.id === selectedNode)?.label}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {nodes.find(n => n.id === selectedNode)?.fraud 
                          ? "⚠️ High fraud probability detected"
                          : "✓ No suspicious activity detected"
                        }
                      </p>
                    </div>
                  </div>
                  
                  {selectedNode === 3 && (
                    <div className="space-y-3">
                      <div className="p-4 rounded-lg border border-border bg-background">
                        <p className="font-medium mb-2 text-foreground">GNN Detection</p>
                        <p className="text-sm text-muted-foreground">
                          Fraud probability: <span className="font-semibold text-graph-fraud">0.94</span>
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Reason: Participant in cyclic transaction pattern
                        </p>
                      </div>
                      
                      <div className="p-4 rounded-lg border border-accent/20 bg-accent/5">
                        <p className="font-medium mb-2 text-foreground flex items-center gap-2">
                          <span>🤖</span> Agent Explanation
                        </p>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          User D is part of a suspected money laundering ring. Analysis shows a cyclic flow pattern: D → E ($1,200) → F ($1,150) → back to D ($1,100). This circular movement of funds with minimal value loss is a classic layering technique used to obscure the origin of funds.
                        </p>
                      </div>
                      
                      <Button size="sm" variant="outline" className="w-full">
                        View Full Report
                      </Button>
                    </div>
                  )}
                  
                  {selectedNode === 0 && (
                    <div className="p-4 rounded-lg border border-border bg-background">
                      <p className="font-medium mb-2 text-foreground">GNN Detection</p>
                      <p className="text-sm text-muted-foreground">
                        Fraud probability: <span className="font-semibold text-graph-safe">0.05</span>
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Normal transaction patterns detected. No suspicious connections.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};
