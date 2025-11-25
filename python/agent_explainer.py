"""
SentinAL: GraphRAG Compliance Agent
====================================
Module 3 of 3: agent_explainer.py

This module implements a LangChain agent that uses local LLMs (via Ollama)
to explain fraud detections in natural language for compliance officers.

Privacy-First Design:
---------------------
All LLM inference happens locally via Ollama. Financial data never leaves
the local environment - no calls to OpenAI or other cloud services.

Author: [Your Name]
Date: 2025
"""

import networkx as nx
import json
import argparse
import pickle
from typing import List, Dict, Any
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from langchain.schema import AgentAction, AgentFinish


class GraphQueryTool:
    """
    Custom tool that allows the LLM agent to query the transaction graph.
    """
    
    def __init__(self, graph: nx.DiGraph, fraud_scores: Dict):
        """
        Initialize the graph query tool.
        
        Args:
            graph (nx.DiGraph): NetworkX graph of transactions
            fraud_scores (dict): Fraud probability scores from GNN
        """
        self.graph = graph
        self.fraud_scores = fraud_scores
    
    def get_user_info(self, user_id: int) -> str:
        """
        Get basic information about a user node.
        
        Args:
            user_id (int): User node ID
            
        Returns:
            str: Formatted user information
        """
        if user_id not in self.graph.nodes():
            return f"User {user_id} not found in graph."
        
        node_data = self.graph.nodes[user_id]
        fraud_prob = self.fraud_scores['fraud_probability'][user_id]
        
        info = f"""
User {user_id} Profile:
- Account Age: {node_data['account_age_days']} days
- Initial Risk Score: {node_data['risk_score_initial']:.3f}
- GNN Fraud Probability: {fraud_prob:.3f}
- True Label: {'FRAUD' if node_data['is_fraud'] == 1 else 'Normal'}
        """
        
        return info.strip()
    
    def get_k_hop_subgraph(self, user_id: int, k: int = 2) -> str:
        """
        Extract k-hop neighborhood around a user and format as text.
        
        Args:
            user_id (int): Central user node ID
            k (int): Number of hops (default 2)
            
        Returns:
            str: Formatted subgraph description
        """
        if user_id not in self.graph.nodes():
            return f"User {user_id} not found in graph."
        
        # Get k-hop neighbors (BFS)
        neighbors = set([user_id])
        current_layer = {user_id}
        
        for _ in range(k):
            next_layer = set()
            for node in current_layer:
                # Outgoing edges
                next_layer.update(self.graph.successors(node))
                # Incoming edges
                next_layer.update(self.graph.predecessors(node))
            neighbors.update(next_layer)
            current_layer = next_layer
        
        # Extract subgraph
        subgraph = self.graph.subgraph(neighbors)
        
        # Format as readable text
        output = [f"\n{k}-Hop Subgraph around User {user_id}:"]
        output.append(f"Total users in subgraph: {len(neighbors)}")
        output.append("\nTransaction Connections:")
        
        # List all edges with details
        for from_node, to_node, edge_data in subgraph.edges(data=True):
            from_fraud_prob = self.fraud_scores['fraud_probability'][from_node]
            to_fraud_prob = self.fraud_scores['fraud_probability'][to_node]
            
            output.append(
                f"\n  User {from_node} (fraud_prob: {from_fraud_prob:.2f}) "
                f"--> User {to_node} (fraud_prob: {to_fraud_prob:.2f})"
            )
            output.append(f"    Amount: ${edge_data['amount']:.2f}")
            output.append(f"    Type: {edge_data['transaction_type']}")
            output.append(f"    Timestamp: {edge_data['timestamp']}")
            if edge_data.get('is_fraud_edge', 0) == 1:
                output.append(f"    ⚠️  FLAGGED AS FRAUD EDGE")
        
        # Detect cycles
        cycles = self._find_cycles_involving_node(subgraph, user_id)
        if cycles:
            output.append("\n⚠️  CYCLIC PATTERNS DETECTED:")
            for cycle in cycles:
                cycle_str = " → ".join([f"User {node}" for node in cycle])
                output.append(f"  {cycle_str}")
        
        return "\n".join(output)
    
    def _find_cycles_involving_node(self, subgraph: nx.DiGraph, node_id: int) -> List[List[int]]:
        """
        Find all simple cycles that include the specified node.
        
        Args:
            subgraph (nx.DiGraph): Subgraph to search
            node_id (int): Node that must be in the cycle
            
        Returns:
            List[List[int]]: List of cycles (each cycle is a list of node IDs)
        """
        try:
            all_cycles = list(nx.simple_cycles(subgraph))
            return [cycle for cycle in all_cycles if node_id in cycle]
        except:
            return []


