"""Checks on the files that are submitted: answer.md structure, no secrets, no course data in the repository."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".toml", ".txt"}


def test_answer_md_has_the_course_sections_and_auto_blocks():
    text = (ROOT / "answer.md").read_text(encoding="utf-8")
    for heading in ("# Lecture 5 Answer", "## Exercise", "### Results by method", "## Homework", "Level attempted:"):
        assert heading in text
    for name in ("compare", "answers", "findings"):
        assert re.search(rf"<!-- AUTO:{name} -->\n.+?\n<!-- /AUTO:{name} -->", text, re.S)
    assert "**Advanced**" in text


def test_no_api_keys_in_submitted_files():
    key = re.compile(r"AIza[0-9A-Za-z_\-]{30,}|GEMINI_API_KEY\s*=\s*['\"]?[A-Za-z0-9_\-]{20,}")
    for path in ROOT.rglob("*"):
        if path.is_file() and path.suffix in TEXT_SUFFIXES and ".venv" not in path.parts and "data" not in path.parts:
            assert not key.search(path.read_text(encoding="utf-8", errors="ignore")), path


def test_course_materials_are_git_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "data/rag_data/" in ignore and ".env" in ignore


def test_no_em_dashes_in_the_written_files():
    for name in ("answer.md", "README.md"):
        assert "\u2014" not in (ROOT / name).read_text(encoding="utf-8"), name
