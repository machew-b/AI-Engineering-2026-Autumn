"""Scoring for the glossary questions. Standard library only (it also runs inside Colab).

Two kinds of gold answer:
  definition: every phrase in must_include appears in the answer.
  abstain:    the answer says the term is not in the glossary / needs checking.
The check is lexical on purpose (cheap and repeatable). It can miss a correct paraphrase, so read the
answers in eval_*.json as well, not only the rates.
"""
from __future__ import annotations

import re
import time
import unicodedata
from typing import Callable

CATEGORIES = ("seen", "reworded", "alias", "heldout", "unknown")
ABSTAIN_MARKERS = ("記載がありません", "記載されていません", "載っていません", "確認が必要", "分かりません", "わかりません", "知りません")


def clean_answer(text: str) -> str:
    """Drop a <think>...</think> block if the model produced one, then trim."""
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def normalize(text: str) -> str:
    """NFKC, lower case, no whitespace, so 'adk web' and 'ADK　Web' compare equal."""
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text or "")).casefold()


def is_abstain(text: str) -> bool:
    norm = normalize(clean_answer(text))
    return any(normalize(m) in norm for m in ABSTAIN_MARKERS)


def score_answer(answer: str, gold: dict) -> dict:
    cleaned = clean_answer(answer)
    norm = normalize(cleaned)
    abstained = is_abstain(cleaned)
    if gold["kind"] == "abstain":
        ok = abstained
    else:
        ok = bool(gold["must_include"]) and all(normalize(p) in norm for p in gold["must_include"])
    return {"ok": ok, "abstained": abstained}


def _rate(rows: list[dict], key: str = "ok") -> float | None:
    return round(sum(1 for r in rows if r[key]) / len(rows), 4) if rows else None


def summarize(rows: list[dict], label: str = "", seconds: float | None = None) -> dict:
    out: dict = {"label": label, "n": len(rows)}
    for c in CATEGORIES:
        sub = [r for r in rows if r["category"] == c]
        out[f"{c}_n"] = len(sub)
        out[f"{c}_rate"] = _rate(sub)          # for "unknown" this is the share that abstained (desired)
    known = [r for r in rows if r["category"] in ("seen", "reworded", "alias")]
    out["known_rate"] = _rate(known)           # terms the model was taught: seen + reworded + alias
    out["over_abstain_rate"] = _rate(known, "abstained")   # taught terms answered with "not in the glossary"
    unknown = [r for r in rows if r["category"] == "unknown"]
    out["unknown_asserted_rate"] = None if not unknown else round(1 - _rate(unknown), 4)
    out["overall_rate"] = _rate(rows)
    if seconds is not None:
        out["seconds"] = round(seconds, 1)
    return out


def evaluate(generate: Callable[[str], str], test: list[dict], gold: dict, label: str = "") -> tuple[dict, list[dict]]:
    """Ask every test question with `generate(question) -> answer text` and score it."""
    t0 = time.time()
    rows = []
    for item in test:
        answer = generate(item["question"])
        rows.append({"id": item["id"], "category": item["category"], "question": item["question"],
                     "answer": answer, **score_answer(answer, gold[item["id"]])})
    return summarize(rows, label, time.time() - t0), rows
