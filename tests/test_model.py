
import unittest
import torch
import sys
import os

# Add python directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

from gnn_train import FraudRGCN

class TestFraudGNN(unittest.TestCase):
    def setUp(self):
        self.num_features = 10
        self.hidden_channels = 16
        self.num_relations = 3
        self.num_classes = 2
        
        self.model = FraudRGCN(
            num_features=self.num_features,
            hidden_channels=self.hidden_channels,
            num_relations=self.num_relations,
            num_classes=self.num_classes,
            num_layers=2,
            dropout=0.1
        )

    def test_model_structure(self):
        """Test if model layers are correctly initialized"""
        self.assertEqual(len(self.model.convs), 2)
        self.assertIsInstance(self.model.lin, torch.nn.Linear)

    def test_forward_pass(self):
        """Test forward pass output shape"""
        num_nodes = 50
        num_edges = 100
        
        # Create dummy data
        x = torch.randn(num_nodes, self.num_features)
        edge_index = torch.randint(0, num_nodes, (2, num_edges))
        edge_type = torch.randint(0, self.num_relations, (num_edges,))

        # Forward
        out = self.model(x, edge_index, edge_type)
        
        # Check output
        self.assertEqual(out.shape, (num_nodes, self.num_classes))
        
        # Check if output is log_softmax (all values <= 0)
        self.assertTrue(torch.all(out <= 0))

if __name__ == '__main__':
    unittest.main()
