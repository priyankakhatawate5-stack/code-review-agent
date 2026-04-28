# Testing the Code Review Agent

## Quick Test (no GitHub needed)
```bash
python tests/test_local.py
```
Tests MCP tools locally: syntax checker, secret detector, pylint, refactoring suggestions.

## End-to-End Test (posts a real comment on GitHub)
```bash
python tests/test_e2e_github.py --owner YOUR_USERNAME --repo YOUR_REPO --pr NUMBER
```
Runs the full agent on a real PR and posts a review comment.

## Webhook Simulation Test (hits your running server)
```bash
# Start the server first: python main.py
python tests/test_webhook_sim.py
```
Sends a fake signed webhook to your local server to verify the full pipeline.

## Test with a Dummy PR
```bash
python tests/create_test_pr.py --owner YOUR_USERNAME --repo YOUR_REPO
```
Creates a branch with intentionally bad code, opens a PR, so you can see the agent review it.
