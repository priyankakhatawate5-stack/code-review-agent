#!/usr/bin/env python
"""
Create a test PR with intentionally bad code on a GitHub repo.
This lets you trigger the agent and see real review comments.

Usage:
    python tests/create_test_pr.py --owner YOUR_USERNAME --repo YOUR_REPO

Prerequisites:
    - GITHUB_TOKEN set in .env with repo write access
    - The repo must already exist on GitHub
"""
import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from github import Github
from config import GITHUB_TOKEN

BAD_CODE = '''\
import json
import os
import sys
import requests

# TODO: clean up this code
# FIXME: remove hardcoded secrets before production

API_KEY = "sk-proj-abcdefghijklmnopqrstuvwxyz1234567890"
DATABASE_URL = "postgres://admin:password123@prod-db.example.com:5432/myapp"
AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"

def get_user_data(user_id):
    """Fetch user data from API."""
    response = requests.get(
        f"https://api.example.com/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {API_KEY}"},
        verify=False  # SECURITY: disabling SSL verification
    )
    data = response.json()
    return data

def process_payment(amount, card_number, cvv):
    """Process a payment - logs sensitive data!"""
    print(f"Processing payment: card={card_number}, cvv={cvv}, amount={amount}")
    # SQL injection vulnerability
    query = f"INSERT INTO payments (amount, card) VALUES ({amount}, '{card_number}')"
    return query

def validate_input(data):
    if data:
        if isinstance(data, dict):
            if "user" in data:
                if data["user"]:
                    if "email" in data["user"]:
                        if "@" in data["user"]["email"]:
                            if len(data["user"]["email"]) > 5:
                                if data["user"]["email"].count("@") == 1:
                                    return True
    return False

class UserManager:
    def __init__(self):
        self.password = "admin123"  # hardcoded password
        self.secret_key = "my-super-secret-key-do-not-share"

    def authenticate(self, username, password):
        # Timing attack vulnerable comparison
        if password == self.password:
            return True
        return False

unused_var = "this is never used"
another_unused = 42
'''


def main():
    parser = argparse.ArgumentParser(description="Create a test PR with bad code")
    parser.add_argument("--owner", required=True, help="GitHub repo owner")
    parser.add_argument("--repo", required=True, help="Repository name")
    args = parser.parse_args()

    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN not set in .env")
        sys.exit(1)

    g = Github(GITHUB_TOKEN)
    repo = g.get_user(args.owner).get_repo(args.repo)

    branch_name = f"test/bad-code-{int(time.time())}"

    # Get default branch SHA
    default_branch = repo.default_branch
    ref = repo.get_git_ref(f"heads/{default_branch}")
    sha = ref.object.sha

    # Create branch
    print(f"📌 Creating branch: {branch_name}")
    repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)

    # Add the bad file
    print("📝 Adding bad_code.py with intentional issues...")
    repo.create_file(
        path="bad_code.py",
        message="Add code with security issues for review testing",
        content=BAD_CODE,
        branch=branch_name,
    )

    # Create PR
    print("🔀 Opening pull request...")
    pr = repo.create_pull(
        title="[TEST] Code with security issues - please review",
        body=(
            "## Test PR for Code Review Agent\n\n"
            "This PR contains intentionally bad code to test the automated reviewer.\n\n"
            "**Expected findings:**\n"
            "- Hardcoded secrets (API keys, passwords, AWS keys)\n"
            "- SQL injection vulnerability\n"
            "- SSL verification disabled\n"
            "- Deeply nested conditionals\n"
            "- Sensitive data logging\n"
            "- Unused imports and variables\n"
        ),
        head=branch_name,
        base=default_branch,
    )

    print(f"\n{'='*55}")
    print(f"✅ PR created: {pr.html_url}")
    print(f"{'='*55}")
    print(f"\nIf your webhook is set up, the agent will review it automatically.")
    print(f"Or test manually:")
    print(f"  python tests/test_e2e_github.py --owner {args.owner} --repo {args.repo} --pr {pr.number}")


if __name__ == "__main__":
    main()
