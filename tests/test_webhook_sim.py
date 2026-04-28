#!/usr/bin/env python
"""
Simulate a GitHub webhook hitting your running server.
Tests the full pipeline: signature verification → agent dispatch.

Prerequisites:
    1. Server running: python main.py
    2. OpenCode running: opencode serve

Usage:
    python tests/test_webhook_sim.py
"""
import hashlib
import hmac
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config import GITHUB_WEBHOOK_SECRET


SERVER_URL = os.getenv("TEST_SERVER_URL", "http://localhost:8000")


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """Create the same HMAC-SHA256 signature GitHub sends."""
    sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


def test_health():
    """Verify the server is up."""
    print("[1/4] Health check...")
    try:
        r = requests.get(f"{SERVER_URL}/health", timeout=5)
        r.raise_for_status()
        print(f"  ✅ Server healthy: {r.json()}")
        return True
    except requests.ConnectionError:
        print(f"  ❌ Cannot connect to {SERVER_URL}. Is the server running? (python main.py)")
        return False


def test_invalid_signature():
    """Webhook with wrong signature should be rejected."""
    print("\n[2/4] Invalid signature → expect 403...")
    payload = json.dumps({"action": "opened", "pull_request": {}, "repository": {}, "sender": {}}).encode()
    r = requests.post(
        f"{SERVER_URL}/webhook",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": "sha256=invalid",
            "X-GitHub-Event": "pull_request",
        },
        timeout=10,
    )
    if r.status_code == 403:
        print(f"  ✅ Correctly rejected (403)")
        return True
    else:
        print(f"  ❌ Expected 403, got {r.status_code}: {r.text}")
        return False


def test_non_pr_event():
    """Non-PR event should be ignored gracefully."""
    print("\n[3/4] Non-PR event → expect 'ignored'...")
    payload = json.dumps({"action": "created"}).encode()
    sig = sign_payload(payload, GITHUB_WEBHOOK_SECRET)
    r = requests.post(
        f"{SERVER_URL}/webhook",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "issues",
        },
        timeout=10,
    )
    data = r.json()
    if data.get("status") == "ignored":
        print(f"  ✅ Correctly ignored: {data}")
        return True
    else:
        print(f"  ❌ Unexpected response: {data}")
        return False


def test_valid_pr_webhook(owner: str, repo: str, pr_number: int):
    """Send a properly-signed PR webhook. Agent will analyze the PR."""
    print(f"\n[4/4] Valid PR webhook → {owner}/{repo}#{pr_number}...")
    payload = json.dumps({
        "action": "opened",
        "pull_request": {
            "id": 1,
            "number": pr_number,
            "title": "Test PR",
            "body": "Testing the code review agent",
            "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
            "repository_url": f"https://api.github.com/repos/{owner}/{repo}",
            "user": {"login": owner},
        },
        "repository": {
            "name": repo,
            "html_url": f"https://github.com/{owner}/{repo}",
            "owner": {"login": owner},
        },
        "sender": {"login": owner},
    }).encode()

    sig = sign_payload(payload, GITHUB_WEBHOOK_SECRET)
    r = requests.post(
        f"{SERVER_URL}/webhook",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": sig,
            "X-GitHub-Event": "pull_request",
        },
        timeout=15,
    )
    data = r.json()
    if r.status_code == 202 and data.get("status") == "queued":
        print(f"  ✅ PR queued for analysis: {data}")
        print(f"\n  👉 Check analysis status: {SERVER_URL}/status/{owner}/{repo}#{pr_number}")
        print(f"  👉 Check GitHub PR: https://github.com/{owner}/{repo}/pull/{pr_number}")
        return True
    else:
        print(f"  ❌ Unexpected: {r.status_code} {data}")
        return False


def main():
    print("=" * 55)
    print("  Webhook Simulation Test")
    print("=" * 55)

    if not test_health():
        sys.exit(1)

    results = [
        test_invalid_signature(),
        test_non_pr_event(),
    ]

    # For the full webhook test, ask for PR details
    owner = input("\nEnter GitHub owner (your username): ").strip()
    repo = input("Enter repo name: ").strip()
    pr_number = int(input("Enter PR number: ").strip())

    results.append(test_valid_pr_webhook(owner, repo, pr_number))

    passed = sum(results)
    total = len(results)
    print(f"\n{'='*55}")
    print(f"  {passed}/{total} tests passed")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
