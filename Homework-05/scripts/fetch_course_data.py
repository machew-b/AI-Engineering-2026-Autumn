"""Download the Lecture 05 course data into data/rag_data/ and check that every file is the one this homework used.

The course materials are marked "no photography or sharing with third parties without permission", so they are
not copied into this repository (data/rag_data/ is in .gitignore). This script gets them from the course's
repository at the revision named on the Lecture 05 problem page.

    uv run python -m scripts.fetch_course_data            # download, then verify
    uv run python -m scripts.fetch_course_data --verify   # verify only (no network)
"""
import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REVISION = "1ce722c2816b70ef62891a6378b2478af555e3fd"
BASE = f"https://raw.githubusercontent.com/matsuolab/lecture-ai-engineering-2026/{REVISION}/data/rag_data/"
DEST = Path(__file__).resolve().parents[1] / "data" / "rag_data"
SHA256 = {
    "lectures.json": "f6022c177ec1b5575b56d21307a5ae2aa09c586047398a17e1e4b86a56e99dce",
    "tree.json": "8d16e7f6a6b5c4864591fbfe0ac55598f6117ff226e4b1e2bd47b0401be79dfc",
    "graph.json": "6d32f92f97470d9febbdb076face22b9c74eb2c57d4950d3ed31978c57007e81",
    "index.sqlite3": "600d7a3633d84c21b6b26d511f9cd701d7dbee32bfe8eab0fd6fee3affb0f69e",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> list[str]:
    """Return one message per file that is missing or different from the revision used in answer.md."""
    problems = []
    for name, expected in SHA256.items():
        path = DEST / name
        if not path.is_file():
            problems.append(f"missing: {path}")
        elif digest(path) != expected:
            problems.append(f"different content (sha256 does not match): {path}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verify", action="store_true", help="only check the files, do not download")
    args = parser.parse_args()
    if not args.verify:
        DEST.mkdir(parents=True, exist_ok=True)
        for name in SHA256:
            print(f"downloading {name} ...")
            with urllib.request.urlopen(BASE + name, timeout=60) as response:
                (DEST / name).write_bytes(response.read())
    problems = verify()
    for message in problems:
        print(message)
    print("all 4 files match the revision used in answer.md" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
