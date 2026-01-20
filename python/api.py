"""
SentinAL: FastAPI Backend (CORS Fixed)
======================================
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agent_explainer import load_data, FraudExplainerAgent
import uvicorn
import os

app = FastAPI(title="SentinAL Fraud Detection API")

# --- THE FIX: ALLOW EVERYTHING ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <--- Allows localhost, 127.0.0.1, and everything else
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State
print("\n[API] 1. Starting Server...")
try:
    if os.path.basename(os.getcwd()) != "python":
        print("⚠️  Warning: Running from wrong directory. Please cd into 'python/' folder.")
    
    graph, fraud_scores = load_data()
    
    # Use the fast model
    model_name = "llama3.2:1b" 
    print(f"[API] 2. Connecting to AI Model ({model_name})...")
    agent = FraudExplainerAgent(graph, fraud_scores, model=model_name)
    print("[API]    ✓ AI System Connected")

except Exception as e:
    print(f"❌ Critical Error: {e}")
    agent = None

@app.get("/analyze/{user_id}")
async def analyze_user(user_id: int):
    if agent is None:
        raise HTTPException(status_code=500, detail="AI System failed to load.")

    try:
        print(f"[API] Request received for User {user_id}...")
        
        # Get Scores
        try:
            score = fraud_scores['fraud_probability'][user_id]
        except:
            score = 0.0

        # Run AI
        explanation = agent.explain(user_id)
        
        return {
            "user_id": user_id,
            "score": f"{score:.3f}",
            "is_fraud": score > 0.8,
            "reason": "Suspicious cyclic topology detected" if score > 0.8 else "Normal behavior",
            "agent_report": explanation
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)