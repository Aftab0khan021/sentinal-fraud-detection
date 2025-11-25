"""
SentinAL: GNN Fraud Detector
=============================
Module 2 of 3: gnn_train.py

This module implements a Relational Graph Convolutional Network (R-GCN)
to detect fraud rings in the synthetic financial transaction network.

Why R-GCN?
----------
Standard GCNs treat all edges the same. R-GCN handles different edge types
(payment, transfer, withdrawal) with separate weight matrices, making it
ideal for heterogeneous financial transaction graphs.

Author: [Your Name]
Date: 2025
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv
from torch_geometric.data import Data
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


class FraudRGCN(torch.nn.Module):
    """
    Relational Graph Convolutional Network for fraud detection.
    
    Architecture:
        - 2 R-GCN layers with ReLU activation
        - Handles 3 relation types (payment, transfer, withdrawal)
        - Binary classification output (fraud vs. normal)
    """
    
    def __init__(self, num_features, hidden_channels, num_relations, num_classes=2):
        """
        Initialize the R-GCN model.
        
        Args:
            num_features (int): Number of input node features
            hidden_channels (int): Hidden dimension size
            num_relations (int): Number of edge types (transaction types)
            num_classes (int): Number of output classes (2 for binary)
        """
        super(FraudRGCN, self).__init__()
        
        # First R-GCN layer: input features -> hidden
        self.conv1 = RGCNConv(
            num_features,
            hidden_channels,
            num_relations=num_relations
        )
        
        # Second R-GCN layer: hidden -> hidden
        self.conv2 = RGCNConv(
            hidden_channels,
            hidden_channels,
            num_relations=num_relations
        )
        
        # Final linear layer for classification
        self.lin = torch.nn.Linear(hidden_channels, num_classes)
        
        self.dropout = torch.nn.Dropout(p=0.3)
    
    def forward(self, x, edge_index, edge_type):
        """
        Forward pass through the network.
        
        Args:
            x (Tensor): Node feature matrix [num_nodes, num_features]
            edge_index (Tensor): Edge connectivity [2, num_edges]
            edge_type (Tensor): Edge type for each edge [num_edges]
            
        Returns:
            Tensor: Log probabilities for each class [num_nodes, num_classes]
        """
        # First R-GCN layer + ReLU + Dropout
        x = self.conv1(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Second R-GCN layer + ReLU + Dropout
        x = self.conv2(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Classification layer
        x = self.lin(x)
        
        # Return log softmax for use with NLLLoss
        return F.log_softmax(x, dim=1)


class FraudDetectorTrainer:
    """
    Handles training, evaluation, and visualization of the fraud detection model.
    """
    
    def __init__(self, data, device='cpu'):
        """
        Initialize the trainer.
        
        Args:
            data (Data): PyTorch Geometric data object
            device (str): Device to train on ('cpu' or 'cuda')
        """
        self.data = data.to(device)
        self.device = device
        
        # Calculate class weights to handle imbalance
        # Fraud is rare, so we need to weight it higher
        self.class_weights = self._calculate_class_weights()
        
        # Initialize model
        self.model = FraudRGCN(
            num_features=data.x.size(1),
            hidden_channels=64,
            num_relations=3,  # payment, transfer, withdrawal
            num_classes=2
        ).to(device)
        
        # Optimizer
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=0.01,
            weight_decay=5e-4
        )
        
        # Loss function with class weights
        self.criterion = torch.nn.NLLLoss(weight=self.class_weights)
        
    def _calculate_class_weights(self):
        """
        Calculate inverse class frequency weights to handle imbalance.
        
        Returns:
            Tensor: Class weights [num_classes]
        """
        y = self.data.y.cpu().numpy()
        class_counts = np.bincount(y)
        class_weights = 1.0 / class_counts
        class_weights = class_weights / class_weights.sum() * len(class_counts)
        
        print(f"\nClass distribution:")
        print(f"  Normal users: {class_counts[0]} ({class_counts[0]/len(y)*100:.1f}%)")
        print(f"  Fraud users: {class_counts[1]} ({class_counts[1]/len(y)*100:.1f}%)")
        print(f"Class weights: {class_weights}")
        
        return torch.tensor(class_weights, dtype=torch.float).to(self.device)
    
    def train_epoch(self):
        """
        Train the model for one epoch.
        
        Returns:
            float: Training loss
        """
        self.model.train()
        self.optimizer.zero_grad()
        
        # Forward pass
        out = self.model(self.data.x, self.data.edge_index, self.data.edge_type)
        
        # Calculate loss
        loss = self.criterion(out, self.data.y)
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    @torch.no_grad()
    def evaluate(self):
        """
        Evaluate the model on the full dataset.
        
        Returns:
            dict: Evaluation metrics
        """
        self.model.eval()
        
        # Get predictions
        out = self.model(self.data.x, self.data.edge_index, self.data.edge_type)
        pred = out.argmax(dim=1)
        
        # Get probabilities for fraud class
        prob = torch.exp(out[:, 1])
        
        # Calculate metrics
        y_true = self.data.y.cpu().numpy()
        y_pred = pred.cpu().numpy()
        y_prob = prob.cpu().numpy()
        
        accuracy = (y_pred == y_true).sum() / len(y_true)
        
        # ROC-AUC (only if both classes present)
        try:
            roc_auc = roc_auc_score(y_true, y_prob)
        except:
            roc_auc = 0.0
        
        return {
            'accuracy': accuracy,
            'roc_auc': roc_auc,
            'predictions': y_pred,
            'probabilities': y_prob,
            'true_labels': y_true
        }
    
    def train(self, epochs=200, print_every=20):
        """
        Train the model for multiple epochs.
        
        Args:
            epochs (int): Number of training epochs
            print_every (int): Print progress every N epochs
        """
        print("\n" + "="*50)
        print("TRAINING R-GCN FRAUD DETECTOR")
        print("="*50)
        
        best_accuracy = 0.0
        
        for epoch in range(1, epochs + 1):
            loss = self.train_epoch()
            
            if epoch % print_every == 0:
                metrics = self.evaluate()
                
                if metrics['accuracy'] > best_accuracy:
                    best_accuracy = metrics['accuracy']
                    torch.save(self.model.state_dict(), 'models/best_fraud_detector.pt')
                
                print(f"Epoch {epoch:3d} | Loss: {loss:.4f} | "
                      f"Acc: {metrics['accuracy']:.4f} | "
                      f"ROC-AUC: {metrics['roc_auc']:.4f}")
        
        print("\n✓ Training complete!")
        print(f"Best accuracy: {best_accuracy:.4f}")
    
    def generate_report(self, save_path='reports/'):
        """
        Generate detailed evaluation report with visualizations.
        
        Args:
            save_path (str): Directory to save report files
        """
        import os
        os.makedirs(save_path, exist_ok=True)
        
        metrics = self.evaluate()
        
        print("\n" + "="*50)
        print("FRAUD DETECTION REPORT")
        print("="*50)
        
        # Classification report
        print("\nClassification Report:")
        print(classification_report(
            metrics['true_labels'],
            metrics['predictions'],
            target_names=['Normal', 'Fraud']
        ))
        
        # Confusion matrix
        cm = confusion_matrix(metrics['true_labels'], metrics['predictions'])
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['Normal', 'Fraud'],
                    yticklabels=['Normal', 'Fraud'])
        plt.title('Fraud Detection Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(f'{save_path}confusion_matrix.png', dpi=300)
        print(f"\n✓ Confusion matrix saved to {save_path}confusion_matrix.png")
        
        # Save fraud probabilities for agent explainer
        fraud_scores = {
            'node_id': list(range(len(metrics['probabilities']))),
            'fraud_probability': metrics['probabilities'].tolist(),
            'true_label': metrics['true_labels'].tolist(),
            'predicted_label': metrics['predictions'].tolist()
        }
        
        import json
        with open(f'{save_path}fraud_scores.json', 'w') as f:
            json.dump(fraud_scores, f, indent=2)
        
        print(f"✓ Fraud scores saved to {save_path}fraud_scores.json")
        print("\nTop 10 most suspicious users:")
        top_fraud_idx = np.argsort(metrics['probabilities'])[-10:][::-1]
        for rank, idx in enumerate(top_fraud_idx, 1):
            print(f"  {rank}. User {idx}: {metrics['probabilities'][idx]:.4f} "
                  f"(True label: {'FRAUD' if metrics['true_labels'][idx] == 1 else 'Normal'})")


def main():
    """
    Main execution function to train and evaluate the fraud detector.
    """
    print("Starting SentinAL GNN Training...")
    
    # Load data
    print("\nLoading graph data...")
    data = torch.load('data/graph_pyg.pt', weights_only=False)
    print(f"✓ Loaded graph with {data.num_nodes} nodes and {data.num_edges} edges")
    
    # Initialize trainer
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    import os
    os.makedirs('models', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    trainer = FraudDetectorTrainer(data, device=device)
    
    # Train model
    trainer.train(epochs=200, print_every=20)
    
    # Generate report
    trainer.generate_report()
    
    print("\n" + "="*50)
    print("✓ Training and evaluation complete!")
    print("\nNext step:")
    print("  Run 'python agent_explainer.py --user_id <ID>' to get fraud explanations")
    print("="*50)


if __name__ == "__main__":
    main()
