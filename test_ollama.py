import requests
import json

def test_ollama(model="qwen2.5-coder:7b", prompt="Explain the basic structure of a LaTeX document in 3 sentences."):
    url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    print(f"--- Sending request to Ollama ({model}) ---")
    try:
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        print("\n--- Response Received ---")
        print(result.get("response", "No response field found."))
        
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to Ollama. Is it running on http://localhost:11434?")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    # You can change the model name here to match what you have installed in Ollama
    test_ollama(model="phi3.5")
