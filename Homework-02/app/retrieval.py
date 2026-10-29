"""A deliberately simple glossary search, used as the comparison system for the fine-tuned model.

Rule (fixed before looking at any result): normalize the question, find every term name or alias that
appears in it, take the longest one, and return that entry's definition. If nothing matches, answer
"not in the glossary". No fuzzy matching, no thresholds, nothing tuned on the test questions. It is the
kind of lookup the Lecture 3 glossary search tool starts from.

Run:  uv run python -m app.retrieval      (writes results/retrieval_baseline.json and .md)
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from app import glossary_data as gd
from app import scoring

RESULTS = gd.ROOT / "results"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text or "")).strip().casefold()


def name_variants(entry: dict) -> list[str]:
    """Names to look for: the term, the term without its parenthesis, the parenthesis parts, and the aliases."""
    names = [entry["term"], *entry["aliases"]]
    m = re.match(r"^(.*?)（(.*)）\s*$", entry["term"])
    if m:
        names.append(m.group(1))
        names.extend(p for p in re.split(r"[/／・]", m.group(2)))
    seen, out = set(), []
    for n in names:
        n = _norm(n)
        if len(n) >= 2 and n not in seen:     # one-character names (like "r") would match almost anything
            seen.add(n)
            out.append(n)
    return out


def _found(question: str, name: str) -> bool:
    if name.isascii():                          # English names must not match inside a longer English word
        return re.search(rf"(?<![a-z0-9]){re.escape(name)}(?![a-z0-9])", question) is not None
    return name in question


def search(question: str, terms: list[dict]) -> tuple[dict | None, str | None]:
    q = _norm(question)
    best, best_name = None, None
    for entry in terms:
        for name in name_variants(entry):
            if _found(q, name) and (best_name is None or len(name) > len(best_name)):
                best, best_name = entry, name
    return best, best_name


def answer(question: str, terms: list[dict]) -> str:
    entry, _ = search(question, terms)
    return entry["definition"] if entry else gd.ABSTAIN_ANSWER


def evaluate_retrieval(test: list[dict], gold: dict, terms: list[dict]) -> tuple[dict, list[dict]]:
    rows = []
    for item in test:
        entry, name = search(item["question"], terms)
        text = entry["definition"] if entry else gd.ABSTAIN_ANSWER
        rows.append({"id": item["id"], "category": item["category"], "question": item["question"], "answer": text,
                     "matched_id": entry["id"] if entry else None, "matched_name": name,
                     **scoring.score_answer(text, gold[item["id"]])})
    return scoring.summarize(rows, "retrieval", 0.0), rows


def wrong_matches(rows: list[dict], gold: dict) -> list[dict]:
    """Rows where the search returned some entry, but not the one the question was about."""
    return [r for r in rows if r["matched_id"] is not None and r["matched_id"] != gold[r["id"]]["term_id"]]


def main() -> None:
    terms = gd.load_terms()
    data = gd.build_dataset(terms)
    summary, rows = evaluate_retrieval(data["test"], data["gold"], terms)
    bad = wrong_matches(rows, data["gold"])
    slim = [{k: r[k] for k in ("id", "category", "ok", "matched_id")} for r in rows]
    wrong = [{"id": r["id"], "question": r["question"], "matched_id": r["matched_id"], "matched_name": r["matched_name"]} for r in bad]
    row_lines = ",\n".join("  " + json.dumps(r, ensure_ascii=False) for r in slim)   # one row per line keeps the file short
    text = ('{\n "summary": ' + json.dumps(summary, ensure_ascii=False) + ',\n "wrong_matches": '
            + json.dumps(wrong, ensure_ascii=False) + ',\n "rows": [\n' + row_lines + "\n ]\n}\n")
    json.loads(text)   # must stay valid JSON
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval_baseline.json").write_text(text, encoding="utf-8")
    lines = ["| Category | n | Correct |", "|---|---|---|"]
    for c in scoring.CATEGORIES:
        lines.append(f"| {c} | {summary[c + '_n']} | {summary[c + '_rate']:.2f} |")
    lines.append(f"| ALL | {summary['n']} | {summary['overall_rate']:.2f} |")
    (RESULTS / "retrieval_baseline.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    for r in bad:
        print("wrong match:", r["id"], "->", r["matched_id"], f"({r['matched_name']})")


if __name__ == "__main__":
    main()
