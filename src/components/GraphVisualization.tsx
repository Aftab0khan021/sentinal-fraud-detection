import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { Card } from './ui/card';
import { Loader2, ZoomIn, ZoomOut, RefreshCw, Filter } from 'lucide-react';
import { Button } from './ui/button';
import { api } from '@/services/api';

interface Node extends d3.SimulationNodeDatum {
    id: string;
    is_fraud: boolean;
    risk_score: number;
    fraud_probability: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
    source: string | Node;
    target: string | Node;
    amount: number;
    is_laundering: boolean;
}

interface GraphData {
    nodes: Node[];
    links: Link[];
}

interface GraphVisualizationProps {
    onNodeSelect: (nodeId: number) => void;
    selectedNodeId?: number | null;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
    onNodeSelect,
    selectedNodeId
}) => {
    const svgRef = useRef<SVGSVGElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [data, setData] = useState<GraphData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [simulation, setSimulation] = useState<d3.Simulation<Node, Link> | null>(null);
    const [transform, setTransform] = useState<d3.ZoomTransform>(d3.zoomIdentity);

    // Fetch Data
    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const jsonData = await api.getGraphData();
            setData(jsonData);

            // Initialize simulation with new data
            if (jsonData.nodes.length > 0) {
                initSimulation(jsonData.nodes, jsonData.links);
            }
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || err.message || "An error occurred");
            // Fallback data for demo if API fails
            const fallbackNodes = Array.from({ length: 20 }, (_, i) => ({
                id: i.toString(),
                is_fraud: i % 5 === 0,
                risk_score: Math.random(),
                fraud_probability: i % 5 === 0 ? 0.9 : 0.1
            }));
            const fallbackLinks = [];
            for (let i = 0; i < 20; i++) {
                if (i < 19) fallbackLinks.push({ source: i.toString(), target: (i + 1).toString(), amount: 1000, is_laundering: false });
                if (i % 5 === 0) fallbackLinks.push({ source: i.toString(), target: ((i + 2) % 20).toString(), amount: 5000, is_laundering: true });
            }
            setData({ nodes: fallbackNodes, links: fallbackLinks });
            initSimulation(fallbackNodes, fallbackLinks);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    // Initialize D3 Simulation
    const initSimulation = (nodes: Node[], links: Link[]) => {
        if (!svgRef.current || !containerRef.current) return;

        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;

        // Clear previous simulation
        if (simulation) simulation.stop();

        const sim = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id((d: any) => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(30));

        setSimulation(sim);
    };

    // Render Graph
    useEffect(() => {
        if (!simulation || !data || !svgRef.current) return;

        const svg = d3.select(svgRef.current);

        // Zoom behavior
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event) => {
                setTransform(event.transform);
                d3.select("#graph-group").attr("transform", event.transform);
            });

        svg.call(zoom);

        // Initial render logic updates are handled by Rerender on transform/data change usually, 
        // but D3 works best with direct DOM manipulation for the simulation tick.
        // However, for React, we can let D3 handle the positions and React render the elements, 
        // OR likely better: Let React render elements based on state, but that might be slow.
        // Best practice: Let D3 manage DOM or use a ref to sync. 
        // For this simple case, I'll use the "D3 updates DOM" approach for performance.

        const g = d3.select("#graph-group");
        g.selectAll("*").remove(); // Clear previous

        // Links
        const link = g.append("g")
            .selectAll("line")
            .data(data.links)
            .enter().append("line")
            .attr("stroke", d => d.is_laundering ? "#ef4444" : "#94a3b8")
            .attr("stroke-width", d => d.is_laundering ? 2 : 1)
            .attr("stroke-opacity", 0.6);

        // Nodes
        const node = g.append("g")
            .selectAll("g")
            .data(data.nodes)
            .enter().append("g")
            .attr("cursor", "pointer")
            .call(d3.drag<any, any>()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => d.is_fraud ? 8 : 5)
            .attr("fill", d => d.is_fraud ? "#ef4444" : "#22c55e")
            .attr("stroke", "#ffffff")
            .attr("stroke-width", 1.5);

        // Highlight selected
        if (selectedNodeId !== null && selectedNodeId !== undefined) {
            node.filter(d => parseInt(d.id) === selectedNodeId)
                .append("circle")
                .attr("r", 12)
                .attr("fill", "none")
                .attr("stroke", "#3b82f6")
                .attr("stroke-width", 2);
        }

        node.append("title")
            .text(d => `User ${d.id}\nScore: ${d.fraud_probability.toFixed(3)}`);

        node.on("click", (event, d) => {
            onNodeSelect(parseInt(d.id));
        });

        simulation.on("tick", () => {
            link
                .attr("x1", d => (d.source as Node).x!)
                .attr("y1", d => (d.source as Node).y!)
                .attr("x2", d => (d.target as Node).x!)
                .attr("y2", d => (d.target as Node).y!);

            node
                .attr("transform", d => `translate(${d.x},${d.y})`);
        });

        function dragstarted(event: any, d: any) {
            if (!event.active) simulation?.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event: any, d: any) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event: any, d: any) {
            if (!event.active) simulation?.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return () => {
            simulation.stop();
        };
    }, [simulation, data, selectedNodeId]); // Re-bind if simulation or data changes

    // Zoom Controls
    const handleZoomIn = () => {
        if (!svgRef.current) return;
        d3.select(svgRef.current).transition().duration(300).call(d3.zoom<SVGSVGElement, unknown>().scaleBy, 1.2);
    };

    const handleZoomOut = () => {
        if (!svgRef.current) return;
        d3.select(svgRef.current).transition().duration(300).call(d3.zoom<SVGSVGElement, unknown>().scaleBy, 0.8);
    };

    const handleReset = () => {
        if (!svgRef.current) return;
        d3.select(svgRef.current).transition().duration(500).call(d3.zoom<SVGSVGElement, unknown>().transform, d3.zoomIdentity);
    };

    return (
        <div className="relative w-full h-[600px] border border-border rounded-lg bg-slate-950 overflow-hidden shadow-inner" ref={containerRef}>
            {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-background/50 z-50">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
            )}

            {error && !loading && !data && (
                <div className="absolute inset-0 flex items-center justify-center text-red-500 z-50">
                    <p>{error}</p>
                </div>
            )}

            {/* Controls */}
            <div className="absolute bottom-4 right-4 flex flex-col gap-2 z-10">
                <Button variant="secondary" size="icon" onClick={handleZoomIn} title="Zoom In">
                    <ZoomIn className="w-4 h-4" />
                </Button>
                <Button variant="secondary" size="icon" onClick={handleZoomOut} title="Zoom Out">
                    <ZoomOut className="w-4 h-4" />
                </Button>
                <Button variant="secondary" size="icon" onClick={handleReset} title="Reset View">
                    <RefreshCw className="w-4 h-4" />
                </Button>
            </div>

            {/* Legend */}
            <div className="absolute top-4 left-4 p-3 bg-card/90 backdrop-blur rounded-lg border border-border text-xs shadow-lg z-10">
                <h4 className="font-semibold mb-2">Network Legend</h4>
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-red-500"></div>
                    <span>Fraudulent User</span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-3 h-3 rounded-full bg-green-500"></div>
                    <span>Legitimate User</span>
                </div>
                <div className="flex items-center gap-2 mb-1">
                    <div className="w-4 h-0.5 bg-red-500"></div>
                    <span>Suspicious Flow</span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-4 h-0.5 bg-slate-400"></div>
                    <span>Normal Transaction</span>
                </div>
            </div>

            <svg ref={svgRef} className="w-full h-full cursor-move">
                <g id="graph-group"></g>
            </svg>
        </div>
    );
};
