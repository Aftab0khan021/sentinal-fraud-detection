"""
Generate sample graph data for SentinAL demo
"""
import pickle
import numpy as np
import networkx as nx

# Create a simple directed graph with 100 nodes
G = nx.DiGraph()

# Add nodes with fraud scores
for i in range(100):
    fraud_score = np.random.random()
    G.add_node(i, fraud_score=fraud_score)

# Add random edges (transactions)
for _ in range(200):
    src = np.random.randint(0, 100)
    dst = np.random.randint(0, 100)
    if src != dst:
        amount = np.random.uniform(10, 10000)
        G.add_edge(src, dst, amount=amount)

# Create fraud scores array
fraud_scores = np.array([G.nodes[i]["fraud_score"] for i in range(100)])

# Save data
data = {"graph": G, "fraud_scores": fraud_scores}

with open("data/graph_enhanced.pkl", "wb") as f:
    pickle.dump(data, f)

print("✓ Sample graph data generated successfully!")
print(f"  Nodes: {G.number_of_nodes()}")
print(f"  Edges: {G.number_of_edges()}")
print(f"  Saved to: data/graph_enhanced.pkl")
