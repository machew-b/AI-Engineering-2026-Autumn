"""Turn the result files from the Colab runs into the tables in answer.md.

    uv run python -m app.report            # print the tables
    uv run python -m app.report --write    # also replace the <!-- AUTO:name --> blocks in answer.md
    uv run python -m app.report --check    # list what is still unfinished in answer.md (exit 1 if anything)

Expected files (download them from Colab, see GUIDE.md):
    results/exercise/{result,eval_before,eval_after}.json   from the course notebook (FAQ exercise)
    results/run_a/{result,eval_before,eval_after}.json      from notebooks/lora_glossary_tuning.ipynb, run A
    results/run_b/...                                       optional, same notebook with INCLUDE_ABSTAIN = True
    results/retrieval_baseline.json                         made by `python -m app.retrieval`
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from app.glossary_data import ROOT

RESULTS = ROOT / "results"
ANSWER = ROOT / "answer.md"
NOT_RUN = "_Not run yet._"
# In the course notebook this question is the control (the FAQ does cover it). Its own "FAQ にある" flag is False for it
# because the flag only looks at the 21 test questions, so the role is taken from the question text instead.
CONTROL_QUESTION = "課題の提出期限はいつですか"
CATS = [("seen", "Seen wording"), ("reworded", "New wording"), ("alias", "Alias"),
        ("heldout", "Left out of training"), ("unknown", "Not in glossary (abstain = correct)")]


def load(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def pct(x) -> str:
    return "n/a" if x is None else f"{round(x * 100)}%"


def _cut(text: str, n: int = 60) -> str:
    text = re.sub(r"\s+", " ", text or "").replace("|", "/")
    return text if len(text) <= n else text[: n - 1] + "…"


def comparison_table(results: Path = RESULTS) -> str:
    a, b = load(results / "run_a" / "result.json"), load(results / "run_b" / "result.json")
    ret = load(results / "retrieval_baseline.json")
    cols = [("Base model", (a or b or {}).get("before"))]
    cols.append(("Run A (glossary only)", a and a["after"]))
    cols.append(("Run B (+ abstain examples)", b and b["after"]))
    cols.append(("Glossary search", ret and ret["summary"]))
    if not any(s for _, s in cols[:3]):
        return NOT_RUN
    lines = ["| Question type | n | " + " | ".join(n for n, _ in cols) + " |", "|---|---|" + "---|" * len(cols)]
    ref = next(s for _, s in cols if s)
    for key, label in CATS:
        lines.append(f"| {label} | {ref[key + '_n']} | " + " | ".join(pct(s and s[key + "_rate"]) for _, s in cols) + " |")
    lines.append(f"| Taught terms answered with \"not in glossary\" | {ref['seen_n'] + ref['reworded_n'] + ref['alias_n']} | "
                 + " | ".join(pct(s and s["over_abstain_rate"]) for _, s in cols) + " |")
    lines.append(f"| All questions | {ref['n']} | " + " | ".join(pct(s and s["overall_rate"]) for _, s in cols) + " |")
    return "\n".join(lines)


def training_table(results: Path = RESULTS) -> str:
    rows = []
    for name, label in (("run_a", "A: glossary only"), ("run_b", "B: + abstain examples")):
        r = load(results / name / "result.json")
        if r:
            t, c = r["training"], r["config"]
            loss = "n/a" if t.get("final_loss") is None else f"{t['final_loss']:.3f}"
            rows.append(f"| {label} | {r['data']['train']} | {c['num_train_epochs']} | {t['steps']} | {loss} | {t['seconds']:.0f} | {t.get('trainable', 'n/a')} |")
    if not rows:
        return NOT_RUN
    return "\n".join(["| Run | Training examples | Epochs | Steps | Final loss | Seconds | Trainable parameters |",
                      "|---|---|---|---|---|---|---|", *rows])


def examples_table(results: Path = RESULTS, run: str = "run_a", categories=("heldout", "unknown")) -> str:
    before, after = load(results / run / "eval_before.json"), load(results / run / "eval_after.json")
    if not (before and after):
        return NOT_RUN
    lines = ["| Question | Base model | After training | After: correct? |", "|---|---|---|---|"]
    for b, a in zip(before["rows"], after["rows"]):
        if a["category"] in categories:
            lines.append(f"| {_cut(a['question'], 40)} | {_cut(b['answer'])} | {_cut(a['answer'])} | {'yes' if a['ok'] else 'no'} |")
    return "\n".join(lines)


def exercise_table(results: Path = RESULTS) -> str:
    r = load(results / "exercise" / "result.json")
    if not r:
        return NOT_RUN
    b, a = r["before"], r["after"]
    lines = [f"- Executed training myself: {'yes' if r.get('executed_training_myself') else 'no'}",
             f"- Model and settings: `{r['config']['base_model']}`, {r['method']}, lr {r['config']['lr']}, r {r['config']['lora_r']}, "
             f"alpha {r['config']['lora_alpha']}, {r['config']['num_train_epochs']} epochs, seed {r['config']['seed']}",
             "", "| | Format rate | Content rate | Both |", "|---|---|---|---|",
             f"| Before training | {pct(b['format_rate'])} | {pct(b['content_rate'])} | {pct(b['both_rate'])} |",
             f"| After training | {pct(a['format_rate'])} | {pct(a['content_rate'])} | {pct(a['both_rate'])} |",
             "", f"- Regressed questions (passed before, failed after): {r['regressed'] or 'none'}"]
    if r.get("knowledge"):
        lines += ["", "| Knowledge question | Role | Before | After |", "|---|---|---|---|"]
        for k in r["knowledge"]:
            role = "control (in the FAQ)" if k["質問"] == CONTROL_QUESTION else "not in the FAQ"
            lines.append(f"| {k['質問']} | {role} | {k['学習前の分類']} | {k['学習後の分類']} |")
    return "\n".join(lines)


def blocks(results: Path = RESULTS) -> dict[str, str]:
    return {"exercise": exercise_table(results), "training": training_table(results),
            "comparison": comparison_table(results), "examples": examples_table(results)}


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- AUTO:{name} -->\n).*?(\n<!-- /AUTO:{name} -->)", re.S)
    if not pattern.search(text):
        raise KeyError(f"answer.md has no AUTO:{name} block")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def unresolved(text: str) -> list[str]:
    found = [f"TODO left: {m.group(0)[:70]}" for m in re.finditer(r"TODO\([^)]*\)[^\n]*", text)]
    for m in re.finditer(r"<!-- AUTO:(\w+) -->\n(.*?)\n<!-- /AUTO:\w+ -->", text, re.S):
        if m.group(2).strip() == NOT_RUN and m.group(1) in ("exercise", "training", "comparison"):
            found.append(f"result table '{m.group(1)}' is still empty")
    return found


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    if args.check:
        todo = unresolved(ANSWER.read_text(encoding="utf-8"))
        print("\n".join(todo) if todo else "answer.md has no unfinished parts.")
        return 1 if todo else 0
    out = blocks()
    for name, body in out.items():
        print(f"--- {name} ---\n{body}\n")
    if args.write:
        text = ANSWER.read_text(encoding="utf-8")
        for name, body in out.items():
            text = replace_block(text, name, body)
        ANSWER.write_text(text, encoding="utf-8")
        print("answer.md updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