class FraudExplainerAgent:
    """
    LangChain agent that explains fraud detections using local LLMs.
    """
    
    def __init__(self, graph: nx.DiGraph, fraud_scores: Dict, model: str = "llama3"):
        """
        Initialize the fraud explainer agent.
        
        Args:
            graph (nx.DiGraph): Transaction graph
            fraud_scores (dict): GNN fraud scores
            model (str): Ollama model to use (default: "llama3")
        """
        self.graph = graph
        self.fraud_scores = fraud_scores
        
        # Initialize local LLM via Ollama
        print(f"\nInitializing Ollama with model: {model}")
        print("⚠️  Make sure Ollama is running: 'ollama serve'")
        
        self.llm = Ollama(
            model=model,
            temperature=0.3  # Lower temperature for more factual responses
        )
        
        # Create graph query tool
        graph_tool = GraphQueryTool(graph, fraud_scores)
        
        # Define tools available to the agent
        self.tools = [
            Tool(
                name="GetUserInfo",
                func=graph_tool.get_user_info,
                description="Get basic profile information about a user including fraud probability. Input: user_id (integer)"
            ),
            Tool(
                name="GetSubgraph",
                func=lambda user_id: graph_tool.get_k_hop_subgraph(int(user_id), k=2),
                description="Get the 2-hop transaction network around a user. Shows all connected users and transactions. Input: user_id (integer)"
            )
        ]
        
        # Create agent prompt
        self.prompt = self._create_prompt()
        
        # Create agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def _create_prompt(self) -> PromptTemplate:
        """
        Create the compliance officer agent prompt.
        
        Returns:
            PromptTemplate: LangChain prompt template
        """
        template = """You are a fraud compliance officer at PayPal analyzing suspicious financial transactions.
Your job is to explain complex fraud patterns detected by machine learning models in clear, plain English.

You have access to the following tools:
{tools}

Tool Names: {tool_names}

Analysis Guidelines:
1. Start by getting the user's basic info and fraud probability
2. Then examine their transaction network (2-hop subgraph)
3. Look for suspicious patterns:
   - Cyclic flows (money moving in circles)
   - Rapid sequential transfers
   - Connections to other high-risk users
4. Explain WHY these patterns indicate money laundering or fraud

Use this format:

Question: the input question you must answer
Thought: think about what information you need
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat Thought/Action/Observation as needed)
Thought: I now have enough information to provide a final answer
Final Answer: your detailed explanation in plain English

Begin!

Question: {input}
Thought: {agent_scratchpad}
"""
        
        return PromptTemplate(
            template=template,
            input_variables=["input", "agent_scratchpad"],
            partial_variables={
                "tools": "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools]),
                "tool_names": ", ".join([tool.name for tool in self.tools])
            }
        )
    
    def explain(self, user_id: int) -> str:
        """
        Generate a natural language explanation of why a user was flagged.
        
        Args:
            user_id (int): User node ID to explain
            
        Returns:
            str: Natural language explanation
        """
        fraud_prob = self.fraud_scores['fraud_probability'][user_id]
        
        query = f"""Analyze User {user_id} who has a fraud probability of {fraud_prob:.3f}. 
Explain in detail why this user was flagged for suspicious activity. 
Focus on transaction patterns, connections to other risky users, and any cyclic money flows."""
        
        try:
            result = self.agent_executor.invoke({"input": query})
            return result['output']
        except Exception as e:
            return f"Error generating explanation: {str(e)}"


def load_data():
    """
    Load the graph and fraud scores.
    
    Returns:
        tuple: (graph, fraud_scores)
    """
    print("\nLoading data...")
    
    # Load NetworkX graph
    with open('data/graph.pkl', 'rb') as f:
        graph = pickle.load(f)
    print(f"✓ Loaded graph with {graph.number_of_nodes()} nodes")
    
    # Load fraud scores
    with open('reports/fraud_scores.json', 'r') as f:
        fraud_scores = json.load(f)
    print(f"✓ Loaded fraud scores")
    
    return graph, fraud_scores


def main():
    """
    Main execution function for the fraud explainer agent.
    """
    parser = argparse.ArgumentParser(description='SentinAL Fraud Explainer Agent')
    parser.add_argument('--user_id', type=int, help='User ID to explain')
    parser.add_argument('--model', type=str, default='llama3', 
                       help='Ollama model to use (default: llama3)')
    parser.add_argument('--top_n', type=int, default=5,
                       help='Explain top N suspicious users (if --user_id not provided)')
    
    args = parser.parse_args()
    
    print("="*70)
    print("SentinAL: GraphRAG Fraud Explainer")
    print("="*70)
    
    # Load data
    graph, fraud_scores = load_data()
    
    # Initialize agent
    agent = FraudExplainerAgent(graph, fraud_scores, model=args.model)
    
    if args.user_id is not None:
        # Explain specific user
        print(f"\n{'='*70}")
        print(f"EXPLAINING USER {args.user_id}")
        print('='*70)
        
        explanation = agent.explain(args.user_id)
        
        print(f"\n{'='*70}")
        print("FINAL COMPLIANCE REPORT")
        print('='*70)
        print(explanation)
        
    else:
        # Explain top N suspicious users
        import numpy as np
        fraud_probs = np.array(fraud_scores['fraud_probability'])
        top_indices = np.argsort(fraud_probs)[-args.top_n:][::-1]
        
        print(f"\nExplaining top {args.top_n} most suspicious users...")
        
        for rank, user_id in enumerate(top_indices, 1):
            print(f"\n{'='*70}")
            print(f"RANK {rank}: USER {user_id} (Fraud Prob: {fraud_probs[user_id]:.3f})")
            print('='*70)
            
            explanation = agent.explain(int(user_id))
            
            print(f"\n{'-'*70}")
            print("COMPLIANCE REPORT")
            print('-'*70)
            print(explanation)
            print()


if __name__ == "__main__":
    main()
