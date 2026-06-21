"""Typer CLI for DevCapsule."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devcapsule.collectors.clipboard import copy_text
from devcapsule.config import DEFAULT_MAX_CHARS, FOCUS_MODES, get_history_db_path
from devcapsule.core import capture_context
from devcapsule.storage import (
    ensure_database,
    get_capture,
    get_latest_capture,
    list_captures,
    save_capture,
)

console = Console()
app = typer.Typer(
    name="devcapsule",
    help="Turn your current coding state into an AI-ready Markdown context capsule.",
    no_args_is_help=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Launch the TUI when no subcommand is provided."""

    if ctx.invoked_subcommand is not None:
        return
    launch_interactive()
    raise typer.Exit()


@app.command()
def capture(
    focus: Annotated[
        str,
        typer.Option(
            "--focus",
            "-f",
            help="Capture focus mode: debug, pr, explain, or general.",
        ),
    ] = "general",
    max_chars: Annotated[
        int,
        typer.Option("--max-chars", min=1, help="Maximum Markdown characters to capture."),
    ] = DEFAULT_MAX_CHARS,
    copy: Annotated[bool, typer.Option("--copy", help="Copy the capture to the clipboard.")] = False,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write the capture Markdown to a file."),
    ] = None,
) -> None:
    """Create a new context capsule."""

    focus = focus.lower()
    if focus not in FOCUS_MODES:
        raise typer.BadParameter(f"focus must be one of: {', '.join(sorted(FOCUS_MODES))}")

    with console.status("[bold]Collecting local project context...[/bold]"):
        capsule = capture_context(focus=focus, max_chars=max_chars)
        capture_id = save_capture(capsule)
        capsule = capsule.model_copy(update={"id": capture_id})

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(capsule.markdown, encoding="utf-8")

    if copy:
        copied, error = copy_text(capsule.markdown)
        if copied:
            console.print(f"{_success_mark()} Capture copied to clipboard", style="green")
        else:
            console.print(f"Clipboard copy skipped: {error}", style="yellow")

    console.print(
        f"{_success_mark()} Capture #{capture_id} created ({capsule.char_count} chars, focus={focus})",
        style="green",
    )
    if output is not None:
        console.print(f"Saved to {output}")


@app.command()
def share() -> None:
    """Copy the latest capsule to the clipboard."""

    capsule = get_latest_capture()
    if capsule is None:
        console.print("No captures found. Run `devcapsule capture` first.", style="yellow")
        raise typer.Exit(code=1)
    copied, error = copy_text(capsule.markdown)
    if not copied:
        console.print(f"Could not copy latest capsule: {error}", style="red")
        raise typer.Exit(code=1)
    console.print(f"{_success_mark()} Latest capsule copied to clipboard", style="green")


@app.command("history")
def history_command(
    limit: Annotated[int, typer.Option("--limit", "-n", min=1, help="Number of captures to show.")] = 20,
) -> None:
    """Show previous captures from SQLite."""

    captures = list_captures(limit=limit)
    table = Table(title="DevCapsule History")
    table.add_column("ID", justify="right")
    table.add_column("Created time")
    table.add_column("Repo name")
    table.add_column("Branch")
    table.add_column("Focus mode")
    table.add_column("Character count", justify="right")
    for item in captures:
        table.add_row(
            str(item.id or ""),
            item.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            item.repo_name or "unknown",
            item.branch or "unknown",
            item.focus,
            str(item.char_count),
        )
    console.print(table)


@app.command()
def view(id: int) -> None:
    """Print a previous capsule."""

    capsule = get_capture(id)
    if capsule is None:
        console.print(f"Capture #{id} not found.", style="red")
        raise typer.Exit(code=1)
    console.print(capsule.markdown)


@app.command()
def export(id: int, path: Path) -> None:
    """Export a previous capsule to a Markdown file."""

    capsule = get_capture(id)
    if capsule is None:
        console.print(f"Capture #{id} not found.", style="red")
        raise typer.Exit(code=1)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(capsule.markdown, encoding="utf-8")
    console.print(f"{_success_mark()} Exported capture #{id} to {path}", style="green")


@app.command()
def doctor() -> None:
    """Check optional local integrations."""

    rows = [
        ("Git", _ok(shutil.which("git") is not None), "git executable"),
        ("Clipboard", *_clipboard_status()),
        ("Shell history", *_shell_history_status()),
        ("SQLite database", *_sqlite_status()),
        ("TUI support", *_tui_status()),
    ]
    table = Table(title="DevCapsule Doctor")
    table.add_column("Integration")
    table.add_column("Status")
    table.add_column("Details")
    for name, status, detail in rows:
        style = "yellow" if status.startswith("!") else "green"
        table.add_row(name, status, detail, style=style)
    console.print(table)


def launch_interactive() -> None:
    """Launch Textual TUI, or print a fallback menu when unavailable/non-interactive."""

    if not sys.stdin.isatty() or not sys.stdout.isatty():
        _fallback_menu("Interactive terminal not detected.")
        return
    try:
        from devcapsule.tui import run_tui

        run_tui()
    except Exception as exc:  # pragma: no cover - interactive/platform dependent
        _fallback_menu(f"TUI unavailable: {exc}")


def _fallback_menu(reason: str | None = None) -> None:
    body = "\n".join(
        [
            "Create New Capture    devcapsule capture",
            "View History          devcapsule history",
            "Copy Latest Capsule   devcapsule share",
            "Export Capsule        devcapsule export <id> <path>",
            "Doctor                devcapsule doctor",
        ]
    )
    title = "DevCapsule"
    if reason:
        body = f"{reason}\n\n{body}"
    console.print(Panel(body, title=title, expand=False))


def _ok(value: bool) -> str:
    return f"{_success_mark()} OK" if value else "! Missing"


def _success_mark() -> str:
    mark = "\u2713"
    encoding = getattr(console.file, "encoding", None) or sys.stdout.encoding or "utf-8"
    try:
        mark.encode(encoding)
    except UnicodeEncodeError:
        return "+"
    return mark


def _clipboard_status() -> tuple[str, str]:
    try:
        import pyperclip  # type: ignore[import-untyped] # noqa: F401
    except ImportError:
        return "! Missing", "pyperclip is not installed"
    return f"{_success_mark()} OK", "pyperclip import succeeded"


def _shell_history_status() -> tuple[str, str]:
    from devcapsule.collectors.terminal import TerminalCollector

    for path in TerminalCollector()._candidate_history_files():
        if path.is_file():
            return f"{_success_mark()} OK", str(path)
    return "! Missing", "no supported history file found"


def _sqlite_status() -> tuple[str, str]:
    try:
        path = ensure_database()
    except Exception as exc:
        return "! Missing", str(exc)
    return f"{_success_mark()} OK", str(path or get_history_db_path())


def _tui_status() -> tuple[str, str]:
    try:
        import textual  # noqa: F401
    except ImportError:
        return "! Missing", "textual is not installed"
    return f"{_success_mark()} OK", "textual import succeeded"
