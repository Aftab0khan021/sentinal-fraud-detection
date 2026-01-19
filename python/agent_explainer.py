"""
SentinAL: GraphRAG Compliance Agent (Direct Mode)
=================================================
Module 3 of 3: agent_explainer.py

This version runs the graph analysis tools MANUALLY in Python and uses the LLM
ONLY for the final summarization. This bypasses 'Invalid Format' errors common
with smaller models like Llama 3.2 1B.

Author: SentinAL Project
Date: 2025
"""

import networkx as nx
import json
import argparse
import pickle
from typing import List, Dict
import warnings

# Suppress warnings to keep output clean
warnings.filterwarnings("ignore")

# We only need Ollama, no complex Agent classes needed anymore
from langchain_community.llms import Ollama

class GraphQueryTool:
    """Helper class to extract graph data."""
    
    def __init__(self, graph: nx.DiGraph, fraud_scores: Dict):
        self.graph = graph
        self.fraud_scores = fraud_scores
    
    def get_user_info(self, user_id: int) -> str:
        if user_id not in self.graph.nodes():
            return f"User {user_id} not found in graph."
        
        node_data = self.graph.nodes[user_id]
        try:
            fraud_prob = self.fraud_scores['fraud_probability'][user_id]
        except:
            fraud_prob = 0.0
        
        return f"""
[NODE PROFILE]
ID: {user_id}
Account Age: {node_data.get('account_age_days', 'N/A')} days
Base Risk Score: {node_data.get('risk_score_initial', 0):.3f}
Model Fraud Probability: {fraud_prob:.3f}
Status: {'FLAGGED' if node_data.get('is_fraud', 0) == 1 else 'Normal'}
"""

    def get_k_hop_subgraph(self, user_id: int, k: int = 2) -> str:
        if user_id not in self.graph.nodes():
            return ""
        
        # Get neighbors (k-hops)
        neighbors = set([user_id])
        current_layer = {user_id}
        for _ in range(k):
            next_layer = set()
            for node in current_layer:
                next_layer.update(self.graph.successors(node))
                next_layer.update(self.graph.predecessors(node))
            neighbors.update(next_layer)
            current_layer = next_layer
        
        subgraph = self.graph.subgraph(neighbors)
        
        output = [f"\n[TRANSACTION TOPOLOGY]"]
        output.append(f"Network Size: {len(neighbors)} related nodes")
        output.append("Recent Flows:")
        
        for u, v, data in subgraph.edges(data=True):
            amt = data.get('amount', 0)
            output.append(f"  Node {u} -> Node {v} | Amount: ${amt:.2f}")
            
        # Detect cycles (Money Laundering Loops)
        try:
            cycles = list(nx.simple_cycles(subgraph))
            user_cycles = [c for c in cycles if user_id in c]
            if user_cycles:
                output.append("\n[ALERT: CYCLIC PATTERN DETECTED]")
                for cycle in user_cycles:
                    path = " -> ".join(str(n) for n in cycle)
                    output.append(f"  Loop: {path} -> {cycle[0]}")
        except:
            pass
            
        return "\n".join(output)

class FraudExplainerAgent:
    """
    Simplified Agent that gathers data first, then asks LLM to summarize.
    """
    def __init__(self, graph: nx.DiGraph, fraud_scores: Dict, model: str = "llama3"):
        self.graph = graph
        self.fraud_scores = fraud_scores
        self.tool = GraphQueryTool(graph, fraud_scores)
        
        print(f"\nInitializing Ollama with model: {model}")
        print("⚠️  Make sure Ollama is running: 'ollama serve'")
        
        # Temperature 0.1 makes it very factual and less likely to hallucinate
        self.llm = Ollama(model=model, temperature=0.1)

    def explain(self, user_id: int) -> str:
        # 1. GATHER DATA (Python does this reliably)
        print(f"  > [System] Fetching profile for Node {user_id}...")
        profile = self.tool.get_user_info(user_id)
        
        print(f"  > [System] Analyzing network topology...")
        topology = self.tool.get_k_hop_subgraph(user_id)
        
        # 2. CONSTRUCT PROMPT (UPDATED FIX)
        # We removed the complex roleplay instruction that was confusing the AI.
        # This direct format works much better with Llama 3.2 1B.
        prompt = f"""
Input Data:
{profile}

Topology:
{topology}

Instruction:
Based on the data above, summarize the fraud risk for this user.
1. Mention the "Model Fraud Probability" score.
2. If there are "Loops" or "Cycles" listed, identify them as suspicious money layering.
3. Keep the response professional, factual, and under 4 sentences.

Response:
"""
        # 3. GENERATE (LLM just summarizes)
        try:
            print("  > [AI] Generating summary report...")
            return self.llm.invoke(prompt)
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"

def load_data():
    print("\nLoading data...")
    try:
        with open('data/graph.pkl', 'rb') as f:
            graph = pickle.load(f)
        print(f"✓ Loaded graph with {graph.number_of_nodes()} nodes")
    except FileNotFoundError:
        print("❌ Error: data/graph.pkl not found. Run data_gen.py first.")
        exit(1)
    
    try:
        with open('reports/fraud_scores.json', 'r') as f:
            fraud_scores = json.load(f)
        print(f"✓ Loaded fraud scores")
    except FileNotFoundError:
        print("❌ Error: reports/fraud_scores.json not found. Run gnn_train.py first.")
        exit(1)
    
    return graph, fraud_scores

def main():
    parser = argparse.ArgumentParser(description='SentinAL Fraud Explainer Agent')
    parser.add_argument('--user_id', type=int, help='User ID to explain')
    parser.add_argument('--model', type=str, default='llama3.2:1b', 
                       help='Ollama model to use')
    parser.add_argument('--top_n', type=int, default=5)
    
    args = parser.parse_args()
    
    print("="*70)
    print("SentinAL: GraphRAG Fraud Explainer")
    print("="*70)
    
    graph, fraud_scores = load_data()
    agent = FraudExplainerAgent(graph, fraud_scores, model=args.model)
    
    if args.user_id is not None:
        print(f"\n{'='*70}")
        print(f"EXPLAINING USER {args.user_id}")
        print('='*70)
        
        explanation = agent.explain(args.user_id)
        
        print(f"\n{'='*70}")
        print("FINAL COMPLIANCE REPORT")
        print('='*70)
        print(explanation)
        
    else:
        import numpy as np
        fraud_probs = np.array(fraud_scores['fraud_probability'])
        top_indices = np.argsort(fraud_probs)[-args.top_n:][::-1]
        
        print(f"\nExplaining top {args.top_n} most suspicious users...")
        
        for rank, user_id in enumerate(top_indices, 1):
            print(f"\n{'='*70}")
            print(f"RANK {rank}: USER {user_id}")
            print('='*70)
            
            explanation = agent.explain(int(user_id))
            
            print(f"\n{'-'*70}")
            print("COMPLIANCE REPORT")
            print('-'*70)
            print(explanation)
            print()

if __name__ == "__main__":
    main()