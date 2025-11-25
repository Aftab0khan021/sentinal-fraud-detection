import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { AlertCircle, CheckCircle } from "lucide-react";

export const GraphDemo = () => {
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  
  // Data matches the Python backend result for User 77's fraud ring
  const nodes = [
    { id: 77, x: 350, y: 100, fraud: true, label: "User 77" },
    { id: 81, x: 500, y: 175, fraud: true, label: "User 81" },
    { id: 87, x: 425, y: 300, fraud: true, label: "User 87" },
    { id: 82, x: 275, y: 300, fraud: true, label: "User 82" },
    { id: 9,  x: 200, y: 175, fraud: true, label: "User 9" },
    { id: 64, x: 100, y: 100, fraud: false, label: "User 64" }, // Innocent
  ];

  const edges = [
    // The Cyclic Money Laundering Loop
    { from: 77, to: 81, amount: "$12,000", fraud: true },
    { from: 81, to: 87, amount: "$11,500", fraud: true },
    { from: 87, to: 82, amount: "$11,200", fraud: true },
    { from: 82, to: 9,  amount: "$10,800", fraud: true },
    { from: 9,  to: 77, amount: "$10,500", fraud: true }, // Loop closed
    // Normal transaction
    { from: 64, to: 77, amount: "$200", fraud: false },
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
              <svg className="w-full h-80 border border-border rounded-lg bg-background" viewBox="0 0 600 400">
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
                        dy={-5}
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
                  
                  {selectedNode === 77 && (
                    <div className="space-y-3">
                      <div className="p-4 rounded-lg border border-border bg-background">
                        <p className="font-medium mb-2 text-foreground">GNN Detection</p>
                        <p className="text-sm text-muted-foreground">
                          Fraud probability: <span className="font-semibold text-graph-fraud">1.00</span>
                        </p>
                        <p className="text-sm text-muted-foreground mt-1">
                          Reason: Cyclic topology detected in 2-hop neighborhood
                        </p>
                      </div>
                      
                      <div className="p-4 rounded-lg border border-accent/20 bg-accent/5">
                        <p className="font-medium mb-2 text-foreground flex items-center gap-2">
                          <span>🤖</span> Agent Report
                        </p>
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          **Topological Anomaly Detected:** User 77 is part of a closed flow loop involving Users 81, 87, 82, and 9. Funds travel sequentially through these nodes and return to User 77 ($10,500), indicating a layering attempt. Status: ANOMALOUS.
                        </p>
                      </div>
                      
                      <Button size="sm" variant="outline" className="w-full">
                        Download Compliance PDF
                      </Button>
                    </div>
                  )}
                  
                  {(selectedNode !== 77) && (
                    <div className="p-4 rounded-lg border border-border bg-background">
                      <p className="font-medium mb-2 text-foreground">Analysis</p>
                      <p className="text-sm text-muted-foreground">
                        Click on User 77 to see the detailed fraud ring analysis.
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