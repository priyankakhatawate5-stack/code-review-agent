#!/usr/bin/env python
"""
Quick test script to demonstrate the Code Review Agent.

Usage:
    python test_agent.py
"""

import os
from pathlib import Path

from config import validate_config, GITHUB_TOKEN
from agent import create_agent


def test_file_analysis():
    """Test analyzing a code snippet."""
    print("=" * 60)
    print("Testing Code Review Agent - File Analysis")
    print("=" * 60)

    # Create agent
    agent = create_agent(GITHUB_TOKEN)

    # Sample Python code with intentional issues
    sample_code = """
import json
import requests
import os

# TODO: This needs refactoring
def process_user_data(user_data, db_connection, cache, api_key=None):
    # Hardcoded API key - SECURITY ISSUE!
    api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"

    # Very long line that exceeds 100 characters and should be split into multiple parts for readability
    if user_data and user_data.get('email') and user_data.get('active') and user_data.get('verified'):
        user = {"id": user_data.get('id'), "email": user_data.get('email'), "active": user_data.get('active')}

    # Duplicate code block
    try:
        response = requests.get(f"https://api.example.com/users/{user_data['id']}",
                              headers={"Authorization": f"Bearer {api_key}"})
        data = response.json()
    except Exception as e:
        print(f"Error: {e}")

    # Another duplicate code block
    try:
        response = requests.post(f"https://api.example.com/users",
                               headers={"Authorization": f"Bearer {api_key}"})
        result = response.json()
    except Exception as e:
        print(f"Error: {e}")

    return user

# Unused variable
unused_config = {"debug": True}

# Function that's too long with many nested conditions
def validate_and_process(data):
    if data:
        if isinstance(data, dict):
            if 'user' in data:
                if data['user']:
                    if 'email' in data['user']:
                        if '@' in data['user']['email']:
                            # Process user
                            return True
    return False
"""

    print("\n📝 Analyzing sample Python file...")
    print("=" * 60)

    result = agent.analyze_file_snippet(sample_code, "example.py")

    print("\n🔍 Analysis Results:")
    print("-" * 60)
    print(result["analysis"])
    print("-" * 60)

    return result


def test_webhook_validation():
    """Test webhook signature validation."""
    print("\n" + "=" * 60)
    print("Testing Webhook Signature Validation")
    print("=" * 60)

    from webhook_server import verify_github_signature
    import json

    # Test payload
    test_payload = b'{"action": "opened", "pull_request": {"number": 42}}'
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "test-secret")

    # Generate valid signature
    import hmac
    import hashlib

    expected_signature = hmac.new(
        secret.encode(),
        test_payload,
        hashlib.sha256,
    ).hexdigest()

    # Test with valid signature
    valid_header = f"sha256={expected_signature}"
    is_valid = verify_github_signature(test_payload, valid_header)

    print(f"\n✓ Valid signature verified: {is_valid}")
    print(f"  Payload: {test_payload.decode()}")
    print(f"  Signature: sha256={expected_signature[:16]}...")

    # Test with invalid signature
    invalid_header = "sha256=invalid"
    is_valid = verify_github_signature(test_payload, invalid_header)

    print(f"\n✗ Invalid signature rejected: {not is_valid}")
    print(f"  Signature: {invalid_header}")

    return True


def test_mcp_tools():
    """Test MCP tools initialization."""
    print("\n" + "=" * 60)
    print("Testing MCP Tools")
    print("=" * 60)

    from mcp_tools import CodeReviewTools

    tools = CodeReviewTools(GITHUB_TOKEN)
    all_tools = tools.get_all_tools()

    print(f"\n✓ Available tools: {len(all_tools)}")
    print("\nTools list:")
    for tool in all_tools:
        print(f"  • {tool['name']:<25} - {tool['description'][:40]}...")

    # Test syntax analyzer
    print("\n\nTesting syntax analyzer...")
    valid_code = 'x = 1\nprint(x)'
    result = tools.analyze_syntax("test.py", valid_code)
    print(f"  Valid code: {result['has_syntax_errors'] == False}")

    invalid_code = 'x = 1\nprint(x'  # Missing closing paren
    result = tools.analyze_syntax("test.py", invalid_code)
    print(f"  Invalid code detected: {result['has_syntax_errors'] == True}")

    # Test secret detection
    print("\nTesting secret detection...")
    code_with_secret = 'api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"'
    result = tools.detect_secrets(code_with_secret)
    print(f"  Secret detected: {'api_key' in result['secrets_by_type'] or len(result['secrets_by_type']) > 0}")

    code_without_secret = 'x = 1\ny = 2'
    result = tools.detect_secrets(code_without_secret)
    print(f"  No false positives: {len(result['secrets_by_type']) == 0}")

    return True


def main():
    """Run all tests."""
    print("\n")
    print("╔═════════════════════════════════════════════════════════╗")
    print("║   Autonomous Code Review Agent - Test Suite            ║")
    print("╚═════════════════════════════════════════════════════════╝")

    try:
        # Validate configuration
        print("\n🔐 Validating configuration...")
        validate_config()
        print("   ✓ Configuration is valid")

        # Run tests
        test_webhook_validation()
        test_mcp_tools()
        test_file_analysis()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)

        print("\n📚 Next steps:")
        print("  1. Set up GitHub App: https://github.com/settings/apps")
        print("  2. Configure webhooks in your repository")
        print("  3. Deploy the server: docker-compose up")
        print("  4. Open a PR to trigger the agent")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\n📋 Make sure you have:")
        print("  • GITHUB_TOKEN set in .env")
        print("  • ANTHROPIC_API_KEY set in .env")
        print("  • GITHUB_WEBHOOK_SECRET set in .env")


if __name__ == "__main__":
    main()
