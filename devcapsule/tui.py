"""Textual TUI for DevCapsule."""

from __future__ import annotations

from pathlib import Path

from devcapsule.collectors.clipboard import copy_text
from devcapsule.core import capture_context
from devcapsule.storage import get_capture, get_latest_capture, list_captures, save_capture

_TEXTUAL_IMPORT_ERROR: Exception | None = None

try:
    from textual.app import App, ComposeResult
    from textual.containers import Horizontal, Vertical
    from textual.widgets import Button, Footer, Header, Label, ListItem, ListView, Static
except Exception as exc:  # pragma: no cover - import depends on optional UI stack
    App = object  # type: ignore[assignment,misc]
    ComposeResult = object  # type: ignore[assignment,misc]
    _TEXTUAL_IMPORT_ERROR = exc
else:
    _TEXTUAL_IMPORT_ERROR = None


def run_tui() -> None:
    """Run the Textual application."""

    if _TEXTUAL_IMPORT_ERROR is not None:
        raise RuntimeError(str(_TEXTUAL_IMPORT_ERROR))
    DevCapsuleApp().run()


if _TEXTUAL_IMPORT_ERROR is None:

    class DevCapsuleApp(App[None]):
        """A small but functional capture/history UI."""

        CSS = """
        Screen {
            layout: vertical;
        }
        #body {
            height: 1fr;
        }
        #sidebar {
            width: 34;
            min-width: 30;
            border: solid $accent;
            padding: 1;
        }
        #history {
            height: 1fr;
            margin-top: 1;
        }
        #preview {
            width: 1fr;
            border: solid $surface;
            padding: 1;
            overflow: auto;
        }
        Button {
            width: 100%;
            margin-bottom: 1;
        }
        .muted {
            color: $text-muted;
        }
        """

        BINDINGS = [
            ("q", "quit", "Quit"),
            ("r", "refresh_history", "Refresh"),
            ("c", "create_capture", "Capture"),
        ]

        selected_id: int | None = None

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            with Horizontal(id="body"):
                with Vertical(id="sidebar"):
                    yield Static("DevCapsule", classes="muted")
                    yield Button("Create New Capture", id="capture", variant="primary")
                    yield Button("Copy Latest Capsule", id="copy")
                    yield Button("Export Selected Capsule", id="export")
                    yield Button("Doctor", id="doctor")
                    yield Button("Settings / Help", id="help")
                    yield Label("Capture History")
                    yield ListView(id="history")
                yield Static("Select a capture or create a new one.", id="preview")
            yield Footer()

        def on_mount(self) -> None:
            self.refresh_history()

        def action_refresh_history(self) -> None:
            self.refresh_history()

        def action_create_capture(self) -> None:
            self.create_capture()

        def on_button_pressed(self, event: Button.Pressed) -> None:
            button_id = event.button.id
            if button_id == "capture":
                self.create_capture()
            elif button_id == "copy":
                self.copy_latest()
            elif button_id == "export":
                self.export_selected()
            elif button_id == "doctor":
                self.show_doctor()
            elif button_id == "help":
                self.show_help()

        def on_list_view_selected(self, event: ListView.Selected) -> None:
            item_id = event.item.id or ""
            capture_id = int(item_id.removeprefix("capture-")) if item_id.startswith("capture-") else None
            if isinstance(capture_id, int):
                self.selected_id = capture_id
                capsule = get_capture(capture_id)
                if capsule is not None:
                    self.query_one("#preview", Static).update(capsule.markdown)

        def refresh_history(self) -> None:
            history = self.query_one("#history", ListView)
            history.clear()
            for item in list_captures(limit=30):
                label = f"#{item.id} {item.repo_name or 'unknown'} [{item.focus}] {item.created_at:%Y-%m-%d %H:%M}"
                row = ListItem(Label(label), id=f"capture-{item.id}")
                history.append(row)

        def create_capture(self) -> None:
            preview = self.query_one("#preview", Static)
            preview.update("Collecting local project context...")
            capsule = capture_context()
            capture_id = save_capture(capsule)
            self.selected_id = capture_id
            preview.update(capsule.markdown)
            self.refresh_history()
            self.notify(f"Capture #{capture_id} created")

        def copy_latest(self) -> None:
            capsule = get_latest_capture()
            if capsule is None:
                self.notify("No captures found", severity="warning")
                return
            copied, error = copy_text(capsule.markdown)
            if copied:
                self.notify("Latest capsule copied to clipboard")
            else:
                self.notify(f"Clipboard unavailable: {error}", severity="warning")

        def export_selected(self) -> None:
            if self.selected_id is None:
                self.notify("Select a capture first", severity="warning")
                return
            capsule = get_capture(self.selected_id)
            if capsule is None:
                self.notify("Selected capture was not found", severity="error")
                return
            path = Path.cwd() / f"devcapsule-{self.selected_id}.md"
            path.write_text(capsule.markdown, encoding="utf-8")
            self.notify(f"Exported to {path}")

        def show_doctor(self) -> None:
            from devcapsule.cli import (
                _clipboard_status,
                _shell_history_status,
                _sqlite_status,
                _tui_status,
            )

            rows = [
                ("Clipboard", *_clipboard_status()),
                ("Shell history", *_shell_history_status()),
                ("SQLite database", *_sqlite_status()),
                ("TUI support", *_tui_status()),
            ]
            text = "# Doctor\n\n" + "\n".join(f"- {name}: {status} ({detail})" for name, status, detail in rows)
            self.query_one("#preview", Static).update(text)

        def show_help(self) -> None:
            text = """# Settings / Help

- Capture: create a fresh Markdown context capsule for this repository.
- History: select any previous capture in the left pane to preview it.
- Copy Latest: place the newest capsule on the clipboard.
- Export Selected: write the selected capsule to `devcapsule-<id>.md`.
- Privacy: DevCapsule runs locally, stores history in SQLite, and never uploads files.
"""
            self.query_one("#preview", Static).update(text)
