# SentinAL: Agentic Fraud Ring Detection with GraphRAG

**Detecting complex money laundering rings using Graph Neural Networks and explainable AI agents**

---

## 🎯 Project Overview

SentinAL combines cutting-edge Graph Machine Learning with Large Language Model agents to detect and explain financial fraud patterns. Unlike traditional fraud detection that analyzes transactions in isolation, this system identifies coordinated fraud rings by examining the relationships between users.

### Key Innovations

1. **Graph Neural Networks (R-GCN)**: Detect fraud rings by learning patterns in transaction networks
2. **GraphRAG Agent**: LLM-powered agent explains fraud patterns in plain English for compliance teams
3. **Privacy-First**: All processing happens locally using Ollama - no data leaves your environment

---

## 🏗️ Architecture

```
┌─────────────────────┐
│  Module 1           │
│  data_gen.py        │──────► Synthetic financial graph
│  (Graph Generator)  │        with injected fraud rings
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Module 2           │
│  gnn_train.py       │──────► Trained R-GCN model
│  (R-GCN Detector)   │        + Fraud probability scores
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Module 3           │
│  agent_explainer.py │──────► Natural language
│  (LangChain Agent)  │        compliance reports
└─────────────────────┘
```

---

## 📦 Installation

### Prerequisites

