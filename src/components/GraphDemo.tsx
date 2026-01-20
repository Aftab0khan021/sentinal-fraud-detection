import { useState } from "react";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";

// Updated type to match API response
type AnalysisReport = {
  score: string;
  is_fraud: boolean;
  reason: string;
  agent_report: string;
};

export const GraphDemo = () => {
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeReport, setActiveReport] = useState<AnalysisReport | null>(null);
  
  // Visual Graph Data (Keep this hardcoded for the Visual Demo)
  const nodes = [
    { id: 77, x: 350, y: 100, fraud: true, label: "User 77" },
    { id: 81, x: 500, y: 175, fraud: true, label: "User 81" },
    { id: 87, x: 425, y: 300, fraud: true, label: "User 87" },
    { id: 82, x: 275, y: 300, fraud: true, label: "User 82" },
    { id: 9,  x: 200, y: 175, fraud: true, label: "User 9" },
    { id: 64, x: 100, y: 100, fraud: false, label: "User 64" },
  ];

  const edges = [
    { from: 77, to: 81, amount: "$12,000", fraud: true },
    { from: 81, to: 87, amount: "$11,500", fraud: true },
    { from: 87, to: 82, amount: "$11,200", fraud: true },
    { from: 82, to: 9,  amount: "$10,800", fraud: true },
    { from: 9,  to: 77, amount: "$10,500", fraud: true }, 
    { from: 64, to: 77, amount: "$200", fraud: false },
  ];

  // Function to call the Python API
  const handleNodeClick = async (nodeId: number) => {
    if (selectedNode === nodeId) return; // Don't reload if already selected
    
    setSelectedNode(nodeId);
    setLoading(true);
    setActiveReport(null); // Clear previous report

    try {
      // FETCH FROM YOUR PYTHON API
      const response = await fetch(`http://localhost:8000/analyze/${nodeId}`);
      if (!response.ok) throw new Error("API Connection Failed");
      
      const data = await response.json();
      setActiveReport(data);
      
    } catch (error) {
      console.error("Failed to fetch analysis:", error);
      // Fallback for demo if API is offline
      setActiveReport({
        score: "Error",
        is_fraud: false,
        reason: "API Unavailable",
        agent_report: "Could not connect to Python backend. Make sure 'uvicorn api:app' is running."
      });
    } finally {
      setLoading(false);
    }
  };

  const activeNode = nodes.find(n => n.id === selectedNode);

  return (
    <section className="bg-muted/30 py-20">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-3xl font-bold mb-4 text-center text-foreground">
            Live AI Detection
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            Click a node to trigger a real-time request to the Python/Llama3 Agent
          </p>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* LEFT COLUMN: THE GRAPH */}
            <Card className="p-6 bg-card">
              <h3 className="font-semibold mb-4 text-card-foreground">Transaction Network</h3>
              <svg className="w-full h-80 border border-border rounded-lg bg-background" viewBox="0 0 600 400">
                {edges.map((edge, idx) => {
                  const fromNode = nodes.find(n => n.id === edge.from);
                  const toNode = nodes.find(n => n.id === edge.to);
                  if (!fromNode || !toNode) return null;

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
                
                {nodes.map((node) => (
                  <g
                    key={node.id}
                    onClick={() => handleNodeClick(node.id)}
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
            </Card>
            
            {/* RIGHT COLUMN: REAL-TIME API RESULTS */}
            <Card className="p-6 bg-card">
              <h3 className="font-semibold mb-4 text-card-foreground">
                AI Agent Analysis {selectedNode && `(User ${selectedNode})`}
              </h3>
              
              {!selectedNode ? (
                <div className="flex items-center justify-center h-80 text-muted-foreground">
                  Select a node to query the Python Backend
                </div>
              ) : loading ? (
                <div className="flex flex-col items-center justify-center h-80 text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin mb-2" />
                  <p>Running GraphRAG Analysis...</p>
                  <p className="text-xs text-muted-foreground mt-2">(Querying Llama3 Model)</p>
                </div>
              ) : activeReport ? (
                <div className="space-y-4 animate-in fade-in duration-500">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    {activeReport.is_fraud ? (
                      <AlertCircle className="h-6 w-6 text-graph-fraud flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="h-6 w-6 text-graph-safe flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <p className="font-semibold mb-1 text-card-foreground">
                        User {selectedNode}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {activeReport.is_fraud 
                          ? "⚠️ High fraud probability detected"
                          : "✓ No suspicious activity detected"
                        }
                      </p>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="p-4 rounded-lg border border-border bg-background">
                      <p className="font-medium mb-2 text-foreground">GNN Detection</p>
                      <p className="text-sm text-muted-foreground">
                        Score: <span className={`font-semibold ${activeReport.is_fraud ? "text-graph-fraud" : "text-graph-safe"}`}>
                          {activeReport.score}
                        </span>
                      </p>
                      <p className="text-sm text-muted-foreground mt-1">
                        Reason: {activeReport.reason}
                      </p>
                    </div>
                    
                    <div className="p-4 rounded-lg border border-accent/20 bg-accent/5">
                      <p className="font-medium mb-2 text-foreground flex items-center gap-2">
                        <span>🤖</span> Live Agent Report
                      </p>
                      <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
                        {activeReport.agent_report}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-4 text-red-500">Error loading data.</div>
              )}
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
};