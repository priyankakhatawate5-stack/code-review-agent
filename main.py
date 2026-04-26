"""
Main entry point that integrates webhook server with the agent.
"""
import json
import logging
import threading
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from webhook_server import app, verify_github_signature
from agent import create_agent
from config import GITHUB_TOKEN, ENABLE_AUTO_APPROVE

logger = logging.getLogger(__name__)

# Thread pool for async agent execution
executor = ThreadPoolExecutor(max_workers=5)

# In-memory store for pending analyses (use Redis in production)
pending_analyses: Dict[str, Any] = {}
_analyses_lock = threading.Lock()
_MAX_STORED_ANALYSES = 100


def extract_pr_info(payload: Dict[str, Any]) -> Dict[str, str]:
    """Extract PR information from webhook payload."""
    pr_data = payload.get("pull_request", {})
    repo_data = payload.get("repository", {})

    return {
        "owner": repo_data.get("owner", {}).get("login", ""),
        "repo": repo_data.get("name", ""),
        "pr_number": pr_data.get("number", 0),
        "repo_url": repo_data.get("html_url", ""),
        "pr_url": pr_data.get("html_url", ""),
        "pr_title": pr_data.get("title", ""),
        "action": payload.get("action", ""),
    }


def run_agent_analysis(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """
    Run the code review agent on a PR.

    This runs in a separate thread to not block the webhook response.
    """
    logger.info(f"Starting agent analysis for {owner}/{repo}#{pr_number}")

    try:
        agent = create_agent(GITHUB_TOKEN)
        result = agent.analyze_pr(
            owner=owner,
            repo=repo,
            pr_number=pr_number,
            auto_approve=ENABLE_AUTO_APPROVE,
        )
        logger.info(f"Analysis completed for {owner}/{repo}#{pr_number}")
        return result

    except Exception as e:
        logger.error(f"Error running agent analysis: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "owner": owner,
            "repo": repo,
            "pr_number": pr_number,
        }


def process_pr_event(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a PR webhook event.

    Returns immediately (webhook response is 202 Accepted).
    Agent runs asynchronously in background.
    """
    try:
        pr_info = extract_pr_info(payload)

        # Only analyze on opened and synchronize (updated) events
        if pr_info["action"] not in ["opened", "synchronize"]:
            logger.info(f"Skipping PR {pr_info['action']} event")
            return {"status": "skipped", "reason": f"Action '{pr_info['action']}' is not analyzed"}

        # Check if already analyzing this PR
        analysis_key = f"{pr_info['owner']}/{pr_info['repo']}#{pr_info['pr_number']}"
        with _analyses_lock:
            if analysis_key in pending_analyses:
                logger.warning(f"Analysis already in progress for {analysis_key}")
                return {"status": "already_in_progress", "key": analysis_key}

            # Evict oldest entries if at capacity
            if len(pending_analyses) >= _MAX_STORED_ANALYSES:
                oldest_key = next(iter(pending_analyses))
                del pending_analyses[oldest_key]

            # Mark as pending
            pending_analyses[analysis_key] = {
                "status": "queued",
                "action": pr_info["action"],
            }

        # Submit to thread pool (non-blocking)
        future = executor.submit(
            run_agent_analysis,
            pr_info["owner"],
            pr_info["repo"],
            pr_info["pr_number"],
        )

        # Add callback to update status
        def analysis_complete(fut):
            try:
                result = fut.result()
                with _analyses_lock:
                    pending_analyses[analysis_key] = result
                logger.info(f"Analysis status updated: {analysis_key} -> {result['status']}")
            except Exception as e:
                logger.error(f"Error in analysis callback: {e}")
                with _analyses_lock:
                    pending_analyses[analysis_key] = {"status": "error", "error": str(e)}

        future.add_done_callback(analysis_complete)

        return {
            "status": "queued",
            "key": analysis_key,
            "message": "PR queued for analysis",
            "pr": pr_info,
        }

    except Exception as e:
        logger.error(f"Error processing PR event: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@app.post("/webhook")
async def handle_webhook_with_agent(request: Request) -> JSONResponse:
    """Webhook handler that verifies signature and triggers agent analysis."""
    payload_body = await request.body()

    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_github_signature(payload_body, signature):
        logger.warning("Invalid webhook signature received")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = json.loads(payload_body)
    except json.JSONDecodeError:
        logger.error("Failed to parse webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = request.headers.get("X-GitHub-Event", "unknown")
    logger.info(f"Received GitHub event: {event_type}")

    if event_type != "pull_request":
        logger.info(f"Ignoring non-PR event: {event_type}")
        return JSONResponse({"status": "ignored", "message": "Only PR events are processed"})

    result = process_pr_event(payload)
    return JSONResponse(result, status_code=202)


@app.get("/status/{key:path}")
async def get_analysis_status(key: str) -> JSONResponse:
    """Get the status of a PR analysis. Key format: owner/repo#pr_number"""
    with _analyses_lock:
        if key in pending_analyses:
            return JSONResponse(pending_analyses[key])
    raise HTTPException(status_code=404, detail=f"No analysis found for key: {key}")


@app.get("/analyses")
async def list_analyses() -> JSONResponse:
    """List all ongoing and completed analyses."""
    with _analyses_lock:
        snapshot = dict(pending_analyses)
    return JSONResponse({"total": len(snapshot), "analyses": snapshot})


if __name__ == "__main__":
    import uvicorn
    from config import HOST, PORT

    logger.info(f"Starting Code Review Agent Server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
