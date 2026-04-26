# Autonomous Code Review & Refactoring Agent

An AI-powered GitHub PR reviewer that automatically analyzes code for security vulnerabilities, code quality issues, performance problems, and refactoring opportunities.

## Features

✅ **Security Scanning**
- Detect hardcoded secrets (API keys, passwords, tokens)
- Identify vulnerable dependencies
- Find unsafe code patterns

✅ **Code Quality Analysis**
- Syntax error detection
- Code complexity assessment
- Style violation identification
- Unused code detection

✅ **Refactoring Suggestions**
- Function decomposition recommendations
- Code duplication detection
- Performance optimization suggestions
- Design pattern improvements

✅ **Autonomous Workflow**
- Automatically analyzes every PR
- Posts comprehensive review comments
- Can request changes or auto-approve
- Learns from context and PR description

## Prerequisites

- Python 3.11+
- GitHub account with repo access
- [Anthropic API key](https://console.anthropic.com)

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd code-review-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your credentials
# You need:
# - GITHUB_TOKEN: GitHub Personal Access Token (with repo access)
# - GITHUB_WEBHOOK_SECRET: Secret for webhook validation
# - ANTHROPIC_API_KEY: Your Claude API key
```

**Getting credentials:**

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Grant `repo` and `workflow` permissions
4. Copy the token to `.env`

**Webhook Secret:**
```bash
# Generate a random secret
python -c "import secrets; print(secrets.token_hex(32))"
```

**Anthropic API Key:**
1. Visit https://console.anthropic.com/account/keys
2. Create a new API key
3. Copy to `.env`

### 3. Test Locally

```bash
# Verify configuration
python config.py

# Run the server
python webhook_server.py
# Server runs at http://localhost:8000
```

## GitHub Setup

### Create a GitHub App (Recommended)

1. Go to https://github.com/settings/apps
2. Click "New GitHub App"
3. Fill in:
   - App name: `Code Review Agent`
   - Homepage URL: `https://yourdomain.com`
   - Webhook URL: `https://yourdomain.com/webhook`
   - Webhook Secret: (paste your secret from above)
4. Grant permissions:
   - `pull_requests`: Read & write
   - `contents`: Read
   - `checks`: Read & write
5. Subscribe to events:
   - `pull_request`
6. Install the app on your repositories

### Configure Webhook

1. In your repo settings → Webhooks
2. Add payload URL: `https://yourdomain.com/webhook`
3. Content type: `application/json`
4. Secret: (use your GITHUB_WEBHOOK_SECRET)
5. Events: Select "Pull requests"

## Deployment

### Option 1: Heroku (Free tier deprecated)

Use Railway.app or Fly.io instead:

```bash
# Deploy to Railway
railway init
railway add
railway up
```

### Option 2: Docker

```bash
# Build image
docker build -t code-review-agent .

# Run container
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_token \
  -e ANTHROPIC_API_KEY=your_key \
  -e GITHUB_WEBHOOK_SECRET=your_secret \
  code-review-agent
```

### Option 3: AWS Lambda + API Gateway

(See `deployment/lambda_handler.py`)

## Usage

### Automatic Review (CI/CD)

Once set up, the agent automatically:
1. Detects PR opened/updated events
2. Fetches changed files
3. Analyzes code with Claude
4. Posts review comment with findings
5. Optionally requests changes or approves

### Manual Review (CLI)

```python
from agent import create_agent

agent = create_agent("your_github_token")

# Analyze a PR
result = agent.analyze_pr(
    owner="username",
    repo="repo-name",
    pr_number=42,
    auto_approve=False
)

# Analyze a code snippet
analysis = agent.analyze_file_snippet(
    content="your code here",
    filename="example.py"
)
print(analysis["analysis"])
```

## Configuration

Edit `.env` to customize:

```bash
# Model (default: claude-opus-4-7)
CLAUDE_MODEL=claude-opus-4-7

# Auto-approve clean PRs (default: false)
ENABLE_AUTO_APPROVE=false

# Severity threshold for requesting changes (0-10, default: 8)
CRITICAL_SEVERITY_THRESHOLD=8

# Max analysis time in seconds (default: 60)
MAX_ANALYSIS_TIME_SECONDS=60
```

## Example Review Comment

```markdown
## 🤖 AI Code Review

### Summary
Found 2 security concerns and 3 code quality improvements in this PR.

### Security Issues
- **Hardcoded API Key**: Line 24 contains exposed AWS credentials
  - Impact: Anyone with repo access can use this key
  - Fix: Move to environment variable or AWS Secrets Manager

### Code Quality Issues
- **Unused Import**: Line 3, `json` module not used
  - Remove: `import json`

- **Line Too Long**: Line 45 exceeds 100 character limit
  - Current: `if user and user.is_active and user.last_login and user.last_login > ...`
  - Fix: Break into multiple conditions

### Refactoring Suggestions
- **Function too long**: `process_user_data()` is 78 lines
  - Extract validation into `validate_user_data()`
  - Extract processing into `transform_user_data()`

### ✅ Recommendations
- **Priority**: Fix hardcoded credentials immediately
- **Nice-to-have**: Clean up unused imports and long lines
```

## Architecture

```
code-review-agent/
├── webhook_server.py      # FastAPI server for GitHub webhooks
├── agent.py              # Claude agent orchestration
├── mcp_tools.py          # MCP tools for code analysis
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── .env.example         # Environment template
└── tests/               # Test suite (coming soon)
```

## How It Works

1. **Webhook Event**: GitHub sends PR event to webhook endpoint
2. **Validation**: Verify webhook signature
3. **Agent Initialization**: Create Claude agent with MCP tools
4. **Analysis Loop**:
   - Claude examines the PR
   - Calls tools (get files, analyze code, etc.)
   - Synthesizes findings
   - Posts review comment
5. **Completion**: Agent marks PR as reviewed

## Limitations

- Works with Python files primarily (extensible to other languages)
- Limited by Claude's context window (200K tokens)
- GitHub API rate limits: 5,000 requests/hour
- Static analysis only (no runtime execution)

## Troubleshooting

**Webhook not received:**
- Verify webhook URL is publicly accessible
- Check webhook secret matches
- View GitHub webhook deliveries in repo settings

**Agent not analyzing:**
- Check logs for API errors
- Verify GITHUB_TOKEN and ANTHROPIC_API_KEY are valid
- Ensure PR files are in supported language

**Review comments not posting:**
- Verify GitHub token has `pull_requests:write` permission
- Check rate limits: `gh api rate_limit`

## Cost Estimation

- **Claude Opus**: ~$0.015 per PR (varies by code size)
- **GitHub API**: Free tier (5,000 requests/month)
- **Typical org**: $15-50/month for 200-500 PRs

## Future Enhancements

- [ ] Multi-language support (JavaScript, Go, Java, Rust)
- [ ] Custom rule configuration
- [ ] Integration with GitHub Advanced Security
- [ ] Historical trend analysis
- [ ] Team collaboration features
- [ ] Caching for faster analysis
- [ ] Custom severity rules per organization

## Contributing

Contributions welcome! Areas for improvement:
- Additional code analysis patterns
- Support for more languages
- Performance optimizations
- Test coverage

## License

MIT

## Support

- Issues: GitHub Issues
- Questions: Start a Discussion
- Feedback: Email or create an issue

---

**Made with ❤️ using Claude AI**
# code-review-agent
