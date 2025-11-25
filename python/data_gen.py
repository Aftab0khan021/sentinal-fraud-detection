"""
SentinAL: Synthetic Financial Graph Generator
==============================================
Module 1 of 3: data_gen.py

This module generates a realistic synthetic financial transaction network
with deliberately injected fraud patterns for training and testing the GNN detector.

Author: [Your Name]
Date: 2025
"""

import networkx as nx
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import torch
from torch_geometric.data import Data
from torch_geometric.utils import from_networkx
import pickle

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)


class FinancialGraphGenerator:
    """
    Generates synthetic financial transaction networks with fraud patterns.
    """
    
    def __init__(self, num_users=100, fraud_ring_size=5):
        """
        Initialize the generator.
        
        Args:
            num_users (int): Total number of user nodes to generate
            fraud_ring_size (int): Size of the fraud ring to inject (4-5 recommended)
        """
        self.num_users = num_users
        self.fraud_ring_size = fraud_ring_size
        self.graph = nx.DiGraph()
        self.transaction_types = ['payment', 'transfer', 'withdrawal']
        
    def generate_user_features(self):
        """
        Generate realistic user node features.
        
        Returns:
            dict: User features including account_age_days and risk_score_initial
        """
        user_features = {}
        
        for user_id in range(self.num_users):
            # Account age in days (between 30 and 1825 days / ~5 years)
            account_age = random.randint(30, 1825)
            
            # Initial risk score (0.0 to 1.0, most users should be low risk)
            # Use beta distribution for realistic skew toward low scores
            risk_score = np.random.beta(2, 5)
            
            user_features[user_id] = {
                'account_age_days': account_age,
                'risk_score_initial': risk_score,
                'is_fraud': 0  # Will be updated for fraud ring members
            }
            
            # Add node to graph
            self.graph.add_node(
                user_id,
                account_age_days=account_age,
                risk_score_initial=risk_score,
                is_fraud=0
            )
        
        return user_features
    
    def inject_fraud_ring(self):
        """
        Inject a cyclic money laundering ring into the graph.
        This creates a circular flow pattern: A -> B -> C -> ... -> A
        
        Returns:
            list: IDs of users in the fraud ring
        """
        # Select random users for the fraud ring
        fraud_users = random.sample(range(self.num_users), self.fraud_ring_size)
        
        print(f"Injecting fraud ring with users: {fraud_users}")
        
        # Mark these users as fraudulent
        for user_id in fraud_users:
            self.graph.nodes[user_id]['is_fraud'] = 1
        
        # Create cyclic transaction pattern
        # Each user sends to the next, and the last sends back to the first
        base_amount = 1000  # Starting amount for laundering
        timestamp = datetime.now()
        
        for i in range(len(fraud_users)):
            from_user = fraud_users[i]
            to_user = fraud_users[(i + 1) % len(fraud_users)]  # Wrap around to create cycle
            
            # Each transaction loses a small amount (realistic layering)
            amount = base_amount * (0.95 ** i)
            
            # Add edge with fraud characteristics
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
        """
        Generate normal (non-fraudulent) transactions between random users.
        
        Args:
            num_transactions (int): Number of normal transactions to generate
        """
        timestamp = datetime.now()
        
        for i in range(num_transactions):
            # Select random users (avoid self-loops)
            from_user = random.randint(0, self.num_users - 1)
            to_user = random.randint(0, self.num_users - 1)
            
            if from_user == to_user:
                continue
            
            # Generate realistic transaction amount (log-normal distribution)
            amount = round(np.random.lognormal(mean=4.5, sigma=1.5), 2)
            amount = max(10, min(amount, 5000))  # Clamp between $10 and $5000
            
            # Random transaction type
            tx_type = random.choice(self.transaction_types)
            
            # Add edge (allow multiple edges between same users)
            self.graph.add_edge(
                from_user,
                to_user,
                amount=amount,
                timestamp=timestamp + timedelta(hours=random.randint(0, 720)),
                transaction_type=tx_type,
                is_fraud_edge=0
            )
    
    def to_pytorch_geometric(self):
        """
        Convert NetworkX graph to PyTorch Geometric Data object.
        
        Returns:
            Data: PyTorch Geometric data object ready for GNN training
        """
        # Extract node features
        node_features = []
        node_labels = []
        
        for node_id in sorted(self.graph.nodes()):
            node = self.graph.nodes[node_id]
            features = [
                node['account_age_days'] / 1825.0,  # Normalize to [0, 1]
                node['risk_score_initial']
            ]
            node_features.append(features)
            node_labels.append(node['is_fraud'])
        
        x = torch.tensor(node_features, dtype=torch.float)
        y = torch.tensor(node_labels, dtype=torch.long)
        
        # Extract edge information
        edge_index = []
        edge_attr = []
        edge_type = []
        
        type_mapping = {tx_type: idx for idx, tx_type in enumerate(self.transaction_types)}
        
        for from_node, to_node, data in self.graph.edges(data=True):
            edge_index.append([from_node, to_node])
            edge_attr.append([
                np.log1p(data['amount']) / 10.0,  # Log-normalize amount
                data['is_fraud_edge']
            ])
            edge_type.append(type_mapping[data['transaction_type']])
        
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.float)
        edge_type = torch.tensor(edge_type, dtype=torch.long)
        
        # Create PyG Data object
        data = Data(
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            edge_type=edge_type,
            y=y
        )
        
        return data
    
    def save(self, nx_path='data/graph.pkl', pyg_path='data/graph_pyg.pt'):
        """
        Save the generated graph in both NetworkX and PyTorch Geometric formats.
        
        Args:
            nx_path (str): Path to save NetworkX graph (pickle)
            pyg_path (str): Path to save PyG Data object (torch)
        """
        import os
        os.makedirs('data', exist_ok=True)
        
        # Save NetworkX graph
        with open(nx_path, 'wb') as f:
            pickle.dump(self.graph, f)
        print(f"NetworkX graph saved to {nx_path}")
        
        # Save PyG data
        pyg_data = self.to_pytorch_geometric()
        torch.save(pyg_data, pyg_path)
        print(f"PyTorch Geometric data saved to {pyg_path}")
        
        # Print summary statistics
        print("\n" + "="*50)
        print("GRAPH GENERATION SUMMARY")
        print("="*50)
        print(f"Total users: {self.graph.number_of_nodes()}")
        print(f"Total transactions: {self.graph.number_of_edges()}")
        print(f"Fraudulent users: {sum(1 for _, data in self.graph.nodes(data=True) if data['is_fraud'] == 1)}")
        print(f"Fraudulent transactions: {sum(1 for _, _, data in self.graph.edges(data=True) if data.get('is_fraud_edge', 0) == 1)}")
        print("="*50)


def main():
    """
    Main execution function to generate and save the synthetic financial graph.
    """
    print("Starting SentinAL Financial Graph Generation...")
    print("="*50)
    
    # Initialize generator
    generator = FinancialGraphGenerator(
        num_users=100,
        fraud_ring_size=5
    )
    
    # Generate user features
    print("\n[1/4] Generating user nodes with features...")
    generator.generate_user_features()
    
    # Inject fraud ring
    print("\n[2/4] Injecting fraud ring pattern...")
    fraud_users = generator.inject_fraud_ring()
    
    # Generate normal transactions
    print("\n[3/4] Generating normal transactions...")
    generator.generate_normal_transactions(num_transactions=300)
    
    # Save outputs
    print("\n[4/4] Saving graph data...")
    generator.save()
    
    print("\n✓ Graph generation complete!")
    print("\nNext steps:")
    print("  1. Run 'python gnn_train.py' to train the fraud detector")
    print("  2. Run 'python agent_explainer.py' to query fraud explanations")


if __name__ == "__main__":
    main()
