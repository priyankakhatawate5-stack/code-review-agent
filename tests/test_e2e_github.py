#!/usr/bin/env python
"""
End-to-end test — runs the agent on a REAL GitHub PR.
Posts a review comment so you can verify on GitHub.

Usage:
    python tests/test_e2e_github.py --owner YOUR_USERNAME --repo YOUR_REPO --pr 1
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GITHUB_TOKEN, ENABLE_AUTO_APPROVE
from agent import create_agent


def main():
    parser = argparse.ArgumentParser(description="Run the code review agent on a real PR")
    parser.add_argument("--owner", required=True, help="GitHub repo owner (e.g. your username)")
    parser.add_argument("--repo", required=True, help="Repository name")
    parser.add_argument("--pr", required=True, type=int, help="PR number to analyze")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set in .env")
        sys.exit(1)

    print(f"🚀 Running agent on {args.owner}/{args.repo}#{args.pr}")
    print(f"   Auto-approve: {ENABLE_AUTO_APPROVE}")
    print(f"   Token: {GITHUB_TOKEN[:10]}...")
    print()

    agent = create_agent(GITHUB_TOKEN)
    result = agent.analyze_pr(
        owner=args.owner,
        repo=args.repo,
        pr_number=args.pr,
        auto_approve=ENABLE_AUTO_APPROVE,
    )

    print(f"\n{'='*50}")
    print(f"✅ Result: {result}")
    print(f"{'='*50}")
    print(f"\n👉 Check your PR for the review comment:")
    print(f"   https://github.com/{args.owner}/{args.repo}/pull/{args.pr}")


if __name__ == "__main__":
    main()
