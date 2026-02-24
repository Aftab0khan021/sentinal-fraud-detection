"""
Test Ollama connection and agent initialization
"""
from langchain_ollama import OllamaLLM

try:
    print("Testing Ollama connection...")
    llm = OllamaLLM(model="llama3.2:1b", base_url="http://localhost:11434")

    response = llm.invoke("Say hello in one word")
    print(f"✓ Ollama is working!")
    print(f"Response: {response}")

except Exception as e:
    print(f"✗ Ollama connection failed: {e}")

# Test agent initialization
try:
    print("\nTesting agent initialization...")
    from agent_explainer import FraudExplainerAgent

    agent = FraudExplainerAgent()
    print("✓ Agent initialized successfully!")

except Exception as e:
    print(f"✗ Agent initialization failed: {e}")
    import traceback

    traceback.print_exc()
