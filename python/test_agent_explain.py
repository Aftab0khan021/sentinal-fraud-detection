"""
Test agent.explain() method directly
"""
import pickle
from agent_explainer import FraudExplainerAgent

# Load graph data
with open('data/graph_enhanced.pkl', 'rb') as f:
    data = pickle.load(f)

graph = data['graph']
fraud_scores = data['fraud_scores']

print("Initializing agent...")
agent = FraudExplainerAgent(graph=graph, fraud_scores=fraud_scores)
print("✓ Agent initialized")

print("\nTesting explain method...")
try:
    explanation = agent.explain(58)
    print(f"✓ Explanation generated!")
    print(f"\nExplanation:\n{explanation}")
except Exception as e:
    print(f"✗ Explanation failed: {e}")
    import traceback
    traceback.print_exc()
