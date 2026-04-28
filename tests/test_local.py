#!/usr/bin/env python
"""
Local test — no GitHub, no server needed.
Tests all MCP tools against sample code.

Usage:
    python tests/test_local.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_tools import CodeReviewTools


SAMPLE_BAD_CODE = '''\
import json
import os
import requests

# TODO: refactor this mess
# FIXME: hardcoded creds

API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
DB_URL = "postgres://admin:supersecretpassword@db.example.com:5432/prod"

def fetch_user(user_id, api_key="ghp_abc123def456ghi789jkl012mno345pqr678"):
    response = requests.get(f"https://api.example.com/users/{user_id}", headers={"Authorization": f"Bearer {api_key}"})
    data = response.json()
    if data:
        if isinstance(data, dict):
            if "user" in data:
                if data["user"]:
                    if "email" in data["user"]:
                        if "@" in data["user"]["email"]:
                            return data["user"]
    return None

def process(a, b, c, d, e, f, g, h):
    x = a + b
    y = c + d
    z = e + f
    w = g + h
    return x + y + z + w

unused_variable = 42
'''

SAMPLE_GOOD_CODE = '''\
"""A clean module."""

def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"
'''

SAMPLE_REQUIREMENTS = '''\
flask==2.0.1
requests>=2.31.0
django==3.2.0
'''


def run_tests():
    passed = 0
    failed = 0

    # Use a dummy token since we won't hit GitHub API
    tools = CodeReviewTools("dummy-token")

    # --- Syntax check ---
    print("\\n[1/5] Syntax analysis (valid code)")
    result = tools.analyze_syntax("good.py", SAMPLE_GOOD_CODE)
    if not result["has_syntax_errors"]:
        print("  ✅ PASS — no syntax errors")
        passed += 1
    else:
        print(f"  ❌ FAIL — unexpected errors: {result['errors']}")
        failed += 1

    print("\\n[2/5] Syntax analysis (invalid code)")
    result = tools.analyze_syntax("bad.py", "def foo(:\\n  pass")
    if result["has_syntax_errors"]:
        print(f"  ✅ PASS — caught: {result['errors'][0]['message']}")
        passed += 1
    else:
        print("  ❌ FAIL — syntax error not detected")
        failed += 1

    # --- Secret detection ---
    print("\\n[3/5] Secret detection")
    result = tools.detect_secrets(SAMPLE_BAD_CODE)
    types_found = list(result["secrets_by_type"].keys())
    if result["detected_secrets"] and len(types_found) >= 2:
        print(f"  ✅ PASS — found {len(types_found)} secret types: {types_found}")
        passed += 1
    else:
        print(f"  ❌ FAIL — expected >=2 secret types, got {types_found}")
        failed += 1

    # --- Pylint / code quality ---
    print("\\n[4/5] Code quality (pylint)")
    result = tools.run_pylint("bad.py", SAMPLE_BAD_CODE)
    issue_types = {i["type"] for i in result["issues"]}
    if result["total_issues"] > 0:
        print(f"  ✅ PASS — found {result['total_issues']} issues: {issue_types}")
        passed += 1
    else:
        print("  ❌ FAIL — no issues detected in bad code")
        failed += 1

    # --- Refactoring suggestions ---
    print("\\n[5/5] Refactoring suggestions")
    result = tools.suggest_refactoring("bad.py", SAMPLE_BAD_CODE)
    if result["total_suggestions"] > 0:
        print(f"  ✅ PASS — {result['total_suggestions']} suggestions:")
        for s in result["suggestions"]:
            print(f"       • [{s['severity']}] {s['message']}")
        passed += 1
    else:
        print("  ❌ FAIL — no refactoring suggestions")
        failed += 1

    # --- Summary ---
    print(f"\\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
    print(f"{'='*50}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
