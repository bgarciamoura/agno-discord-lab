"""Testes da tool save_deliverable (escrita em disco isolada via tmp_path)."""

from pathlib import Path

from agno.run.base import RunContext

from tools import deliverables


def ctx(tmp_path, **deps):
    return RunContext(run_id="run1", session_id="sess1", dependencies=deps or None)


def test_saves_into_output_dir_from_dependencies(tmp_path):
    path = deliverables.save_deliverable("schema.sql", "CREATE TABLE x (id INT);", run_context=ctx(tmp_path, output_dir=str(tmp_path)))
    saved = Path(path)
    assert saved.parent == tmp_path.resolve()
    assert saved.read_text(encoding="utf-8") == "CREATE TABLE x (id INT);"


def test_fallback_dir_uses_session_and_run(tmp_path, monkeypatch):
    monkeypatch.setattr(deliverables, "DEFAULT_ROOT", tmp_path / "outputs")
    path = Path(deliverables.save_deliverable("doc.md", "# oi", run_context=ctx(tmp_path)))
    assert path.parent == (tmp_path / "outputs" / "sess1" / "run1").resolve()


def test_sanitizes_path_traversal(tmp_path):
    path = Path(deliverables.save_deliverable("../../evil.md", "x", run_context=ctx(tmp_path, output_dir=str(tmp_path))))
    assert path.parent == tmp_path.resolve()
    assert path.name == "evil.md"


def test_rejects_forbidden_extension(tmp_path):
    result = deliverables.save_deliverable("run.sh", "rm -rf /", run_context=ctx(tmp_path, output_dir=str(tmp_path)))
    assert result.startswith("Erro")
    assert not list(tmp_path.iterdir())


def test_rejects_empty_content(tmp_path):
    assert deliverables.save_deliverable("a.md", "   ", run_context=ctx(tmp_path, output_dir=str(tmp_path))).startswith("Erro")


def test_truncates_long_content(tmp_path):
    big = "a" * (deliverables.MAX_CHARS + 500)
    path = Path(deliverables.save_deliverable("big.txt", big, run_context=ctx(tmp_path, output_dir=str(tmp_path))))
    text = path.read_text(encoding="utf-8")
    assert "truncado" in text
    assert len(text) < len(big)
