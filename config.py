"""Configuration management for Code Review Agent."""
import os
from dotenv import load_dotenv

load_dotenv()

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

# LLM Configuration (GitHub Copilot Chat API)
# Uses OpenCode's OAuth token to access Copilot models
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.githubcopilot.com")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4.6")
COPILOT_AUTH_FILE = os.getenv("COPILOT_AUTH_FILE", os.path.expanduser("~/.local/share/opencode/auth.json"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 9000))
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
    print(f"OpenCode URL: {OPENCODE_BASE_URL}")
    print(f"OpenCode Model: {OPENCODE_MODEL}")
