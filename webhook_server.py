"""GitHub Webhook Server for Code Review Agent."""
import hashlib
import hmac
import json
import logging
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import (
    HOST,
    PORT,
    DEBUG,
    GITHUB_WEBHOOK_SECRET,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Review Agent", version="0.1.0")


class PullRequest(BaseModel):
    """GitHub Pull Request event model."""
    id: int
    number: int
    title: str
    body: Optional[str] = None
    html_url: str
    repository_url: str
    user: dict
    action: str


class WebhookPayload(BaseModel):
    """GitHub Webhook payload model."""
    action: str
    pull_request: dict
    repository: dict
    sender: dict


def verify_github_signature(payload_body: bytes, signature_header: str) -> bool:
    """Verify that the webhook signature matches GitHub's."""
    if not signature_header:
        return False

    # GitHub sends the signature as 'sha256=hex_digest'
    expected_signature = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256,
    ).hexdigest()

    # Extract the signature from the header
    try:
        signature_type, signature_value = signature_header.split("=")
        if signature_type != "sha256":
            logger.warning(f"Unexpected signature type: {signature_type}")
            return False

        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature_value)
    except ValueError:
        logger.warning(f"Invalid signature header format: {signature_header}")
        return False


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "service": "code-review-agent"}


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "name": "Code Review Agent",
        "version": "0.1.0",
        "status": "running",
        "webhook_endpoint": "/webhook",
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Code Review Agent on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
