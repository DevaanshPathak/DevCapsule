from __future__ import annotations

from devcapsule.collectors.project import ProjectCollector


def test_project_collector_ignores_generated_and_sensitive_paths(tmp_path) -> None:
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "lib.js").write_text("ignored", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=secretvalue", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[project]\nname='demo'", encoding="utf-8")
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")

    context = ProjectCollector(tmp_path).collect_context()
    tree_text = "\n".join(context.tree)

    assert "node_modules" not in tree_text
    assert ".env" not in tree_text
    assert "README.md" in tree_text
    assert {file.path for file in context.important_files} == {"README.md", "pyproject.toml"}


def test_project_collector_redacts_file_content(tmp_path) -> None:
    (tmp_path / "README.md").write_text("token = verysecretvalue", encoding="utf-8")

    context = ProjectCollector(tmp_path).collect_context()

    assert context.important_files[0].redacted is True
    assert "verysecretvalue" not in context.important_files[0].content
