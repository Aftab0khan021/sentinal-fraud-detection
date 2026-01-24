"""
SentinAL: Data Generation Tests
================================
Unit tests for synthetic financial graph generation.

Author: SentinAL Testing Team
Date: 2026-01-23
"""

import pytest
import networkx as nx
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_gen import FinancialGraphGenerator


class TestFinancialGraphGenerator:
    """Test suite for FinancialGraphGenerator"""
    
    def test_initialization(self):
        """Test generator initialization"""
        generator = FinancialGraphGenerator(num_users=50, fraud_ring_size=3)
        
        assert generator.num_users == 50
        assert generator.fraud_ring_size == 3
        assert isinstance(generator.graph, nx.DiGraph)
        assert len(generator.transaction_types) == 3
    
    def test_generate_user_features(self):
        """Test user node feature generation"""
        generator = FinancialGraphGenerator(num_users=20)
        generator.generate_user_features()
        
        # Check all users created
        assert generator.graph.number_of_nodes() == 20
        
        # Check node attributes
        for node_id in range(20):
            node_data = generator.graph.nodes[node_id]
            assert 'account_age_days' in node_data
            assert 'risk_score_initial' in node_data
            assert 'is_fraud' in node_data
            
            # Check value ranges
            assert 30 <= node_data['account_age_days'] <= 1825
            assert 0 <= node_data['risk_score_initial'] <= 1
            assert node_data['is_fraud'] in [0, 1]
    
    def test_inject_fraud_ring(self):
        """Test fraud ring injection"""
        generator = FinancialGraphGenerator(num_users=30, fraud_ring_size=5)
        generator.generate_user_features()
        fraud_users = generator.inject_fraud_ring()
        
        # Check fraud ring size
        assert len(fraud_users) == 5
        
        # Check all fraud users are marked
        for user_id in fraud_users:
            assert generator.graph.nodes[user_id]['is_fraud'] == 1
        
        # Check cyclic edges exist
        for i in range(len(fraud_users)):
            from_user = fraud_users[i]
            to_user = fraud_users[(i + 1) % len(fraud_users)]
            assert generator.graph.has_edge(from_user, to_user)
            
            # Check edge attributes
            edge_data = generator.graph[from_user][to_user]
            assert 'amount' in edge_data
            assert 'timestamp' in edge_data
            assert 'transaction_type' in edge_data
            assert edge_data['is_fraud_edge'] == 1
    
    def test_generate_normal_transactions(self):
        """Test normal transaction generation"""
        generator = FinancialGraphGenerator(num_users=25)
        generator.generate_user_features()
        generator.generate_normal_transactions(num_transactions=50)
        
        # Check transactions created
        assert generator.graph.number_of_edges() >= 40  # Some may be duplicates
        
        # Check edge attributes
        for u, v, data in generator.graph.edges(data=True):
            assert 'amount' in data
            assert 'timestamp' in data
            assert 'transaction_type' in data
            assert data['transaction_type'] in generator.transaction_types
            assert 10 <= data['amount'] <= 5000
    
    def test_to_pytorch_geometric(self):
        """Test conversion to PyTorch Geometric format"""
        generator = FinancialGraphGenerator(num_users=15, fraud_ring_size=3)
        generator.generate_user_features()
        generator.inject_fraud_ring()
        generator.generate_normal_transactions(num_transactions=30)
        
        pyg_data = generator.to_pytorch_geometric()
        
        # Check data structure
        assert hasattr(pyg_data, 'x')  # Node features
        assert hasattr(pyg_data, 'edge_index')  # Edge connectivity
        assert hasattr(pyg_data, 'edge_attr')  # Edge features
        assert hasattr(pyg_data, 'edge_type')  # Edge types
        assert hasattr(pyg_data, 'y')  # Node labels
        
        # Check dimensions
        assert pyg_data.x.shape[0] == 15  # Number of nodes
        assert pyg_data.x.shape[1] == 2  # Number of features
        assert pyg_data.y.shape[0] == 15  # Number of labels
        assert pyg_data.edge_index.shape[0] == 2  # Source and target
        
        # Check data types
        assert pyg_data.x.dtype == torch.float
        assert pyg_data.y.dtype == torch.long
        assert pyg_data.edge_type.dtype == torch.long
    
    def test_fraud_ring_cycle(self):
        """Test that fraud ring forms a complete cycle"""
        generator = FinancialGraphGenerator(num_users=20, fraud_ring_size=4)
        generator.generate_user_features()
        fraud_users = generator.inject_fraud_ring()
        
        # Check cycle exists
        cycles = list(nx.simple_cycles(generator.graph))
        fraud_cycle_found = False
        
        for cycle in cycles:
            if set(cycle) == set(fraud_users):
                fraud_cycle_found = True
                break
        
        assert fraud_cycle_found, "Fraud ring should form a cycle"
    
    def test_no_self_loops_in_normal_transactions(self):
        """Test that normal transactions don't create self-loops"""
        generator = FinancialGraphGenerator(num_users=20)
        generator.generate_user_features()
        generator.generate_normal_transactions(num_transactions=100)
        
        # Check no self-loops
        for u, v in generator.graph.edges():
            assert u != v, "Should not have self-loops"
    
    def test_reproducibility(self):
        """Test that results are reproducible with same seed"""
        # First generation
        generator1 = FinancialGraphGenerator(num_users=10, fraud_ring_size=3)
        generator1.generate_user_features()
        fraud_users1 = generator1.inject_fraud_ring()
        
        # Second generation (seeds are reset in module)
        generator2 = FinancialGraphGenerator(num_users=10, fraud_ring_size=3)
        generator2.generate_user_features()
        fraud_users2 = generator2.inject_fraud_ring()
        
        # Should generate same fraud users
        assert fraud_users1 == fraud_users2
    
    def test_edge_type_mapping(self):
        """Test that edge types are correctly mapped"""
        generator = FinancialGraphGenerator(num_users=10)
        generator.generate_user_features()
        generator.generate_normal_transactions(num_transactions=20)
        
        pyg_data = generator.to_pytorch_geometric()
        
        # All edge types should be 0, 1, or 2
        assert torch.all(pyg_data.edge_type >= 0)
        assert torch.all(pyg_data.edge_type <= 2)
    
    def test_node_feature_normalization(self):
        """Test that node features are properly normalized"""
        generator = FinancialGraphGenerator(num_users=15)
        generator.generate_user_features()
        
        pyg_data = generator.to_pytorch_geometric()
        
        # Account age should be normalized to [0, 1]
        assert torch.all(pyg_data.x[:, 0] >= 0)
        assert torch.all(pyg_data.x[:, 0] <= 1)
        
        # Risk score should be in [0, 1]
        assert torch.all(pyg_data.x[:, 1] >= 0)
        assert torch.all(pyg_data.x[:, 1] <= 1)


def test_main_function():
    """Test that main function runs without errors"""
    import tempfile
    import os
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        original_dir = os.getcwd()
        try:
            os.chdir(tmpdir)
            os.makedirs('data', exist_ok=True)
            
            # Run main (this will save files)
            from data_gen import main
            main()
            
            # Check files were created
            assert os.path.exists('data/graph.pkl')
            assert os.path.exists('data/graph_pyg.pt')
            
        finally:
            os.chdir(original_dir)
