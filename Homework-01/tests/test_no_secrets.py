"""The homework rules forbid API keys in answer.md, code, logs or screenshots."""

import re
from pathlib import Path

# Google API keys: the older format is "AIza" plus 35 URL-safe characters, newer keys start with "AQ.".
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}|AQ\.[0-9A-Za-z_\-]{20,}")
ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".csv", ".txt", ".yml", ".yaml", ".env", ".cfg", ""}


def find_offenders(root: Path) -> list[str]:
    """Files under `root` that contain something shaped like a Google API key."""
    offenders = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        # Skip tool folders such as .venv, .git and .pytest_cache. They are not part of the submission, and
        # pytest's own cache stores test names, which here include deliberately fake keys.
        if any(part.startswith(".") for part in relative.parts[:-1]) or "__pycache__" in relative.parts:
            continue
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if KEY_PATTERN.search(path.read_text(errors="ignore")):
            offenders.append(relative.as_posix())
    return offenders


def test_no_google_api_key_in_homework_folder():
    offenders = find_offenders(ROOT)
    assert offenders == [], f"Possible API key found in: {offenders}"


def test_pattern_and_scan_logic(tmp_path):
    # the pattern recognizes both key formats and ignores normal text
    assert KEY_PATTERN.search("AIza" + "x" * 35)
    assert KEY_PATTERN.search("AQ." + "x" * 40)
    assert not KEY_PATTERN.search("AQ. a sentence that starts like that")
    assert not KEY_PATTERN.search("uv run python -m app.ask")

    # the scan flags a real submission file but ignores tool folders such as pytest's cache
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "nodeids").write_text("AQ." + "x" * 40)
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "run.csv").write_text("AIza" + "x" * 35)
    (tmp_path / "notes.md").write_text("nothing secret here")
    assert find_offenders(tmp_path) == ["results/run.csv"]
