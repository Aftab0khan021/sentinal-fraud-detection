"""
SentinAL: FastAPI Backend (Final Fix for 'List' Error)
======================================================
1. Fixed 'AttributeError' by accessing fraud scores as a list index.
2. Kept 'No Warm-Up' for instant start.
3. Standardized 'agent_report' output.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent_explainer import load_data, FraudExplainerAgent
import uvicorn
import os
import sys
from pathlib import Path

# --- SETUP: ABSOLUTE PATHS ---
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

app = FastAPI(title="SentinAL Fraud Detection API")

# --- SETUP: CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
agent = None
fraud_scores = None

@app.on_event("startup")
async def startup_event():
    """Load data on server start."""
    global agent, fraud_scores
    print("\n[API] 1. Server Starting...")
    
    # 1. Load Data
    try:
        print(f"[API]    Loading data from: {BASE_DIR}")
        graph, fraud_scores = load_data()
        print("[API]    ✓ Data Loaded")
    except Exception as e:
        print(f"❌ DATA ERROR: {e}")
        return

    # 2. Connect AI (Lazy Load)
    try:
        model_name = "llama3.2:1b"
        print(f"[API] 2. Connecting to AI ({model_name})...")
        agent = FraudExplainerAgent(graph, fraud_scores, model=model_name)
        print("[API]    ✓ AI System Connected (Lazy Loading Enabled)")
            
    except Exception as e:
        print(f"❌ AI ERROR: {e}")

@app.get("/analyze/{user_id}")
async def analyze_user(user_id: int):
    """
    Main Endpoint: Returns Fraud Score (List Index) + AI Explanation
    """
    if agent is None:
        return {"error": True, "agent_report": "AI System not connected."}

    try:
        print(f"[API] Analyzing User {user_id}...")
        
        # --- FIX IS HERE ---
        # OLD (Error): score = fraud_scores['fraud_probability'].get(user_id, 0.0)
        # NEW (Correct): Access list by index with bounds check
        try:
            score = fraud_scores['fraud_probability'][user_id]
        except IndexError:
            print(f"⚠️ User ID {user_id} out of bounds, defaulting to 0.0")
            score = 0.0
        except TypeError:
            # Fallback if fraud_scores is somehow None
            score = 0.0
        
        # 2. Get AI Explanation
        explanation = agent.explain(user_id)
        
        # 3. Determine Fraud Status
        is_fraud = score > 0.8
        
        return {
            "error": False,
            "user_id": user_id,
            "score": f"{score:.3f}",
            "is_fraud": is_fraud,
            "reason": "Suspicious cyclic topology detected" if is_fraud else "Normal behavior",
            "agent_report": explanation 
        }
        
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
        return {
            "error": True,
            "agent_report": f"Server Error: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)