"""
SentinAL: Enhanced Synthetic Financial Graph Generator
======================================================
Module 1 (Enhanced): data_gen_enhanced.py

Generates realistic financial transaction networks with MULTIPLE fraud patterns:
1. Cyclic Ring (original) - Money laundering
2. Fan-Out - Layering/distribution
3. Rapid-Fire - Automated bot attacks
4. Scatter-Gather - Smurfing/structuring

Author: SentinAL Project  
Date: 2026-01-23
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
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)


class EnhancedFinancialGraphGenerator:
    """
    Generates synthetic financial transaction networks with multiple fraud patterns.
    """
    
    def __init__(self, num_users=100):
        self.num_users = num_users
        self.graph = nx.DiGraph()
        self.transaction_types = ['payment', 'transfer', 'withdrawal']
        self.fraud_users = set()
        
    def generate_user_features(self):
        """Generate realistic user node features."""
        for user_id in range(self.num_users):
            account_age = random.randint(30, 1825)
            risk_score = np.random.beta(2, 5)
            
            self.graph.add_node(
                user_id,
                account_age_days=account_age,
                risk_score_initial=risk_score,
                is_fraud=0,
                fraud_pattern=None
            )
    
    def inject_cyclic_ring(self, ring_size=5):
        """
        Pattern 1: Cyclic Money Laundering Ring
        A → B → C → D → A (circular flow to obscure origin)
        """
        available_users = [u for u in range(self.num_users) if u not in self.fraud_users]
        if len(available_users) < ring_size:
            print(f"⚠️  Not enough users for cyclic ring")
            return []
        
        fraud_users = random.sample(available_users, ring_size)
        print(f"💍 Cyclic Ring: {fraud_users}")
        
        # Mark users as fraudulent
        for user_id in fraud_users:
            self.graph.nodes[user_id]['is_fraud'] = 1
            self.graph.nodes[user_id]['fraud_pattern'] = 'cyclic_ring'
            self.fraud_users.add(user_id)
        
        # Create cycle
        base_amount = 1000
        timestamp = datetime.now()
        
        for i in range(len(fraud_users)):
            from_user = fraud_users[i]
            to_user = fraud_users[(i + 1) % len(fraud_users)]
            amount = base_amount * (0.95 ** i)
            
            self.graph.add_edge(
                from_user, to_user,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(hours=i),
                transaction_type='transfer',
                is_fraud_edge=1,
                pattern='cyclic_ring'
            )
        
        return fraud_users
    
    def inject_fanout_pattern(self, source_user=None, num_targets=10):
        """
        Pattern 2: Fan-Out (Layering)
        One source → Many destinations (money laundering layering phase)
        """
        available_users = [u for u in range(self.num_users) if u not in self.fraud_users]
        if len(available_users) < num_targets + 1:
            print(f"⚠️  Not enough users for fan-out")
            return []
        
        if source_user is None:
            source_user = random.choice(available_users)
            available_users.remove(source_user)
        
        targets = random.sample(available_users, num_targets)
        
        print(f"📤 Fan-Out: {source_user} → {targets}")
        
        # Mark source as fraud
        self.graph.nodes[source_user]['is_fraud'] = 1
        self.graph.nodes[source_user]['fraud_pattern'] = 'fanout_source'
        self.fraud_users.add(source_user)
        
        # Create fan-out edges
        timestamp = datetime.now()
        base_amount = 5000
        
        for i, target in enumerate(targets):
            amount = base_amount / num_targets  # Split money
            
            self.graph.add_edge(
                source_user, target,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(minutes=i*5),
                transaction_type='transfer',
                is_fraud_edge=1,
                pattern='fanout'
            )
        
        return [source_user] + targets
    
    def inject_rapidfire_pattern(self, user_id=None, num_transactions=20):
        """
        Pattern 3: Rapid-Fire (Automated Bot Attack)
        Many transactions in very short time window
        """
        available_users = [u for u in range(self.num_users) if u not in self.fraud_users]
        if len(available_users) < 2:
            print(f"⚠️  Not enough users for rapid-fire")
            return []
        
        if user_id is None:
            user_id = random.choice(available_users)
        
        print(f"⚡ Rapid-Fire: User {user_id} ({num_transactions} txns)")
        
        # Mark as fraud
        self.graph.nodes[user_id]['is_fraud'] = 1
        self.graph.nodes[user_id]['fraud_pattern'] = 'rapidfire'
        self.fraud_users.add(user_id)
        
        # Create rapid transactions
        timestamp = datetime.now()
        
        for i in range(num_transactions):
            target = random.choice([u for u in range(self.num_users) if u != user_id])
            amount = random.uniform(50, 200)
            
            self.graph.add_edge(
                user_id, target,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(seconds=i*3),  # 3 seconds apart!
                transaction_type='payment',
                is_fraud_edge=1,
                pattern='rapidfire'
            )
        
        return [user_id]
    
    def inject_scatter_gather_pattern(self, hub_user=None, num_sources=5, num_targets=5):
        """
        Pattern 4: Scatter-Gather (Smurfing/Structuring)
        Many sources → Hub → Many targets (break up large amounts)
        """
        available_users = [u for u in range(self.num_users) if u not in self.fraud_users]
        if len(available_users) < num_sources + num_targets + 1:
            print(f"⚠️  Not enough users for scatter-gather")
            return []
        
        if hub_user is None:
            hub_user = random.choice(available_users)
            available_users.remove(hub_user)
        
        sources = random.sample(available_users, num_sources)
        for s in sources:
            available_users.remove(s)
        targets = random.sample(available_users, num_targets)
        
        print(f"🔄 Scatter-Gather: {sources} → {hub_user} → {targets}")
        
        # Mark hub as fraud
        self.graph.nodes[hub_user]['is_fraud'] = 1
        self.graph.nodes[hub_user]['fraud_pattern'] = 'scatter_gather_hub'
        self.fraud_users.add(hub_user)
        
        timestamp = datetime.now()
        
        # Gather phase: sources → hub
        for i, source in enumerate(sources):
            amount = random.uniform(800, 1200)
            self.graph.add_edge(
                source, hub_user,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(hours=i),
                transaction_type='transfer',
                is_fraud_edge=1,
                pattern='scatter_gather_in'
            )
        
        # Scatter phase: hub → targets
        for i, target in enumerate(targets):
            amount = random.uniform(900, 1100)
            self.graph.add_edge(
                hub_user, target,
                amount=round(amount, 2),
                timestamp=timestamp + timedelta(hours=num_sources + i),
                transaction_type='transfer',
                is_fraud_edge=1,
                pattern='scatter_gather_out'
            )
        
        return sources + [hub_user] + targets
    
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
                from_user, to_user,
                amount=amount,
                timestamp=timestamp + timedelta(hours=random.randint(0, 720)),
                transaction_type=tx_type,
                is_fraud_edge=0,
                pattern='normal'
            )
    
    def to_pytorch_geometric(self):
        """Convert NetworkX graph to PyTorch Geometric format."""
        # Node features
        node_features = []
        node_labels = []
        
        for node_id in range(self.num_users):
            node_data = self.graph.nodes[node_id]
            account_age_norm = node_data['account_age_days'] / 1825.0
            risk_score = node_data['risk_score_initial']
            node_features.append([account_age_norm, risk_score])
            node_labels.append(node_data['is_fraud'])
        
        x = torch.tensor(node_features, dtype=torch.float)
        y = torch.tensor(node_labels, dtype=torch.long)
        
        # Edge features
        edge_list = []
        edge_types = []
        edge_attrs = []
        
        type_to_int = {t: i for i, t in enumerate(self.transaction_types)}
        
        for from_node, to_node, edge_data in self.graph.edges(data=True):
            edge_list.append([from_node, to_node])
            edge_type = type_to_int[edge_data['transaction_type']]
            edge_types.append(edge_type)
            edge_attrs.append([edge_data['amount'] / 5000.0])
        
        edge_index = torch.tensor(edge_list, dtype=torch.long).t().contiguous()
        edge_type = torch.tensor(edge_types, dtype=torch.long)
        edge_attr = torch.tensor(edge_attrs, dtype=torch.float)
        
        data = Data(
            x=x,
            edge_index=edge_index,
            edge_type=edge_type,
            edge_attr=edge_attr,
            y=y
        )
        
        return data


def main():
    """Generate enhanced fraud detection dataset."""
    print("\n" + "="*70)
    print("🚀 ENHANCED SENTINAL FINANCIAL GRAPH GENERATION")
    print("="*70)
    
    generator = EnhancedFinancialGraphGenerator(num_users=100)
    
    print("\n[1/6] Generating user nodes...")
    generator.generate_user_features()
    
    print("\n[2/6] Injecting fraud patterns...")
    
    # Pattern 1: Cyclic ring (5 users)
    generator.inject_cyclic_ring(ring_size=5)
    
    # Pattern 2: Fan-out (1 source, 8 targets)
    generator.inject_fanout_pattern(num_targets=8)
    
    # Pattern 3: Rapid-fire (1 user, 15 transactions)
    generator.inject_rapidfire_pattern(num_transactions=15)
    
    # Pattern 4: Scatter-gather (4 sources, hub, 4 targets)
    generator.inject_scatter_gather_pattern(num_sources=4, num_targets=4)
    
    print(f"\n[3/6] Generating normal transactions...")
    generator.generate_normal_transactions(num_transactions=300)
    
    print(f"\n[4/6] Converting to PyTorch Geometric format...")
    pyg_data = generator.to_pytorch_geometric()
    
    print(f"\n[5/6] Saving data...")
    os.makedirs('data', exist_ok=True)
    
    with open('data/graph_enhanced.pkl', 'wb') as f:
        pickle.dump(generator.graph, f)
    print("✓ NetworkX graph saved to data/graph_enhanced.pkl")
    
    torch.save(pyg_data, 'data/graph_pyg_enhanced.pt')
    print("✓ PyTorch Geometric data saved to data/graph_pyg_enhanced.pt")
    
    print(f"\n[6/6] Summary...")
    print("\n" + "="*70)
    print("ENHANCED GRAPH GENERATION SUMMARY")
    print("="*70)
    print(f"Total users: {generator.num_users}")
    print(f"Total transactions: {generator.graph.number_of_edges()}")
    print(f"Fraudulent users: {len(generator.fraud_users)}")
    print(f"\nFraud Patterns Injected:")
    print(f"  💍 Cyclic Ring: 5 users")
    print(f"  📤 Fan-Out: 9 users (1 source + 8 targets)")
    print(f"  ⚡ Rapid-Fire: 1 user")
    print(f"  🔄 Scatter-Gather: 9 users (4 sources + hub + 4 targets)")
    print(f"\nTotal fraud-involved users: {len(generator.fraud_users)}")
    print("="*70)
    print("\n✅ Enhanced data generation complete!\n")


if __name__ == "__main__":
    main()
