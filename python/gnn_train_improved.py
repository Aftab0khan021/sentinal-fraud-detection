"""
SentinAL: Improved GNN Fraud Detector
======================================
Enhanced version with train/val/test split, early stopping, and better evaluation.

Improvements:
- Proper data splitting (60% train, 20% val, 20% test)
- Early stopping to prevent overfitting
- Learning rate scheduling
- Better evaluation metrics
- Model checkpointing

Author: SentinAL Team
Date: 2026-01-23
"""

import torch
import torch.nn.functional as F
from torch_geometric.nn import RGCNConv
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json


class ImprovedFraudRGCN(torch.nn.Module):
    """Enhanced R-GCN with better architecture"""
    
    def __init__(self, num_features, hidden_channels, num_relations, num_classes=2, dropout=0.3):
        super(ImprovedFraudRGCN, self).__init__()
        
        self.conv1 = RGCNConv(num_features, hidden_channels, num_relations=num_relations)
        self.conv2 = RGCNConv(hidden_channels, hidden_channels, num_relations=num_relations)
        self.lin = torch.nn.Linear(hidden_channels, num_classes)
        self.dropout = torch.nn.Dropout(p=dropout)
    
    def forward(self, x, edge_index, edge_type):
        x = self.conv1(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.conv2(x, edge_index, edge_type)
        x = F.relu(x)
        x = self.dropout(x)
        
        x = self.lin(x)
        return F.log_softmax(x, dim=1)


class ImprovedFraudDetectorTrainer:
    """Enhanced trainer with proper train/val/test split"""
    
    def __init__(self, data, device='cpu', train_ratio=0.6, val_ratio=0.2):
        """
        Initialize trainer with data splitting.
        
        Args:
            data: PyG Data object
            device: 'cpu' or 'cuda'
            train_ratio: Proportion for training (default 60%)
            val_ratio: Proportion for validation (default 20%)
            test_ratio: Remaining 20% for testing
        """
        self.data = data.to(device)
        self.device = device
        
        # Create train/val/test masks
        num_nodes = data.num_nodes
        indices = torch.randperm(num_nodes)
        
        train_size = int(num_nodes * train_ratio)
        val_size = int(num_nodes * val_ratio)
        
        self.data.train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        self.data.val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        self.data.test_mask = torch.zeros(num_nodes, dtype=torch.bool)
        
        self.data.train_mask[indices[:train_size]] = True
        self.data.val_mask[indices[train_size:train_size+val_size]] = True
        self.data.test_mask[indices[train_size+val_size:]] = True
        
        print(f"\n📊 Data Split:")
        print(f"  Train: {self.data.train_mask.sum()} nodes ({train_ratio*100:.0f}%)")
        print(f"  Val:   {self.data.val_mask.sum()} nodes ({val_ratio*100:.0f}%)")
        print(f"  Test:  {self.data.test_mask.sum()} nodes ({(1-train_ratio-val_ratio)*100:.0f}%)")
        
        # Calculate class weights only on training data
        self.class_weights = self._calculate_class_weights()
        
        # Initialize model
        self.model = ImprovedFraudRGCN(
            num_features=data.x.size(1),
            hidden_channels=64,
            num_relations=3,
            num_classes=2
        ).to(device)
        
        # Optimizer with weight decay
        self.optimizer = torch.optim.Adam(
            self.model.parameters(),
            lr=0.01,
            weight_decay=5e-4
        )
        
        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='max',
            factor=0.5,
            patience=10
        )
        
        # Loss function with class weights
        self.criterion = torch.nn.NLLLoss(weight=self.class_weights)
        
        # Early stopping
        self.best_val_acc = 0.0
        self.patience_counter = 0
        self.best_model_state = None
    
    def _calculate_class_weights(self):
        """Calculate class weights based on training set only"""
        y_train = self.data.y[self.data.train_mask].cpu().numpy()
        class_counts = np.bincount(y_train)
        class_weights = 1.0 / class_counts
        class_weights = class_weights / class_weights.sum() * len(class_counts)
        
        print(f"\n⚖️  Training Set Class Distribution:")
        print(f"  Normal: {class_counts[0]} ({class_counts[0]/len(y_train)*100:.1f}%)")
        print(f"  Fraud:  {class_counts[1]} ({class_counts[1]/len(y_train)*100:.1f}%)")
        print(f"  Class Weights: Normal={class_weights[0]:.2f}, Fraud={class_weights[1]:.2f}")
        
        return torch.tensor(class_weights, dtype=torch.float).to(self.device)
    
    def train_epoch(self):
        """Train for one epoch on training set only"""
        self.model.train()
        self.optimizer.zero_grad()
        
        out = self.model(self.data.x, self.data.edge_index, self.data.edge_type)
        loss = self.criterion(out[self.data.train_mask], self.data.y[self.data.train_mask])
        
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    @torch.no_grad()
    def evaluate(self, mask_name='val'):
        """Evaluate on specific split"""
        self.model.eval()
        
        if mask_name == 'train':
            mask = self.data.train_mask
        elif mask_name == 'val':
            mask = self.data.val_mask
        else:  # test
            mask = self.data.test_mask
        
        out = self.model(self.data.x, self.data.edge_index, self.data.edge_type)
        pred = out.argmax(dim=1)
        prob = torch.exp(out[:, 1])
        
        y_true = self.data.y[mask].cpu().numpy()
        y_pred = pred[mask].cpu().numpy()
        y_prob = prob[mask].cpu().numpy()
        
        accuracy = (y_pred == y_true).sum() / len(y_true)
        
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
    
    def train(self, epochs=200, print_every=20, patience=20):
        """Train with early stopping"""
        print("\n" + "="*50)
        print("🚀 TRAINING IMPROVED R-GCN FRAUD DETECTOR")
        print("="*50)
        
        for epoch in range(1, epochs + 1):
            loss = self.train_epoch()
            
            if epoch % print_every == 0:
                train_metrics = self.evaluate('train')
                val_metrics = self.evaluate('val')
                
                print(f"Epoch {epoch:3d} | Loss: {loss:.4f} | "
                      f"Train Acc: {train_metrics['accuracy']:.4f} | "
                      f"Val Acc: {val_metrics['accuracy']:.4f} | "
                      f"Val AUC: {val_metrics['roc_auc']:.4f}")
                
                # Learning rate scheduling
                self.scheduler.step(val_metrics['accuracy'])
                
                # Early stopping
                if val_metrics['accuracy'] > self.best_val_acc:
                    self.best_val_acc = val_metrics['accuracy']
                    self.patience_counter = 0
                    self.best_model_state = self.model.state_dict().copy()
                    torch.save(self.model.state_dict(), 'models/best_fraud_detector_improved.pt')
                    print(f"  → ✓ New best model saved (Val Acc: {self.best_val_acc:.4f})")
                else:
                    self.patience_counter += 1
                
                if self.patience_counter >= patience:
                    print(f"\n⏹️  Early stopping at epoch {epoch}")
                    break
        
        # Load best model
        print("\n" + "="*50)
        print("📊 FINAL TEST SET EVALUATION")
        print("="*50)
        
        self.model.load_state_dict(torch.load('models/best_fraud_detector_improved.pt'))
        test_metrics = self.evaluate('test')
        
        print(f"\n✅ Test Results:")
        print(f"  Accuracy: {test_metrics['accuracy']:.4f}")
        print(f"  ROC-AUC:  {test_metrics['roc_auc']:.4f}")
        
        return test_metrics


