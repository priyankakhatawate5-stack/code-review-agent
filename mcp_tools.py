"""MCP Tool definitions for the Code Review Agent."""
import ast
import json
import logging
import re
import subprocess
from typing import Any, Dict, List

from github import Github, GithubException

logger = logging.getLogger(__name__)


class CodeReviewTools:
    """Collection of MCP tools available to the Claude agent."""

    def __init__(self, github_token: str):
        """Initialize tools with GitHub token."""
        self.github = Github(github_token)
        self.github_token = github_token

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Get the list of files changed in a PR along with their diffs.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number

        Returns:
            Dictionary with file changes and diffs
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)

            files_data = {
                "files": [],
                "total_additions": pull.additions,
                "total_deletions": pull.deletions,
                "title": pull.title,
                "description": pull.body,
            }

            for file in pull.get_files():
                file_info = {
                    "filename": file.filename,
                    "status": file.status,
                    "additions": file.additions,
                    "deletions": file.deletions,
                    "patch": file.patch or "",
                }
                files_data["files"].append(file_info)

            logger.info(f"Retrieved {len(files_data['files'])} files for PR #{pr_number}")
            return files_data

        except GithubException as e:
            logger.error(f"Error fetching PR files: {e}")
            return {"error": str(e), "files": []}

    def get_file_content(
        self, owner: str, repo: str, file_path: str, ref: str = "HEAD"
    ) -> Dict[str, Any]:
        """
        Get the full content of a file in the repository.

        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to file
            ref: Branch/commit reference

        Returns:
            File content or error
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            content = repository.get_contents(file_path, ref=ref)
            return {
                "filename": file_path,
                "content": content.decoded_content.decode("utf-8"),
                "size": content.size,
            }

        except GithubException as e:
            logger.error(f"Error fetching file content: {e}")
            return {"error": str(e)}

    def analyze_syntax(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Analyze Python file for syntax errors.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Syntax analysis results
        """
        try:
            compile(content, file_path, "exec")
            return {"filename": file_path, "has_syntax_errors": False, "errors": []}

        except SyntaxError as e:
            return {
                "filename": file_path,
                "has_syntax_errors": True,
                "errors": [
                    {
                        "type": "SyntaxError",
                        "line": e.lineno,
                        "message": e.msg,
                        "text": e.text,
                    }
                ],
            }

    def detect_secrets(self, content: str) -> Dict[str, List]:
        """
        Detect hardcoded secrets and credentials in code.

        Args:
            content: Code content

        Returns:
            List of detected secrets
        """
        # Regex patterns for common secrets
        patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret_key": r"aws[_-]?secret[_-]?(?:access[_-]?)?key\s*=\s*['\"]([a-zA-Z0-9/+]{40})['\"]",
            "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY",
            "password": r"(?:password|passwd|pwd)\s*=\s*['\"](.{4,30})['\"]",
            "api_key": r"api[_-]?key\s*=\s*['\"]([a-zA-Z0-9_\-]{20,})['\"]",
            "github_token": r"ghp_[a-zA-Z0-9]{36,}",
            "github_oauth": r"gho_[a-zA-Z0-9]{36,}",
            "slack_token": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
            "database_url": r"(?:postgres|mysql|mongodb|redis)://[^:]+:[^@]+@",
            "generic_secret": r"(?:secret|token)\s*=\s*['\"]([a-zA-Z0-9_\-]{16,})['\"]",
            "stripe_key": r"sk_(?:live|test)_[a-zA-Z0-9]{24,}",
            "sendgrid_key": r"SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}",
        }

        secrets = {}
        for secret_type, pattern in patterns.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                secrets[secret_type] = matches

        return {
            "detected_secrets": bool(secrets),
            "secrets_by_type": secrets,
            "severity": "CRITICAL" if secrets else "NONE",
        }

    def check_dependencies(self, content: str, filename: str) -> Dict[str, Any]:
        """
        Check for vulnerable dependencies (basic implementation).

        Args:
            content: requirements.txt or setup.py content
            filename: Name of the file being analyzed

        Returns:
            Vulnerability check results
        """
        import os
        import tempfile

        package_pattern = r"^([a-zA-Z0-9\-_]+[>=<!]=?[0-9\.\*,]+|[a-zA-Z0-9\-_]+)$"
        packages = []

        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                if re.match(r"^[a-zA-Z0-9]", line):
                    packages.append(line)

        vulnerabilities = []
        scan_error = None

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                f.write("\n".join(packages))
                tmp_path = f.name

            result = subprocess.run(
                ["safety", "check", "-r", tmp_path, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            os.unlink(tmp_path)

            if result.stdout:
                vuln_data = json.loads(result.stdout)
                for v in vuln_data:
                    vulnerabilities.append({
                        "package": v[0],
                        "affected_versions": v[1],
                        "installed_version": v[2],
                        "description": v[3],
                        "cve": v[4] if len(v) > 4 else None,
                    })
        except FileNotFoundError:
            scan_error = "safety not installed — run 'pip install safety' to enable CVE scanning"
        except subprocess.TimeoutExpired:
            scan_error = "safety check timed out"
        except (json.JSONDecodeError, Exception) as e:
            scan_error = f"safety check failed: {e}"

        return {
            "filename": filename,
            "packages_found": packages,
            "vulnerable_packages": vulnerabilities,
            "scan_error": scan_error,
        }

    def run_quality_checks(self, file_path: str, content: str) -> Dict[str, Any]:
        """
        Run lightweight Python code-quality checks: unused imports
        (via AST), long lines, and TODO/FIXME markers.

        Unused-import detection uses the ast module rather than regex
        so it correctly handles `from x import y`, aliased imports, and
        avoids false positives from name mentions inside strings.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Code quality issues
        """
        issues = []
        lines = content.split("\n")

        # Unused-import detection via AST
        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            # Skip AST-based checks if file doesn't parse; syntax errors
            # are reported separately by analyze_syntax.
            tree = None

        if tree is not None:
            imported_names: Dict[str, int] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname or alias.name.split(".")[0]
                        imported_names[name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        name = alias.asname or alias.name
                        imported_names[name] = node.lineno

            used_names = {
                node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
            } | {
                node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
            }

            for name, lineno in imported_names.items():
                if name not in used_names:
                    issues.append({
                        "line": lineno,
                        "type": "unused-import",
                        "message": f"Unused import: {name}",
                        "severity": "low",
                    })

        # Line-level checks
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append({
                    "line": i,
                    "type": "line-too-long",
                    "message": f"Line is too long ({len(line)} > 100 characters)",
                    "severity": "low",
                })
            if "TODO" in line or "FIXME" in line:
                issues.append({
                    "line": i,
                    "type": "fixme-comment",
                    "message": f"Found {line.strip()}",
                    "severity": "info",
                })

        return {
            "filename": file_path,
            "total_issues": len(issues),
            "issues": issues,
        }

    def suggest_refactoring(self, file_path: str, content: str) -> Dict[str, List]:
        """
        Suggest refactoring opportunities.

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Refactoring suggestions
        """
        suggestions = []

        # Check for duplicate code patterns
        if content.count("def ") > 5:
            suggestions.append({
                "type": "excessive_functions",
                "message": "File contains many functions. Consider breaking into modules.",
                "severity": "low",
            })

        # Check for function length
        lines = content.split("\n")
        current_function = None
        function_lines = 0

        for i, line in enumerate(lines):
            if re.match(r"^def\s+\w+", line):
                if current_function and function_lines > 50:
                    suggestions.append({
                        "type": "long_function",
                        "function": current_function,
                        "lines": function_lines,
                        "message": f"Function '{current_function}' is {function_lines} lines. Consider breaking it down.",
                        "severity": "medium",
                    })
                current_function = re.match(r"^def\s+(\w+)", line).group(1)
                function_lines = 0
            elif current_function:
                function_lines += 1

        # Check for complex conditionals
        if content.count("if") > 10:
            suggestions.append({
                "type": "excessive_conditionals",
                "message": "File has many conditional branches. Consider simplifying logic.",
                "severity": "low",
            })

        return {
            "filename": file_path,
            "total_suggestions": len(suggestions),
            "suggestions": suggestions,
        }

    def post_review_comment(
        self, owner: str, repo: str, pr_number: int, body: str
    ) -> Dict[str, Any]:
        """
        Post a review comment on a GitHub PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Comment body (markdown)

        Returns:
            Comment creation result
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)
            comment = pull.create_issue_comment(body)

            logger.info(f"Posted comment on PR #{pr_number}: {comment.id}")
            return {
                "success": True,
                "comment_id": comment.id,
                "comment_url": comment.html_url,
            }

        except GithubException as e:
            logger.error(f"Error posting comment: {e}")
            return {"success": False, "error": str(e)}

    def request_changes(
        self, owner: str, repo: str, pr_number: int, body: str
    ) -> Dict[str, Any]:
        """
        Request changes on a PR (requires proper permissions).

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Review body

        Returns:
            Review creation result
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)

            # Create a review that requests changes
            review = pull.create_review(body=body, event="REQUEST_CHANGES")
            logger.info(f"Requested changes on PR #{pr_number}")

            return {
                "success": True,
                "review_id": review.id,
                "event": "REQUEST_CHANGES",
            }

        except GithubException as e:
            logger.error(f"Error requesting changes: {e}")
            return {"success": False, "error": str(e)}

    def approve_pr(self, owner: str, repo: str, pr_number: int, body: str = "") -> Dict[str, Any]:
        """
        Approve a PR.

        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            body: Optional review message

        Returns:
            Review creation result
        """
        try:
            repository = self.github.get_repo(f"{owner}/{repo}")
            pull = repository.get_pull(pr_number)

            review = pull.create_review(body=body, event="APPROVE")
            logger.info(f"Approved PR #{pr_number}")

            return {
                "success": True,
                "review_id": review.id,
                "event": "APPROVE",
            }

        except GithubException as e:
            logger.error(f"Error approving PR: {e}")
            return {"success": False, "error": str(e)}

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Return all tools in MCP format."""
        return [
            {
                "name": "get_pr_files",
                "description": "Get changed files in a GitHub PR with diffs",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string", "description": "Repository owner"},
                        "repo": {"type": "string", "description": "Repository name"},
                        "pr_number": {"type": "integer", "description": "PR number"},
                    },
                    "required": ["owner", "repo", "pr_number"],
                },
            },
            {
                "name": "get_file_content",
                "description": "Get full content of a file",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "file_path": {"type": "string"},
                        "ref": {"type": "string", "default": "HEAD"},
                    },
                    "required": ["owner", "repo", "file_path"],
                },
            },
            {
                "name": "analyze_syntax",
                "description": "Check file for Python syntax errors",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["file_path", "content"],
                },
            },
            {
                "name": "detect_secrets",
                "description": "Detect hardcoded secrets and credentials",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Code content to scan"},
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "check_dependencies",
                "description": "Check requirements.txt or setup.py for issues",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "filename": {"type": "string"},
                    },
                    "required": ["content", "filename"],
                },
            },
            {
                "name": "run_quality_checks",
                "description": "Run lightweight Python code-quality checks: unused imports (via AST), long lines, and TODO/FIXME markers",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["file_path", "content"],
                },
            },
            {
                "name": "suggest_refactoring",
                "description": "Suggest refactoring opportunities",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["file_path", "content"],
                },
            },
            {
                "name": "post_review_comment",
                "description": "Post a comment on a GitHub PR",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                        "body": {"type": "string", "description": "Comment body (markdown)"},
                    },
                    "required": ["owner", "repo", "pr_number", "body"],
                },
            },
            {
                "name": "request_changes",
                "description": "Request changes on a GitHub PR",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                        "body": {"type": "string"},
                    },
                    "required": ["owner", "repo", "pr_number", "body"],
                },
            },
            {
                "name": "approve_pr",
                "description": "Approve a GitHub PR",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "owner": {"type": "string"},
                        "repo": {"type": "string"},
                        "pr_number": {"type": "integer"},
                        "body": {"type": "string", "description": "Optional review message"},
                    },
                    "required": ["owner", "repo", "pr_number"],
                },
            },
        ]
