import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("AVALAI_API_KEY") or not os.getenv("AVALAI_BASE_URL"):
    raise EnvironmentError("AVALAI_API_KEY and AVALAI_BASE_URL must be set in the environment or a .env file.")

print("Safar Travel AI Agent Setup:")
print(f"  Model: {os.getenv('MODEL_NAME', 'gpt-5.2')}")
print(f"  Base URL: {os.getenv('AVALAI_BASE_URL', 'Not Set')}")
print("  RAG data and tools are initializing via AgentManager...")