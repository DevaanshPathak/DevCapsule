"""Project structure and file collector."""

from __future__ import annotations

import os
from pathlib import Path

from devcapsule.config import (
    DEFAULT_FILE_CHARS,
    DEFAULT_TREE_ENTRIES,
    IGNORED_DIRS,
    IMPORTANT_FILES,
    SOURCE_EXTENSIONS,
)
from devcapsule.models import ContextSection, FileContext, ProjectContext
from devcapsule.ranking.relevance import (
    is_sensitive_path,
    language_for_path,
    rank_paths,
    redact_secrets,
    truncate_text,
)


class ProjectCollector:
    """Collect project tree and a ranked subset of important files."""

    name = "project"

    def __init__(
        self,
        root: Path | None = None,
        *,
        focus: str = "general",
        modified_files: list[str] | None = None,
        staged_files: list[str] | None = None,
        diff_text: str = "",
        terminal_text: str = "",
        max_file_chars: int = DEFAULT_FILE_CHARS,
        max_tree_entries: int = DEFAULT_TREE_ENTRIES,
    ) -> None:
        self.root = (Path.cwd() if root is None else Path(root)).resolve()
        self.focus = focus
        self.modified_files = set(modified_files or [])
        self.staged_files = set(staged_files or [])
        self.diff_text = diff_text
        self.terminal_text = terminal_text
        self.max_file_chars = max_file_chars
        self.max_tree_entries = max_tree_entries

    def collect_context(self) -> ProjectContext:
        warnings: list[str] = []
        tree, candidates = self._walk_project()
        important = self._collect_important_files(warnings)
        important_paths = {item.path for item in important}
        ranked = rank_paths(
            candidates,
            focus=self.focus,
            modified_files=self.modified_files,
            staged_files=self.staged_files,
            diff_text=self.diff_text,
            terminal_text=self.terminal_text,
        )
        source_files: list[FileContext] = []
        for relative_path in ranked:
            normalized = relative_path.as_posix()
            if normalized in important_paths:
                continue
            context = self._read_file(relative_path, purpose="Ranked relevant source/config file")
            if context is not None:
                source_files.append(context)
            if len(source_files) >= 12:
                break

        return ProjectContext(
            repo_root=str(self.root),
            tree=tree,
            important_files=important,
            source_files=source_files,
            warnings=warnings,
        )

    def collect(self) -> ContextSection:
        context = self.collect_context()
        lines = ["Project tree:"]
        lines.extend(f"- {entry}" for entry in context.tree[: self.max_tree_entries])
        if context.warnings:
            lines.append("\nWarnings:")
            lines.extend(f"- {warning}" for warning in context.warnings)
        return ContextSection(title="Project Structure", content="\n".join(lines))

    def _walk_project(self) -> tuple[list[str], list[Path]]:
        tree: list[str] = []
        candidates: list[Path] = []
        for current, dirnames, filenames in os.walk(self.root):
            current_path = Path(current)
            dirnames[:] = sorted(
                dirname for dirname in dirnames if dirname not in IGNORED_DIRS and not dirname.startswith(".tox")
            )
            rel_dir = current_path.relative_to(self.root)
            depth = 0 if rel_dir == Path(".") else len(rel_dir.parts)
            if depth > 5:
                dirnames[:] = []
                continue
            for dirname in dirnames:
                if len(tree) < self.max_tree_entries:
                    path = (rel_dir / dirname).as_posix() if rel_dir != Path(".") else f"{dirname}/"
                    if not path.endswith("/"):
                        path = f"{path}/"
                    tree.append(path)
            for filename in sorted(filenames):
                relative_path = (rel_dir / filename) if rel_dir != Path(".") else Path(filename)
                if is_sensitive_path(relative_path):
                    continue
                if len(tree) < self.max_tree_entries:
                    tree.append(relative_path.as_posix())
                if relative_path.suffix.lower() in SOURCE_EXTENSIONS or filename in IMPORTANT_FILES:
                    candidates.append(relative_path)
        if len(tree) >= self.max_tree_entries:
            tree.append("[Truncated: project tree exceeded max entry budget]")
        return tree, candidates

    def _collect_important_files(self, warnings: list[str]) -> list[FileContext]:
        contexts: list[FileContext] = []
        for name in sorted(IMPORTANT_FILES):
            relative_path = Path(name)
            if is_sensitive_path(relative_path):
                continue
            absolute_path = self.root / relative_path
            if not absolute_path.is_file():
                continue
            context = self._read_file(relative_path, purpose="Important project/dependency file")
            if context is not None:
                contexts.append(context)
        if not contexts:
            warnings.append("No standard README, dependency, or config files were found.")
        return contexts

    def _read_file(self, relative_path: Path, *, purpose: str) -> FileContext | None:
        if is_sensitive_path(relative_path):
            return None
        absolute_path = self.root / relative_path
        try:
            if not absolute_path.is_file() or absolute_path.stat().st_size > 1_000_000:
                return None
            raw = absolute_path.read_bytes()
        except OSError:
            return None
        if b"\x00" in raw[:4096]:
            return None
        text = raw.decode("utf-8", errors="replace")
        redacted = redact_secrets(text)
        truncated, was_truncated = truncate_text(redacted, self.max_file_chars)
        return FileContext(
            path=relative_path.as_posix(),
            purpose=purpose,
            content=truncated,
            language=language_for_path(relative_path),
            truncated=was_truncated,
            redacted=redacted != text,
            char_count=len(truncated),
        )
