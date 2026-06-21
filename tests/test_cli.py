from __future__ import annotations

from typer.testing import CliRunner

from devcapsule.cli import app


def test_cli_doctor_smoke(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVCAPSULE_DB_PATH", str(tmp_path / "history.sqlite3"))
    runner = CliRunner()

    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "DevCapsule Doctor" in result.output


def test_cli_capture_and_history_smoke(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DEVCAPSULE_DB_PATH", str(tmp_path / "history.sqlite3"))
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["capture", "--max-chars", "8000"])
        assert result.exit_code == 0, result.output
        assert "Capture #1 created" in result.output

        history = runner.invoke(app, ["history"])
        assert history.exit_code == 0, history.output
        assert "DevCapsule History" in history.output
        assert "general" in history.output
