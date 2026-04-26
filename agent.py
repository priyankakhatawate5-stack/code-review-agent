"""Code review agent using local Ollama model via OpenAI-compatible API."""
import json
import logging
from typing import Any, Dict

from openai import OpenAI

from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from mcp_tools import CodeReviewTools

logger = logging.getLogger(__name__)


class CodeReviewAgent:
    """Autonomous code review agent using a local Ollama model."""

    def __init__(self, github_token: str):
        self.client = OpenAI(
            base_url=OLLAMA_BASE_URL,
            api_key="ollama",  # required by the client but unused by Ollama
        )
        self.tools = CodeReviewTools(github_token)
        self.model = OLLAMA_MODEL

    def _build_system_prompt(self) -> str:
        return """You are an expert code reviewer assistant. Your role is to analyze pull requests and provide comprehensive code reviews.

You should:
1. Analyze code for security vulnerabilities (hardcoded secrets, SQL injection, etc.)
2. Identify code quality issues (anti-patterns, style violations, complexity)
3. Suggest performance optimizations
4. Recommend refactoring improvements

For each issue found:
- Explain WHY it's a problem
- Provide the IMPACT of the issue
- Suggest a CONCRETE FIX with code example if applicable
- Rate SEVERITY (critical, high, medium, low)

You have access to tools to:
- Read changed files in the PR
- Get full file content for context
- Check for syntax errors and secrets
- Analyze code quality
- Post comments and request changes on GitHub

Always be constructive and educational in your reviews. Provide actionable feedback."""

    def _convert_tools(self) -> list:
        """Convert MCP tool format to OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
            for tool in self.tools.get_all_tools()
        ]

    def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """Execute a tool and return the result as JSON string."""
        try:
            tool_method = getattr(self.tools, tool_name)
            result = tool_method(**tool_input)
            return json.dumps(result)
        except AttributeError:
            error_msg = f"Tool '{tool_name}' not found"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})
        except Exception as e:
            error_msg = f"Error executing tool '{tool_name}': {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def analyze_pr(
        self, owner: str, repo: str, pr_number: int, auto_approve: bool = False
    ) -> Dict[str, Any]:
        """Analyze a PR autonomously using the local model."""
        logger.info(f"Starting analysis for {owner}/{repo}#{pr_number}")

        auto_approve_instruction = (
            "6. After posting your review comment: if you found NO critical or high severity issues, "
            "call approve_pr to approve the PR. If you found critical/high issues, call request_changes instead."
            if auto_approve
            else "6. After posting your review comment, call request_changes if there are critical or high severity issues."
        )

        user_message = f"""Analyze the pull request #{pr_number} in the {owner}/{repo} repository for:
1. Security vulnerabilities (secrets, unsafe patterns)
2. Code quality issues (style, complexity, anti-patterns)
3. Performance optimizations
4. Refactoring suggestions

Steps:
1. First, get the PR files to see what changed
2. Get full content of Python files that were changed
3. Analyze each file for syntax, secrets, code quality, and refactoring opportunities
4. Compile all findings into a comprehensive review
5. Post a comment on the PR with your findings
{auto_approve_instruction}

Be thorough but practical. Focus on issues that truly matter."""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": user_message},
        ]

        tools = self._convert_tools()
        iteration = 0
        max_iterations = 10

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Agent iteration {iteration}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )

            message = response.choices[0].message
            messages.append(message.model_dump(exclude_unset=True))

            finish_reason = response.choices[0].finish_reason
            if finish_reason == "stop" or not message.tool_calls:
                logger.info("Agent completed analysis")
                return {
                    "status": "completed",
                    "iterations": iteration,
                    "pr_number": pr_number,
                    "repository": f"{owner}/{repo}",
                }

            # Process all tool calls in this response
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_input = json.loads(tool_call.function.arguments)

                logger.info(f"Agent called tool: {tool_name}")
                result = self._execute_tool(tool_name, tool_input)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        logger.warning(f"Max iterations ({max_iterations}) reached")
        return {
            "status": "max_iterations_reached",
            "iterations": iteration,
            "pr_number": pr_number,
            "repository": f"{owner}/{repo}",
        }

    def analyze_file_snippet(self, content: str, filename: str) -> Dict[str, Any]:
        """Analyze a single file snippet without full PR context."""
        logger.info(f"Analyzing file: {filename}")

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": f"""Analyze the following Python file for code quality, security, and refactoring needs:

File: {filename}
```python
{content}
```

Provide:
1. Security issues (if any)
2. Code quality issues
3. Refactoring suggestions
4. Overall assessment"""},
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        return {
            "filename": filename,
            "analysis": response.choices[0].message.content,
        }


def create_agent(github_token: str) -> CodeReviewAgent:
    """Factory function to create an agent."""
    return CodeReviewAgent(github_token)
