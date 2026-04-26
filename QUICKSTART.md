# Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Clone and Setup (2 min)

```bash
cd /Users/apple/Projects/ai/code-review-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure (1 min)

```bash
# Get credentials from:
# GitHub: https://github.com/settings/tokens (create new token with 'repo' scope)
# Anthropic: https://console.anthropic.com/account/keys
# Webhook secret: python -c "import secrets; print(secrets.token_hex(32))"

cp .env.example .env
# Edit .env with your credentials
nano .env
```

### Step 3: Validate Configuration (1 min)

```bash
python config.py
# Should output: ✓ Configuration validated successfully
```

### Step 4: Test Locally (1 min)

```bash
python test_agent.py
```

Output should show:
- ✓ Configuration is valid
- ✓ Webhook signature verification works
- ✓ MCP tools are available
- ✓ File analysis completes

### ✅ Success!

Your agent is working locally. Next step: Deploy to GitHub!

---

## 🔧 Deployment Options

### Option 1: Docker (Recommended for Development)

```bash
# Start with docker-compose
docker-compose up

# Agent available at http://localhost:8000
# Test endpoint: curl http://localhost:8000/health
```

### Option 2: Python Directly

```bash
python main.py
# or
python webhook_server.py
```

### Option 3: Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- AWS Lambda + API Gateway
- Heroku / Railway
- Kubernetes
- Docker with nginx

---

## 🔌 GitHub Setup

### Create GitHub App

1. Go to https://github.com/settings/apps
2. Click "New GitHub App"
3. Fill in:
   ```
   Name: Code Review Agent
   Homepage URL: https://yourdomain.com
   Webhook URL: https://yourdomain.com/webhook
   Webhook Secret: [paste your GITHUB_WEBHOOK_SECRET]
   ```
4. Permissions:
   ```
   Pull Requests: Read & Write
   Contents: Read
   Checks: Read & Write
   ```
5. Subscribe to: `pull_request` events
6. Install on your repositories

### Create GitHub Token (Alternative)

1. Go to https://github.com/settings/tokens
2. Create token with `repo` and `workflow` scopes
3. Copy to `GITHUB_TOKEN` in `.env`

---

## 📊 Example Analysis

The agent will analyze PRs and post comments like:

```markdown
## 🤖 AI Code Review

### Security Issues Found
- Hardcoded API key on line 24
  Impact: Anyone with repo access can misuse this
  Fix: Use environment variable or AWS Secrets Manager

### Code Quality Issues
- Unused import: json (line 3)
- Line too long: 145 chars (line 45) - exceeds 100 char limit
- Function process_user() is 89 lines - consider breaking down

### Refactoring Suggestions
- Extract validation logic into separate function
- Use context manager for database connection
- Consider using dataclass instead of dict for user

### ✅ Recommendations
- Fix: Hardcoded credentials (critical)
- Nice-to-have: Clean up unused imports and long lines
```

---

## 🧪 Manual Testing

### Test with Sample Code

```bash
python -c "
from agent import create_agent
from config import GITHUB_TOKEN

agent = create_agent(GITHUB_TOKEN)

code = '''
api_key = \"sk-1234567890\"  # SECURITY ISSUE!
x = 1
if x and x > 0 and x < 100:
    print(x)
'''

result = agent.analyze_file_snippet(code, 'test.py')
print(result['analysis'])
"
```

### Test Webhook Signature

```bash
python -c "
from webhook_server import verify_github_signature
import hmac
import hashlib

payload = b'{\"test\": \"data\"}'
secret = 'test-secret'

sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
header = f'sha256={sig}'

is_valid = verify_github_signature(payload, header)
print(f'Signature valid: {is_valid}')
"
```

### Monitor Analysis Progress

Once deployed, check analysis status:

```bash
# Get all ongoing analyses
curl http://localhost:8000/analyses

# Get status of specific PR
curl http://localhost:8000/status/owner/repo%23123
```

---

## 🐛 Troubleshooting

### Config validation fails
- ✓ Double-check `.env` has all required keys
- ✓ Test tokens are valid: `python config.py`

### Webhook not received
- ✓ Verify webhook URL is publicly accessible
- ✓ Check GitHub webhook deliveries in repo settings
- ✓ Verify webhook secret matches

### Agent not analyzing
- ✓ Check logs: `docker logs -f` or console output
- ✓ Verify GitHub token has proper permissions
- ✓ Check Anthropic API key is valid and has credits

### Review comments not posting
- ✓ Token needs `pull_requests:write` permission
- ✓ Check rate limits: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`

---

## 📈 Next Steps

1. **Deploy**: Push to production (see DEPLOYMENT.md)
2. **Configure**: Add custom rules and severity thresholds
3. **Monitor**: Track analysis quality and false positives
4. **Improve**: Add language support, custom checks
5. **Integrate**: Connect with CI/CD pipelines

---

## 📚 Learn More

- [Full README](README.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Configuration Reference](CONFIG.md)

---

**Happy coding! 🚀**
