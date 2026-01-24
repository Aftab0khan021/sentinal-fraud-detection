"""
SentinAL: GNN Training Tests
=============================
Unit tests for R-GCN fraud detector training.

Author: SentinAL Testing Team
Date: 2026-01-23
"""

import pytest
import torch
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from gnn_train import FraudRGCN, FraudDetectorTrainer


@pytest.fixture
def sample_data():
    """Create sample PyG data for testing"""
    num_nodes = 20
    num_edges = 40
    
    x = torch.randn(num_nodes, 2)  # 2 features
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    edge_type = torch.randint(0, 3, (num_edges,))  # 3 relation types
    y = torch.cat([torch.zeros(15), torch.ones(5)]).long()  # 15 normal, 5 fraud
    
    from torch_geometric.data import Data
    return Data(x=x, edge_index=edge_index, edge_type=edge_type, y=y)


class TestFraudRGCN:
    """Test suite for FraudRGCN model"""
    
    def test_model_initialization(self):
        """Test model initialization"""
        model = FraudRGCN(
            num_features=2,
            hidden_channels=32,
            num_relations=3,
            num_classes=2
        )
        
        assert model is not None
        assert hasattr(model, 'conv1')
        assert hasattr(model, 'conv2')
        assert hasattr(model, 'lin')
        assert hasattr(model, 'dropout')
    
    def test_forward_pass(self, sample_data):
        """Test forward pass through model"""
        model = FraudRGCN(
            num_features=2,
            hidden_channels=32,
            num_relations=3
        )
        
        out = model(sample_data.x, sample_data.edge_index, sample_data.edge_type)
        
        # Check output shape
        assert out.shape == (sample_data.num_nodes, 2)
        
        # Check output is log probabilities
        assert torch.all(out <= 0)  # Log probabilities should be <= 0
    
    def test_model_parameters(self):
        """Test that model has trainable parameters"""
        model = FraudRGCN(num_features=2, hidden_channels=32, num_relations=3)
        
        params = list(model.parameters())
        assert len(params) > 0
        
        # Check parameters require gradients
        for param in params:
            assert param.requires_grad


class TestFraudDetectorTrainer:
    """Test suite for FraudDetectorTrainer"""
    
    def test_trainer_initialization(self, sample_data):
        """Test trainer initialization"""
        trainer = FraudDetectorTrainer(sample_data, device='cpu')
        
        assert trainer.data is not None
        assert trainer.model is not None
        assert trainer.optimizer is not None
        assert trainer.criterion is not None
        assert trainer.class_weights is not None
    
    def test_class_weight_calculation(self, sample_data):
        """Test class weight calculation"""
        trainer = FraudDetectorTrainer(sample_data, device='cpu')
        
        # Should have weights for 2 classes
        assert trainer.class_weights.shape[0] == 2
        
        # Fraud class should have higher weight (it's minority)
        assert trainer.class_weights[1] > trainer.class_weights[0]
    
    def test_train_epoch(self, sample_data):
        """Test single training epoch"""
        trainer = FraudDetectorTrainer(sample_data, device='cpu')
        
        loss = trainer.train_epoch()
        
        # Loss should be a positive number
        assert isinstance(loss, float)
        assert loss > 0
    
    def test_evaluate(self, sample_data):
        """Test model evaluation"""
        trainer = FraudDetectorTrainer(sample_data, device='cpu')
        
        metrics = trainer.evaluate()
        
        # Check metrics exist
        assert 'accuracy' in metrics
        assert 'roc_auc' in metrics
        assert 'predictions' in metrics
        assert 'probabilities' in metrics
        assert 'true_labels' in metrics
        
        # Check metric ranges
        assert 0 <= metrics['accuracy'] <= 1
        assert 0 <= metrics['roc_auc'] <= 1
    
    def test_model_improvement(self, sample_data):
        """Test that model improves with training"""
        trainer = FraudDetectorTrainer(sample_data, device='cpu')
        
        # Initial evaluation
        initial_metrics = trainer.evaluate()
        initial_accuracy = initial_metrics['accuracy']
        
        # Train for a few epochs
        for _ in range(10):
            trainer.train_epoch()
        
        # Final evaluation
        final_metrics = trainer.evaluate()
        final_accuracy = final_metrics['accuracy']
        
        # Accuracy should improve or stay same (may not always improve in 10 epochs)
        assert final_accuracy >= initial_accuracy - 0.1  # Allow small variance