def main():
    """Main training function"""
    print("\n🎯 Starting Improved SentinAL GNN Training...")
    
    # Load data
    print("\n📂 Loading graph data...")
    data = torch.load('data/graph_pyg.pt', weights_only=False)
    print(f"✓ Loaded graph with {data.num_nodes} nodes and {data.num_edges} edges")
    
    # Train model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"🖥️  Using device: {device}")
    
    trainer = ImprovedFraudDetectorTrainer(data, device=device)
    test_metrics = trainer.train(epochs=200, print_every=20, patience=20)
    
    # Save results
    print("\n💾 Saving results...")
    
    # Generate predictions for all nodes
    trainer.model.eval()
    with torch.no_grad():
        out = trainer.model(data.x, data.edge_index, data.edge_type)
        prob = torch.exp(out[:, 1]).cpu().numpy()
        pred = out.argmax(dim=1).cpu().numpy()
    
    results = {
        'fraud_probability': prob.tolist(),
        'predicted_label': pred.tolist(),
        'true_label': data.y.cpu().numpy().tolist(),
        'test_accuracy': float(test_metrics['accuracy']),
        'test_roc_auc': float(test_metrics['roc_auc']),
        'model_type': 'Improved R-GCN with train/val/test split'
    }
    
    with open('reports/fraud_scores_improved.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✓ Results saved to reports/fraud_scores_improved.json")
    print("\n" + "="*50)
    print("✅ IMPROVED MODEL TRAINING COMPLETE!")
    print("="*50)


if __name__ == "__main__":
    main()