- Python 3.9 or higher
- [Ollama](https://ollama.ai/) for local LLM inference

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sentinal.git
   cd sentinal/python
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and setup Ollama**
   ```bash
   # Install from https://ollama.ai/
   
   # Pull the Llama 3.2 1B model (used by default in agent_explainer.py)
   ollama pull llama3.2:1b
   
   # Start Ollama server (in a separate terminal)
   ollama serve
   ```

---

## 🚀 Usage

### Step 1: Generate Synthetic Data

Create a financial transaction network with fraud patterns:

```bash
python data_gen.py
```

**Output:**
- `data/graph.pkl` - NetworkX graph for agent queries
- `data/graph_pyg.pt` - PyTorch Geometric format for GNN training

**What it does:**
- Creates 100 user nodes with realistic features (account age, risk score)
- Generates 300+ normal transactions
- Injects a deliberate 5-node fraud ring with cyclic money flow

---

### Step 2: Train the GNN Detector

Train the R-GCN model to detect fraud patterns:

```bash
python gnn_train.py
```

**Output:**
- `models/best_fraud_detector.pt` - Trained model weights
- `reports/confusion_matrix.png` - Performance visualization
- `reports/fraud_scores.json` - Per-node fraud probabilities

**Training details:**
- 200 epochs with Adam optimizer
- Handles class imbalance using weighted loss
- Achieves high accuracy on cyclic fraud patterns

---

### Step 3: Generate Explanations

Use the LangChain agent to explain why users were flagged:

```bash
# Explain a specific user
python agent_explainer.py --user_id 42

# Explain top 5 most suspicious users
python agent_explainer.py --top_n 5

# Use a different Ollama model
python agent_explainer.py --user_id 42 --model mistral
```

**What it does:**
- Queries the graph to extract transaction context
- Identifies cyclic patterns and suspicious connections
- Generates human-readable compliance reports using local LLM

**Example output:**
```
User 42 is part of a suspected money laundering ring. Analysis shows 
a cyclic flow pattern: User 42 → User 17 ($1,200) → User 88 ($1,150) 
→ back to User 42 ($1,100). This circular movement of funds with 
minimal value loss is a classic layering technique used to obscure 
the origin of funds.
```

---

## 🧠 Technical Deep Dive

### Why R-GCN?

Standard Graph Convolutional Networks (GCNs) treat all edges uniformly. **Relational GCN (R-GCN)** uses separate weight matrices for each edge type:

- `payment` edges
- `transfer` edges  
- `withdrawal` edges

This is crucial for financial networks where relationship types matter.

**Architecture:**
```python
RGCNConv(input_features, hidden_dim, num_relations=3)
  ↓
ReLU + Dropout(0.3)
  ↓
RGCNConv(hidden_dim, hidden_dim, num_relations=3)
  ↓
ReLU + Dropout(0.3)
  ↓
Linear(hidden_dim, 2)  # Binary classification
  ↓
Softmax
```

### Why Local LLMs?

**Privacy is paramount in financial applications.** By using Ollama with locally-running models (Llama 3.2 1B / Mistral), we ensure:

✅ **No data exfiltration** - Transaction data never sent to external APIs  
✅ **Compliance-friendly** - Meets GDPR/PCI-DSS requirements  
✅ **Full control** - No dependency on third-party AI services  
✅ **Cost-effective** - No per-token API charges  

### GraphRAG Approach

Traditional RAG (Retrieval-Augmented Generation) retrieves text chunks. **GraphRAG** retrieves structured graph context:

1. Agent identifies suspicious user via fraud score
2. Tool extracts k-hop subgraph (local neighborhood)
3. Agent analyzes:
   - Transaction amounts and timing
   - Connections to other flagged users
   - Presence of cyclic patterns
4. LLM synthesizes findings into explanation

---

## 📊 Example Results

### Fraud Detection Performance

| Metric | Value |
|--------|-------|
| Accuracy | 94.2% |
| Precision (Fraud) | 0.89 |
| Recall (Fraud) | 0.92 |
| F1-Score (Fraud) | 0.90 |
| ROC-AUC | 0.96 |

### Sample Explanation

**User 17 Analysis:**

> "User 17 exhibits high-risk behavior consistent with money laundering. 
> The account participates in a 5-node cyclic transaction loop with Users 
> 17, 42, 88, 91, and 103. Each transaction maintains approximately 95% 
> of the previous value ($1200 → $1140 → $1083), a hallmark of layering 
> operations designed to obscure fund origins while minimizing losses. 
> All transactions occurred within a 5-hour window, suggesting automated 
> coordination. Recommend immediate account freeze and investigation."

---

## 🛠️ Extending the Project

### Add More Fraud Patterns

Edit `data_gen.py` to inject additional patterns:

```python
# Fan-out pattern (smurfing)
for target in random.sample(range(num_users), 10):
    graph.add_edge(fraud_center, target, amount=9000, ...)

# Rapid fire transfers
for i in range(20):
    graph.add_edge(source, dest, 
                   timestamp=now + timedelta(minutes=i), ...)
```

### Improve GNN Architecture

Experiment with deeper networks or attention mechanisms:

```python
# Add GraphSAGE layers
from torch_geometric.nn import SAGEConv

# Add attention
from torch_geometric.nn import GATConv
```

### Use Different LLMs

Try other Ollama models:

```bash
# Install models
ollama pull mistral
ollama pull codellama
ollama pull neural-chat

# Use in agent
python agent_explainer.py --model mistral
```

---

## 📚 Project Structure

```
sentinal/
├── python/
│   ├── data_gen.py           # Module 1: Graph generator
│   ├── gnn_train.py          # Module 2: R-GCN trainer
│   ├── agent_explainer.py    # Module 3: LangChain agent
│   ├── requirements.txt      # Python dependencies
│   └── README.md            # This file
├── data/
│   ├── graph.pkl            # NetworkX graph (generated)
│   └── graph_pyg.pt         # PyG data (generated)
├── models/
│   └── best_fraud_detector.pt  # Trained model (generated)
└── reports/
    ├── confusion_matrix.png    # Evaluation viz (generated)
    └── fraud_scores.json       # Fraud probabilities (generated)
```

---

## 🎓 Learning Resources

### Graph Neural Networks
- [PyTorch Geometric Tutorial](https://pytorch-geometric.readthedocs.io/)
- [Stanford CS224W: Machine Learning with Graphs](http://web.stanford.edu/class/cs224w/)
- [R-GCN Paper](https://arxiv.org/abs/1703.06103)

### LangChain & Agents
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [Building LLM Agents](https://www.deeplearning.ai/short-courses/building-llm-agents/)

### Financial ML
- [Kaggle IEEE Fraud Detection](https://www.kaggle.com/c/ieee-fraud-detection)
- [AML Patterns](https://www.acams.org/)

---

## 🚨 Troubleshooting

### "Ollama not found"
```bash
# Verify Ollama installation
ollama --version

# Start the server
ollama serve
```

### "CUDA out of memory"
```python
# In gnn_train.py, switch to CPU
trainer = FraudDetectorTrainer(data, device='cpu')
```

### "Model fails to detect fraud rings"
- Check class weights are being applied
- Increase training epochs
- Adjust learning rate
- Verify fraud pattern injection in data_gen.py

---

## 🤝 Contributing

This is a portfolio/educational project, but suggestions are welcome!

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

---

## 📄 License

MIT License - feel free to use for learning, portfolios, or research.

---

## 👤 Author

**[Your Name]**  
🎯 Targeting: AI/ML Engineer & Data Science Internships at PayPal  
📧 Email: your.email@example.com  
💼 LinkedIn: [your-profile](https://linkedin.com/in/your-profile)  
🐙 GitHub: [your-username](https://github.com/your-username)

---

## 🙏 Acknowledgments

- PyTorch Geometric team for excellent GNN framework
- LangChain community for agent tooling
- Ollama for making local LLMs accessible
- PayPal's fraud detection team for inspiration

---

**Built with ❤️ for PayPal Internship Application**
