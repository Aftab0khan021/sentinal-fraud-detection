# 🛡️ SentinAL: Agentic Fraud Detection with GraphRAG

**SentinAL** is a privacy-first fraud detection system that combines **Graph Neural Networks (GNNs)** with **Local Generative AI** to identify and explain complex money laundering rings.

Unlike standard "black box" models that only output a probability score, SentinAL uses an **AI Agent** to analyze transaction topology and generate human-readable compliance reports—all without sending sensitive financial data to the cloud.

---

## 📸 Project Demo

### 1. The Intelligence (Backend)
*The core AI agent detecting a money laundering ring using local Llama 3.2:*


### 2. The Interface (Frontend)
*The analyst dashboard visualizing the detected fraud ring:*


---

## 🚀 Key Features

* **Graph Neural Network (R-GCN):** Uses Relational Graph Convolutional Networks to detect "cyclic" transaction patterns (A → B → C → A) that traditional tabular models miss.
* **GraphRAG Explanation Agent:** A custom AI agent that retrieves topological subgraphs (k-hop neighbors) and uses a local LLM to explain *why* a user was flagged.
* **Privacy-First Architecture:** Runs 100% locally using **Ollama** (Llama 3.2 1B), ensuring no financial data leaves the secure environment.
* **Interactive Dashboard:** A React/TypeScript UI for compliance officers to visualize risk scores and transaction flows.

## 🛠️ Tech Stack

* **AI/ML:** Python, PyTorch Geometric, NetworkX, Scikit-learn
* **GenAI:** LangChain, Ollama (Llama 3.2), Prompt Engineering
* **Frontend:** React, TypeScript, Vite, Tailwind CSS, Shadcn UI
* **Data:** Synthetic financial graph generation with injected fraud topologies

---

## 💻 How to Run

### 1. Start the AI Backend
The backend handles data generation, model training, and the explanation agent.

```bash
# Navigate to python folder
cd python

# Install dependencies
pip install -r requirements.txt

# 1. Generate synthetic data
python data_gen.py

# 2. Train the Fraud Detection Model (R-GCN)
python gnn_train.py

# 3. Run the Explanation Agent
# Ensure Ollama is running first ('ollama serve')
python agent_explainer.py --user_id 77 --model llama3.2:1b