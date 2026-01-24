import { useState } from "react";
import { Card } from "./ui/card";
import { AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { GraphVisualization } from "./GraphVisualization";

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

  // Function to call the Python API
  const handleNodeClick = async (nodeId: number) => {
    if (selectedNode === nodeId) return; // Don't reload if already selected

    setSelectedNode(nodeId);
    setLoading(true);
    setActiveReport(null); // Clear previous report

    try {
      // FETCH FROM YOUR PYTHON API
      // Since we are using the public demo endpoint /analyze/{user_id} which does not require auth
      // This matches the previous logic.
      const response = await fetch(`http://localhost:8080/analyze/${nodeId}`);
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

  return (
    <section className="bg-muted/30 py-10 h-screen flex flex-col">
      <div className="container mx-auto px-4 flex-grow flex flex-col h-full">
        <div className="mx-auto max-w-7xl w-full h-full flex flex-col">
          <h2 className="text-3xl font-bold mb-4 text-center text-foreground flex-shrink-0">
            Live AI Detection
          </h2>
          <p className="text-center text-muted-foreground mb-8 max-w-2xl mx-auto flex-shrink-0">
            Interactive Analysis: Click a node to trigger a real-time request to the Python/Llama3 Agent
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 flex-grow h-0 min-h-[600px]">
            {/* LEFT COLUMN: THE GRAPH (Takes up 2/3 space) */}
            <Card className="col-span-1 lg:col-span-2 p-1 bg-card border-border shadow-md overflow-hidden flex flex-col h-full">
              <div className="flex-grow relative h-full">
                <GraphVisualization
                  onNodeSelect={handleNodeClick}
                  selectedNodeId={selectedNode}
                />
              </div>
            </Card>

            {/* RIGHT COLUMN: REAL-TIME API RESULTS (Takes up 1/3 space) */}
            <Card className="p-6 bg-card border-border shadow-md overflow-y-auto h-full">
              <h3 className="font-semibold mb-4 text-card-foreground">
                AI Agent Analysis {selectedNode && `(User ${selectedNode})`}
              </h3>

              {!selectedNode ? (
                <div className="flex items-center justify-center h-40 text-muted-foreground">
                  Select a node to query the Python Backend
                </div>
              ) : loading ? (
                <div className="flex flex-col items-center justify-center h-40 text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin mb-2" />
                  <p>Running GraphRAG Analysis...</p>
                  <p className="text-xs text-muted-foreground mt-2">(Querying Llama3 Model)</p>
                </div>
              ) : activeReport ? (
                <div className="space-y-4 animate-in fade-in duration-500">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-muted/50">
                    {activeReport.is_fraud ? (
                      <AlertCircle className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
                    ) : (
                      <CheckCircle className="h-6 w-6 text-green-500 flex-shrink-0 mt-0.5" />
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
                        Score: <span className={`font-semibold ${activeReport.is_fraud ? "text-red-500" : "text-green-500"}`}>
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