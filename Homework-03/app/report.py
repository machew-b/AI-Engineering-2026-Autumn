"""Turn results/compare/runs.json (made by app.compare) into the tables in answer.md.

    uv run python -m app.report            # print the tables
    uv run python -m app.report --write    # also replace the <!-- AUTO:name --> blocks in answer.md
    uv run python -m app.report --check    # list what is still unfinished in answer.md (exit 1 if anything)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from statistics import mean

from app.compare import QUESTIONS

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "compare" / "runs.json"
ANSWER = ROOT / "answer.md"
NOT_RUN = "_Not run yet._"
LABELS = {"bare": "Bare model (Lecture 1)", "pydantic": "Pydantic AI agent", "adk": "ADK agent"}


def load_runs(path: Path = RUNS) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def _ok(runs, system, qid):
    return sorted((r for r in runs if r["system"] == system and r["question_id"] == qid and not r.get("error")),
                  key=lambda r: r["run"])


def _cut(text: str, n: int = 90) -> str:
    text = re.sub(r"\s+", " ", text or "").replace("|", "/")
    return text if len(text) <= n else text[: n - 1] + "…"


def fmt_calls(calls: list[dict]) -> str:
    if not calls:
        return "none"
    return ", ".join(f"`{c['tool']}({', '.join(repr(v) for v in c['args'].values())})`" for c in calls).replace("|", "/")


def _num(values, digits=0):
    return "n/a" if not values else f"{mean(values):.{digits}f}"


def exercise_table(runs: list[dict]) -> str:
    """Exercise steps 2, 3 and 5: the bare model against the agent, the trace, and the request counts."""
    if not runs:
        return NOT_RUN
    lines = ["| Question | System | Tool calls (run 1) | LLM requests per run | Answer (run 1, shortened) |", "|---|---|---|---|---|"]
    for qid, question, _ in QUESTIONS[:3]:
        for system in ("bare", "pydantic"):
            rs = _ok(runs, system, qid)
            if not rs:
                continue
            reqs = "/".join(str(r["requests"]) for r in rs)
            lines.append(f"| {_cut(question, 45)} | {LABELS[system]} | {fmt_calls(rs[0]['tool_calls'])} | {reqs} | {_cut(rs[0]['answer'])} |")
    return "\n".join(lines) if len(lines) > 2 else NOT_RUN


def comparison_table(runs: list[dict]) -> str:
    """Pydantic AI against ADK, same instructions and tools, question by question."""
    rows = []
    for qid, question, _ in QUESTIONS:
        p, a = _ok(runs, "pydantic", qid), _ok(runs, "adk", qid)
        if not (p and a):
            continue
        same = "yes" if all([c["tool"] for c in x["tool_calls"]] == [c["tool"] for c in y["tool_calls"]] for x, y in zip(p, a)) else "no"
        rows.append(f"| {qid} | {fmt_calls(p[0]['tool_calls'])} | {fmt_calls(a[0]['tool_calls'])} | {same} "
                    f"| {_num([r['requests'] for r in p], 1)} | {_num([r['requests'] for r in a], 1)} "
                    f"| {_num([r['seconds'] for r in p], 1)} | {_num([r['seconds'] for r in a], 1)} "
                    f"| {_num([r['input_tokens'] for r in p])} / {_num([r['output_tokens'] for r in p])} "
                    f"| {_num([r['input_tokens'] for r in a])} / {_num([r['output_tokens'] for r in a])} |")
    if not rows:
        return NOT_RUN
    head = ["| Question | Pydantic AI tool calls (run 1) | ADK tool calls (run 1) | Same tool order in every run | Requests (Pydantic AI, mean) | Requests (ADK, mean) "
            "| Seconds (Pydantic AI, mean) | Seconds (ADK, mean) | Tokens in / out (Pydantic AI, mean) | Tokens in / out (ADK, mean) |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    return "\n".join(head + rows)


def answers_table(runs: list[dict]) -> str:
    rows = []
    for qid, question, _ in QUESTIONS:
        p, a = _ok(runs, "pydantic", qid), _ok(runs, "adk", qid)
        if p and a:
            rows.append(f"| {qid} | {_cut(p[0]['answer'], 110)} | {_cut(a[0]['answer'], 110)} |")
    if not rows:
        return NOT_RUN
    return "\n".join(["| Question | Pydantic AI answer (run 1, shortened) | ADK answer (run 1, shortened) |", "|---|---|---|", *rows])


def blocks(runs: list[dict] | None = None) -> dict[str, str]:
    runs = load_runs() if runs is None else runs
    return {"exercise": exercise_table(runs), "comparison": comparison_table(runs), "answers": answers_table(runs)}


def replace_block(text: str, name: str, body: str) -> str:
    pattern = re.compile(rf"(<!-- AUTO:{name} -->\n).*?(\n<!-- /AUTO:{name} -->)", re.S)
    if not pattern.search(text):
        raise KeyError(f"answer.md has no AUTO:{name} block")
    return pattern.sub(lambda m: m.group(1) + body + m.group(2), text)


def unresolved(text: str) -> list[str]:
    found = [f"TODO left: {m.group(0)[:70]}" for m in re.finditer(r"TODO\([^)]*\)[^\n]*", text)]
    for m in re.finditer(r"<!-- AUTO:(\w+) -->\n(.*?)\n<!-- /AUTO:\w+ -->", text, re.S):
        if m.group(2).strip() == NOT_RUN:
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
