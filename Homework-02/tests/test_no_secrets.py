"""The homework rules forbid secrets in answer.md, code, logs or screenshots. This course needs no key in Homework 2."""
import re
from pathlib import Path

KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}|AQ\.[0-9A-Za-z_\-]{20,}|hf_[A-Za-z0-9]{30,}|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}")
ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".csv", ".txt", ".yml", ".yaml", ".env", ".cfg", ".ipynb", ".jsonl", ""}


def find_offenders(root: Path) -> list[str]:
    offenders = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts[:-1]) or "__pycache__" in relative.parts:
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if KEY_PATTERN.search(path.read_text(errors="ignore")):
            offenders.append(relative.as_posix())
    return offenders


def test_no_key_or_token_in_homework_folder():
    assert find_offenders(ROOT) == []


def test_pattern_and_scan_logic(tmp_path):
    assert KEY_PATTERN.search("AIza" + "x" * 35) and KEY_PATTERN.search("hf_" + "x" * 34) and KEY_PATTERN.search("ghp_" + "x" * 36)
    assert not KEY_PATTERN.search("hf_hub or a sentence about HF tokens")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "nodeids").write_text("hf_" + "x" * 34)
    (tmp_path / "run_a").mkdir()
    (tmp_path / "run_a" / "result.json").write_text("hf_" + "x" * 34)
    assert find_offenders(tmp_path) == ["run_a/result.json"]
