"""The homework rules forbid API keys in answer.md, code, logs or screenshots."""

import re
from pathlib import Path

# Google API keys: the older format is "AIza" plus 35 URL-safe characters, newer keys start with "AQ.".
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}|AQ\.[0-9A-Za-z_\-]{20,}")
ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".py", ".md", ".toml", ".json", ".csv", ".txt", ".yml", ".yaml", ".env", ".cfg", ""}


def test_no_google_api_key_in_homework_folder():
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if KEY_PATTERN.search(path.read_text(errors="ignore")):
            offenders.append(str(path.relative_to(ROOT)))
    assert offenders == [], f"Possible API key found in: {offenders}"


def test_pattern_recognizes_both_key_formats_and_ignores_normal_text():
    assert KEY_PATTERN.search("AIza" + "x" * 35)
    assert KEY_PATTERN.search("AQ." + "x" * 40)
    assert not KEY_PATTERN.search("AQ. a sentence that starts like that")
    assert not KEY_PATTERN.search("uv run python -m app.ask")
