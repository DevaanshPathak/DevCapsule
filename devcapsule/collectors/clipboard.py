"""Clipboard collector."""

from __future__ import annotations

from devcapsule.models import ClipboardContext, ContextSection
from devcapsule.ranking.relevance import redact_secrets, truncate_text


class ClipboardCollector:
    """Collect local clipboard text when pyperclip can access it."""

    name = "clipboard"

    def __init__(self, max_chars: int = 4_000) -> None:
        self.max_chars = max_chars

    def collect_context(self) -> ClipboardContext:
        try:
            import pyperclip  # type: ignore[import-untyped]
        except ImportError:
            return ClipboardContext(warnings=["pyperclip is not installed."])

        try:
            text = pyperclip.paste()
        except Exception as exc:  # pragma: no cover - platform dependent
            return ClipboardContext(warnings=[f"Clipboard unavailable: {exc}"])

        if not text:
            return ClipboardContext(available=True, warnings=["Clipboard is empty."])
        text = redact_secrets(text)
        text, _ = truncate_text(text, self.max_chars)
        return ClipboardContext(text=text, available=True)

    def collect(self) -> ContextSection:
        context = self.collect_context()
        content = context.text if context.text else "No clipboard text captured."
        if context.warnings:
            content += "\n\n" + "\n".join(f"- {warning}" for warning in context.warnings)
        return ContextSection(title="Clipboard Context", content=content, warnings=context.warnings)


def copy_text(text: str) -> tuple[bool, str | None]:
    """Copy text to the system clipboard if possible."""

    try:
        import pyperclip
    except ImportError:
        return False, "pyperclip is not installed"
    try:
        pyperclip.copy(text)
    except Exception as exc:  # pragma: no cover - platform dependent
        return False, str(exc)
    return True, None
