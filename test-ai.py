import os
from google import genai
from dotenv import load_dotenv

load_dotenv() # Load your .env file

api_key = os.getenv("GEMINI_API_KEY")
print(f"🔑 API Key Loaded: {'Yes' if api_key else 'NO'}")

if not api_key:
    print("❌ Error: GEMINI_API_KEY is missing from .env")
    exit()

try:
    print("📡 Attempting to connect to Gemini...")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Explain quantum physics in 5 words.'
    )
    print("✅ Success! Response:")
    print(response.text)
except Exception as e:
    print(f"\n❌ Connection Failed: {e}")