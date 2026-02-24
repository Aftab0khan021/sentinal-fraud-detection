"""
Quick script to check the structure of graph_enhanced.pkl
"""
import pickle

with open("data/graph_enhanced.pkl", "rb") as f:
    data = pickle.load(f)

print("Data structure:")
print(f"Type: {type(data)}")
print(f"Keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")

if isinstance(data, dict):
    for key, value in data.items():
        print(f"\n{key}:")
        print(f"  Type: {type(value)}")
        if hasattr(value, "shape"):
            print(f"  Shape: {value.shape}")
        elif hasattr(value, "__len__"):
            print(f"  Length: {len(value)}")
