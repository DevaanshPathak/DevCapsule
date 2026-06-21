# DevCapsule

DevCapsule turns your current coding state into an AI-ready context capsule in one command.

![Demo GIF placeholder](docs/demo-placeholder.gif)

DevCapsule is a local-first CLI and terminal UI for collecting the context developers usually paste by hand into AI coding assistants: Git status, diffs, modified files, project structure, terminal history, clipboard text, dependency files, and environment details. It turns that into a clean Markdown file you can paste into ChatGPT, Claude, Cursor, Codex, or any other assistant.

## Installation

```bash
git clone <repo-url>
cd DevCapsule
python -m pip install -e .
```

Then run:

```bash
devcapsule
```

## CLI Usage

Create a balanced capsule:

```bash
devcapsule capture
```

Focus the capture for a specific task:

```bash
devcapsule capture --focus debug
devcapsule capture --focus pr
devcapsule capture --focus explain
```

Control output size, write a Markdown file, or copy the result:

```bash
devcapsule capture --max-chars 30000
devcapsule capture --output capsule.md
devcapsule capture --copy
```

Work with local history:

```bash
devcapsule history
devcapsule view 1
devcapsule export 1 output.md
devcapsule share
devcapsule doctor
```

## TUI Usage

Running `devcapsule` with no subcommand opens the interactive Textual UI when the terminal supports it.

The TUI includes:

- Create New Capture
- Capture History
- Preview pane
- Copy Latest Capsule
- Export Selected Capsule
- Doctor
- Settings / Help

If Textual is unavailable or the command is run outside an interactive terminal, DevCapsule shows a Rich fallback menu with the same commands.

## Python API

```python
from devcapsule import capture_context

capsule = capture_context()
print(capsule.markdown)
```

The Python API captures context without requiring the CLI. CLI commands persist captures to SQLite; library callers can decide how they want to store or transmit the Markdown.

## Privacy Guarantees

DevCapsule is designed to be safe by default:

- No telemetry.
- No network requests.
- No API keys.
- No uploads.
- History is stored locally in SQLite at `~/.devcapsule/history.sqlite3`.
- `.env`, private key files, and common secret filenames are never included.
- Common API keys, tokens, passwords, private keys, AWS keys, GitHub tokens, and OpenAI keys are redacted as `[REDACTED]`.
- Large diffs and files are truncated with explicit notes.

## Example Output

````markdown
# DevCapsule Context

## Metadata

- Repository: my-app
- Branch: feature/auth-fix
- Working Directory: /Users/dev/my-app
- Focus Mode: debug

## Git State

Modified files:
- api/auth.py
- tests/test_auth.py

Git diff:
```diff
...
```

## Terminal Context

```bash
pytest tests/test_auth.py
```

## Suggested Prompt

Using the context above, help me debug this project. Focus on terminal commands, errors, changed files, and the Git diff first.
````

## Development Setup

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy devcapsule
```

Useful local smoke checks:

```bash
devcapsule doctor
devcapsule capture
devcapsule history
```

## Roadmap

- Per-project configuration file for ignore rules and capture defaults.
- Better terminal error-log ingestion.
- TUI search and keyboard-driven export flows.
- Optional capture templates for debugging, PR review, architecture explanation, and onboarding.
- More language-aware file purpose detection.

## License

MIT
