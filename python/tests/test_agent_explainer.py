"""
SentinAL: Agent Explainer Tests
================================
Unit tests for GraphRAG compliance agent.

Author: SentinAL Testing Team
Date: 2026-01-23
"""

import pytest
import networkx as nx
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_explainer import GraphQueryTool, FraudExplainerAgent


@pytest.fixture
def sample_graph():
    """Create sample graph for testing"""
    G = nx.DiGraph()
    
    # Add nodes
    for i in range(10):
        G.add_node(i, account_age_days=365, risk_score_initial=0.5, is_fraud=0)
    
    # Mark some as fraud
    for i in [7, 8, 9]:
        G.nodes[i]['is_fraud'] = 1
    
    # Add edges
    G.add_edge(0, 1, amount=100, timestamp="2025-01-01", transaction_type="payment")
    G.add_edge(1, 2, amount=200, timestamp="2025-01-02", transaction_type="transfer")
    G.add_edge(7, 8, amount=1000, timestamp="2025-01-03", transaction_type="transfer")
    G.add_edge(8, 9, amount=950, timestamp="2025-01-04", transaction_type="transfer")
    G.add_edge(9, 7, amount=900, timestamp="2025-01-05", transaction_type="transfer")  # Cycle
    
    return G


@pytest.fixture
def sample_fraud_scores():
    """Create sample fraud scores"""
    return {
        'fraud_probability': [0.1] * 7 + [0.9, 0.85, 0.88],
        'true_label': [0] * 7 + [1, 1, 1],
        'predicted_label': [0] * 7 + [1, 1, 1]
    }


class TestGraphQueryTool:
    """Test suite for GraphQueryTool"""
    
    def test_get_user_info(self, sample_graph, sample_fraud_scores):
        """Test user info retrieval"""
        tool = GraphQueryTool(sample_graph, sample_fraud_scores)
        
        info = tool.get_user_info(0)
        
        assert "ID: 0" in info
        assert "Account Age" in info
        assert "Risk Score" in info
        assert "Fraud Probability" in info
    
    def test_get_user_info_not_found(self, sample_graph, sample_fraud_scores):
        """Test user info for non-existent user"""
        tool = GraphQueryTool(sample_graph, sample_fraud_scores)
        
        info = tool.get_user_info(999)
        
        assert "not found" in info
    
    def test_get_k_hop_subgraph(self, sample_graph, sample_fraud_scores):
        """Test k-hop subgraph extraction"""
        tool = GraphQueryTool(sample_graph, sample_fraud_scores)
        
        subgraph_info = tool.get_k_hop_subgraph(0, k=2)
        
        assert "TRANSACTION TOPOLOGY" in subgraph_info
        assert "Network Size" in subgraph_info
    
    def test_cycle_detection(self, sample_graph, sample_fraud_scores):
        """Test cycle detection in fraud ring"""
        tool = GraphQueryTool(sample_graph, sample_fraud_scores)
        
        # User 7 is part of a cycle (7 -> 8 -> 9 -> 7)
        subgraph_info = tool.get_k_hop_subgraph(7, k=2)
        
        assert "CYCLIC PATTERN DETECTED" in subgraph_info or "Loop" in subgraph_info


class TestFraudExplainerAgent:
    """Test suite for FraudExplainerAgent"""
    
    def test_agent_initialization(self, sample_graph, sample_fraud_scores):
        """Test agent initialization"""
        # Note: This will try to connect to Ollama, which may not be available in tests
        # We'll skip actual LLM calls in unit tests
        agent = FraudExplainerAgent(
            sample_graph,
            sample_fraud_scores,
            model="llama3.2:1b"
        )
        
        assert agent.graph is not None
        assert agent.fraud_scores is not None
        assert agent.tool is not None
    
    @pytest.mark.skip(reason="Requires Ollama to be running")
    def test_explain(self, sample_graph, sample_fraud_scores):
        """Test explanation generation (requires Ollama)"""
        agent = FraudExplainerAgent(sample_graph, sample_fraud_scores)
        
        explanation = agent.explain(7)
        
        assert isinstance(explanation, str)
        assert len(explanation) > 0
