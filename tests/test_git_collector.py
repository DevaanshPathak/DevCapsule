from __future__ import annotations

import shutil
import subprocess

import pytest

from devcapsule.collectors.git import GitCollector


@pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")
def test_git_collector_reads_temp_repo(tmp_path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    app_file = tmp_path / "app.py"
    app_file.write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)

    app_file.write_text("print('goodbye')\n", encoding="utf-8")
    (tmp_path / "new.py").write_text("x = 1\n", encoding="utf-8")

    context = GitCollector(tmp_path).collect_context()

    assert context.repo_name == tmp_path.name
    assert "app.py" in context.modified_files
    assert "new.py" in context.untracked_files
    assert "goodbye" in context.diff
