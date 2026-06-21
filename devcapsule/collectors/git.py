"""Git repository collector."""

from __future__ import annotations

import subprocess
from pathlib import Path

from devcapsule.config import DEFAULT_DIFF_CHARS
from devcapsule.models import ContextSection, GitContext
from devcapsule.ranking.relevance import redact_secrets, truncate_text


class GitCollector:
    """Collect local Git state with bounded subprocess calls."""

    name = "git"

    def __init__(self, cwd: Path | None = None, max_diff_chars: int = DEFAULT_DIFF_CHARS) -> None:
        self.cwd = Path.cwd() if cwd is None else Path(cwd)
        self.max_diff_chars = max_diff_chars

    def _run(self, args: list[str], *, cwd: Path | None = None) -> tuple[str, str | None]:
        try:
            completed = subprocess.run(
                args,
                cwd=str(cwd or self.cwd),
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return "", str(exc)
        if completed.returncode != 0:
            return "", completed.stderr.strip() or completed.stdout.strip() or "command failed"
        return completed.stdout.rstrip("\n"), None

    def collect_context(self) -> GitContext:
        warnings: list[str] = []
        repo_root_text, error = self._run(["git", "rev-parse", "--show-toplevel"])
        if error:
            return GitContext(warnings=[f"Git unavailable or not a repository: {error}"])

        repo_root = Path(repo_root_text)
        repo_name = repo_root.name
        branch_text, error = self._run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        branch: str | None = branch_text or None
        if error:
            warnings.append(f"Could not determine branch: {error}")
            branch = None

        status_text, error = self._run(["git", "status", "--porcelain"], cwd=repo_root)
        if error:
            warnings.append(f"Could not read git status: {error}")
            status_text = ""
        modified_files, staged_files, untracked_files = self._parse_status(status_text)

        commits_text, error = self._run(["git", "log", "--oneline", "-n", "5"], cwd=repo_root)
        recent_commits = commits_text.splitlines() if commits_text else []
        if error:
            warnings.append(f"Could not read recent commits: {error}")

        diff_text, error = self._run(["git", "diff", "--no-ext-diff", "--"], cwd=repo_root)
        if error:
            warnings.append(f"Could not read git diff: {error}")
            diff_text = ""
        staged_diff_text, error = self._run(
            ["git", "diff", "--cached", "--no-ext-diff", "--"], cwd=repo_root
        )
        if error:
            warnings.append(f"Could not read staged diff: {error}")
            staged_diff_text = ""

        diff_text, _ = truncate_text(redact_secrets(diff_text), self.max_diff_chars)
        staged_diff_text, _ = truncate_text(redact_secrets(staged_diff_text), self.max_diff_chars)

        return GitContext(
            repo_root=str(repo_root),
            repo_name=repo_name,
            branch=branch,
            modified_files=modified_files,
            staged_files=staged_files,
            untracked_files=untracked_files,
            recent_commits=recent_commits,
            diff=diff_text,
            staged_diff=staged_diff_text,
            warnings=warnings,
        )

    def collect(self) -> ContextSection:
        context = self.collect_context()
        lines: list[str] = []
        if context.repo_root:
            lines.append(f"Repository: {context.repo_name}")
            lines.append(f"Branch: {context.branch or 'unknown'}")
        if context.modified_files:
            lines.append("\nModified files:")
            lines.extend(f"- {path}" for path in context.modified_files)
        if context.staged_files:
            lines.append("\nStaged files:")
            lines.extend(f"- {path}" for path in context.staged_files)
        if context.untracked_files:
            lines.append("\nUntracked files:")
            lines.extend(f"- {path}" for path in context.untracked_files)
        if context.warnings:
            lines.append("\nWarnings:")
            lines.extend(f"- {warning}" for warning in context.warnings)
        return ContextSection(title="Git State", content="\n".join(lines) or "No Git context.")

    @staticmethod
    def _parse_status(status_text: str) -> tuple[list[str], list[str], list[str]]:
        modified: list[str] = []
        staged: list[str] = []
        untracked: list[str] = []
        for line in status_text.splitlines():
            if not line:
                continue
            code = line[:2]
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if code == "??":
                untracked.append(path)
                continue
            if code[0] != " ":
                staged.append(path)
            if code[1] != " ":
                modified.append(path)
        return modified, staged, untracked
