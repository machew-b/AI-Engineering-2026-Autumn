"""The homework rules forbid API keys in answer.md, code, logs or screenshots."""

import re
from pathlib import Path

# Google API keys start with "AIza" followed by 35 URL-safe characters.
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}")
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
