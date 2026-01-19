"""
SentinAL: Synthetic Financial Graph Generator
==============================================
Module 1 of 3: data_gen.py

This module generates a realistic synthetic financial transaction network
with deliberately injected fraud patterns for training and testing the GNN detector.

Author: SentinAL Project
Date: 2025
"""

import networkx as nx
import numpy as np
from datetime import datetime, timedelta
import random
import torch
from torch_geometric.data import Data
import pickle
import os

# Set random seeds for reproducibility
# CRITICAL: Keep these seeds fixed so "User 77" is always the fraudster
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)

class FinancialGraphGenerator:
    """
    Generates synthetic financial transaction networks with fraud patterns.
    """
    
    def __init__(self, num_users=100, fraud_ring_size=5):
        self.num_users = num_users
        self.fraud_ring_size = fraud_ring_size
        self.graph = nx.DiGraph()
        self.transaction_types = ['payment', 'transfer', 'withdrawal']
        
    def generate_user_features(self):
        """Generate realistic user node features."""
        user_features = {}
        
        for user_id in range(self.num_users):
            # Account age in days (between 30 and 1825 days / ~5 years)
            account_age = random.randint(30, 1825)
            
            # Initial risk score (beta distribution for realistic skew)
            risk_score = np.random.beta(2, 5)
            
            self.graph.add_node(
                user_id,
                account_age_days=account_age,
                risk_score_initial=risk_score,
                is_fraud=0
            )
        
    def inject_fraud_ring(self):
        """Inject a cyclic money laundering ring."""
        fraud_users = random.sample(range(self.num_users), self.fraud_ring_size)
        print(f"Injecting fraud ring with users: {fraud_users}")
        
        # Mark users as fraudulent
        for user_id in fraud_users:
            self.graph.nodes[user_id]['is_fraud'] = 1
        
        # Create cyclic transaction pattern: A -> B -> C -> ... -> A
        base_amount = 1000
        timestamp = datetime.now()
        
        for i in range(len(fraud_users)):
            from_user = fraud_users[i]
            to_user = fraud_users[(i + 1) % len(fraud_users)]
            
            amount = base_amount * (0.95 ** i)
            
            self.graph.add_edge(
                from_user,
                to_user,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(hours=i),
                transaction_type='transfer',
                is_fraud_edge=1
            )
        return fraud_users
    
    def generate_normal_transactions(self, num_transactions=300):
        """Generate normal (non-fraudulent) transactions."""
        timestamp = datetime.now()
        
        for i in range(num_transactions):
            from_user = random.randint(0, self.num_users - 1)
            to_user = random.randint(0, self.num_users - 1)
            
            if from_user == to_user:
                continue
            
            amount = round(np.random.lognormal(mean=4.5, sigma=1.5), 2)
            amount = max(10, min(amount, 5000))
            tx_type = random.choice(self.transaction_types)
            
            self.graph.add_edge(
                from_user,
                to_user,
                amount=amount,
                timestamp=timestamp + timedelta(hours=random.randint(0, 720)),
                transaction_type=tx_type,
                is_fraud_edge=0
            )
    
    def to_pytorch_geometric(self):
        """Convert NetworkX graph to PyTorch Geometric Data object."""
        # 1. Node Features
        node_features = []
        node_labels = []
        
        for node_id in sorted(self.graph.nodes()):
            node = self.graph.nodes[node_id]
            features = [
                node['account_age_days'] / 1825.0,
                node['risk_score_initial']
            ]
            node_features.append(features)
            node_labels.append(node['is_fraud'])
        
        x = torch.tensor(node_features, dtype=torch.float)
        y = torch.tensor(node_labels, dtype=torch.long)
        
        # 2. Edge Features
        edge_index = []
        edge_attr = []
        edge_type = []
        
        type_mapping = {tx: i for i, tx in enumerate(self.transaction_types)}
        
        for u, v, data in self.graph.edges(data=True):
            edge_index.append([u, v])
            
            # FIXED: Removed 'is_fraud_edge' to prevent Data Leakage
            # Only providing the normalized amount to the model
            edge_attr.append([
                np.log1p(data['amount']) / 10.0
            ])
            
            edge_type.append(type_mapping[data['transaction_type']])
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.float)
        edge_type = torch.tensor(edge_type, dtype=torch.long)
        
        return Data(x=x, edge_index=edge_index, edge_attr=edge_attr, edge_type=edge_type, y=y)
    
    def save(self, nx_path='data/graph.pkl', pyg_path='data/graph_pyg.pt'):
        os.makedirs('data', exist_ok=True)
        
        with open(nx_path, 'wb') as f:
            pickle.dump(self.graph, f)
        print(f"NetworkX graph saved to {nx_path}")
        
        pyg_data = self.to_pytorch_geometric()
        torch.save(pyg_data, pyg_path)
        print(f"PyTorch Geometric data saved to {pyg_path}")
        
        print("\n" + "="*50)
        print("GRAPH GENERATION SUMMARY")
        print("="*50)
        print(f"Total users: {self.graph.number_of_nodes()}")
        print(f"Total transactions: {self.graph.number_of_edges()}")
        print(f"Fraudulent users: {sum(1 for _, d in self.graph.nodes(data=True) if d['is_fraud'] == 1)}")
        print("="*50)

def main():
    print("Starting SentinAL Financial Graph Generation...")
    generator = FinancialGraphGenerator(num_users=100, fraud_ring_size=5)
    
    print("\n[1/4] Generating user nodes...")
    generator.generate_user_features()
    
    print("\n[2/4] Injecting fraud ring...")
    generator.inject_fraud_ring()
    
    print("\n[3/4] Generating transactions...")
    generator.generate_normal_transactions()
    
    print("\n[4/4] Saving data...")
    generator.save()
    print("\n✓ Data generation complete!")

if __name__ == "__main__":
    main()