"""Configuration management for Code Review Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_APP_PRIVATE_KEY = os.getenv("GITHUB_APP_PRIVATE_KEY")

# Ollama Configuration (local model)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Agent Configuration
ENABLE_AUTO_APPROVE = os.getenv("ENABLE_AUTO_APPROVE", "false").lower() == "true"
CRITICAL_SEVERITY_THRESHOLD = int(os.getenv("CRITICAL_SEVERITY_THRESHOLD", 8))
MAX_ANALYSIS_TIME_SECONDS = int(os.getenv("MAX_ANALYSIS_TIME_SECONDS", 60))

# Validation
def validate_config():
    """Validate that all required configuration is present."""
    required = ["GITHUB_TOKEN", "GITHUB_WEBHOOK_SECRET"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    print("✓ Configuration validated successfully")


if __name__ == "__main__":
    validate_config()
    print(f"GitHub Token: {GITHUB_TOKEN[:10]}...")
    print(f"Ollama URL: {OLLAMA_BASE_URL}")
    print(f"Ollama Model: {OLLAMA_MODEL}")
