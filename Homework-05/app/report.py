"""Turn results/compare/runs.json into the tables in answer.md (and list what is still unfinished).

    uv run python -m app.report --write    # replace the <!-- AUTO:... --> blocks in answer.md
    uv run python -m app.report --check    # list what is still unfinished (exit code 1 if anything is)
    uv run python -m app.report            # print the tables only

Nothing is filled in for a run that was not made: an empty cell says "Not recorded".
Optional: results/compare/judgement.json, {"vector:q1-single:1": "correct", ...} ("correct", "partial" or "wrong"),
is shown in the Judgement column. Correctness is a human judgement; the script never guesses it.
"""
import argparse
import json
import re
import sys
from pathlib import Path

from app.compare import METHODS, QUESTIONS, cited_pages, load, plan, run_id

ROOT = Path(__file__).resolve().parents[1]
ANSWER = ROOT / "answer.md"
JUDGEMENT = ROOT / "results" / "compare" / "judgement.json"
LABEL = {"full-context": "Full context", "vector": "Vector search", "tree": "Tree", "graph": "Graph (course)", "graph2": "Graph v2 (mine)"}
NONE = "Not recorded"
UNSURE = re.compile(r"cannot (verify|confirm|find)|can't (verify|confirm|find)|not (contain|include|provide|available)|no (evidence|information|measurement)|unable to (verify|confirm|find)"
                    r"|記載(は|が)?(さ)?れて(い)?ません|記載はありません|確認できません|見当たりません|含まれていません|載っていません|示されていません", re.I)


def ok_runs(runs: dict, method: str, qid: str) -> list[dict]:
    """Saved runs without an error, in run order. "cited" is re-read from the saved answer with the current parser,
    so a fix to the citation parser applies to runs.json without changing the saved measurements."""
    out = []
    for n in range(1, 10):
        r = runs.get(run_id(method, qid, n))
        if r and not r.get("error"):
            out.append({**r, "cited": cited_pages(r["answer"])})
    return out


def mean(values: list[float]) -> float | None:
    values = [v for v in values if v is not None]
    return sum(values) / len(values) if values else None


def fmt(value, spec: str = ",.0f") -> str:
    return NONE if value is None else format(value, spec)


def gold_counts(rs: list[dict], gold: list, field: str) -> list[int]:
    keys = {tuple(g) for g in gold}
    out = []
    for r in rs:
        got = {tuple(x) for x in (r["cited"] if field == "cited" else r["retrieved"]["full"])}
        out.append(len(keys & got))
    return out


def tool_summary(call: dict) -> str:
    args = call["args"]
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return f"`{call['name']}({args})`"
    return f"`{call['name']}({', '.join(repr(v) for v in args.values())})`"


def table_for(runs: dict, question: dict, judgement: dict) -> str:
    gold = question["gold"]
    n_gold = len(gold)
    head = ("| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) "
            "| Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |\n"
            "|---|---|---|---|---|---|---|---|---|---|---|\n")
    rows = []
    for m in METHODS:
        rs = ok_runs(runs, m, question["id"])
        if not rs:
            rows.append(f"| {LABEL[m]} | 0 | {NONE} | {NONE} | {NONE} | {NONE} | {NONE} | {NONE} | {NONE} | {NONE} | {NONE} |")
            continue
        if not gold:
            received = cited = "no evidence page exists"
            unsure = ", ".join("says it cannot verify" if UNSURE.search(r["answer"]) else "gives an answer" for r in rs)
            cited = unsure
        else:
            received = "all in context" if m == "full-context" else ", ".join(f"{c}/{n_gold}" for c in gold_counts(rs, gold, "received"))
            cited = ", ".join(f"{c}/{n_gold}" for c in gold_counts(rs, gold, "cited"))
        pages = "; ".join(f"L{a} p.{b}" for a, b in rs[0]["cited"]) or "none"
        calls = ", ".join(tool_summary(c) for c in rs[0]["tool_calls"]) or "none"
        cost = mean([r["cost_usd"] for r in rs])
        ids = [run_id(m, question["id"], n) for n in range(1, len(rs) + 1)]
        judged = ", ".join(judgement.get(i) or "not judged" for i in ids)
        rows.append(f"| {LABEL[m]} | {len(rs)} | {received} | {cited} | {pages} | {calls} | {fmt(mean([r['seconds'] for r in rs]), '.2f')} "
                    f"| {fmt(mean([r['input_tokens'] for r in rs]))} / {fmt(mean([r['output_tokens'] for r in rs]))} "
                    f"| {fmt(mean([r['requests'] for r in rs]), '.1f')} | {'Unavailable' if cost is None else format(cost, '.6f')} | {judged} |")
    return head + "\n".join(rows)


def compare_block(runs: dict, judgement: dict) -> str:
    parts = []
    for q in QUESTIONS:
        gold = ", ".join(f"Lecture {a} p.{b}" for a, b in q["gold"]) or "none (the materials cannot answer it)"
        parts.append(f"**{q['id']}**: {q['question']}\nEvidence pages fixed in advance: {gold}\n\n{table_for(runs, q, judgement)}")
    return "\n\n".join(parts)


def answers_block(runs: dict) -> str:
    lines = ["| Question | Method | Answer (run 1, shortened) |", "|---|---|---|"]
    for q in QUESTIONS:
        for m in METHODS:
            rs = ok_runs(runs, m, q["id"])
            text = NONE if not rs else re.sub(r"\s+", " ", rs[0]["answer"]).replace("|", "/")[:220] + ("…" if len(rs[0]["answer"]) > 220 else "")
            lines.append(f"| {q['id']} | {LABEL[m]} | {text} |")
    return "\n".join(lines)


def findings_block(runs: dict) -> str:
    """Plain counts only. What they mean is written by hand in answer.md."""
    out = []
    for q in QUESTIONS:
        if not q["gold"]:
            continue
        n_gold = len(q["gold"])
        parts = []
        for m in ("vector", "graph", "graph2"):
            rs = ok_runs(runs, m, q["id"])
            if rs:
                got = gold_counts(rs, q["gold"], "received")
                parts.append(f"{LABEL[m]} {sum(got)}/{n_gold * len(got)}")
        out.append(f"- {q['id']}: evidence pages received with text, summed over runs: " + ("; ".join(parts) if parts else NONE))
    return "\n".join(out) if out else NONE


def blocks(runs: dict) -> dict[str, str]:
    judgement = json.loads(JUDGEMENT.read_text(encoding="utf-8")) if JUDGEMENT.is_file() else {}
    return {"compare": compare_block(runs, judgement), "answers": answers_block(runs), "findings": findings_block(runs)}


def replace_blocks(text: str, new: dict[str, str]) -> str:
    for name, body in new.items():
        pattern = re.compile(rf"(<!-- AUTO:{name} -->\n).*?(\n<!-- /AUTO:{name} -->)", re.S)
        if not pattern.search(text):
            raise SystemExit(f"answer.md has no AUTO:{name} block")
        text = pattern.sub(lambda m: m.group(1) + body + m.group(2), text)
    return text


def unfinished_lines(text: str) -> list[int]:
    """Line numbers of "Not recorded" and "(fill in after the live runs)" outside the AUTO blocks, i.e. prose to rewrite by hand."""
    lines, inside = [], False
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("<!-- AUTO:"):
            inside = True
        elif line.startswith("<!-- /AUTO:"):
            inside = False
        elif not inside and (NONE in line or "(fill in after the live runs)" in line):
            lines.append(number)
    return lines


def check(runs: dict, text: str) -> list[str]:
    """What is still unfinished. Anything returned here makes --check exit with 1."""
    todo = []
    wanted = plan(METHODS, QUESTIONS, 2, 1)
    missing = [rid for rid, *_ in wanted if rid not in runs]
    failed = [rid for rid, r in runs.items() if r.get("error")]
    if missing:
        todo.append(f"{len(missing)} of {len(wanted)} runs are not made yet (uv run python -m app.compare)")
    if failed:
        todo.append("failed runs (run app.compare again): " + ", ".join(sorted(failed)))
    if NONE in text.split("<!-- AUTO:compare -->")[-1].split("<!-- /AUTO:compare -->")[0] and not missing:
        todo.append(f"the tables still say '{NONE}' (uv run python -m app.report --write)")
    lines = unfinished_lines(text)
    if lines:
        todo.append(f"answer.md lines {', '.join(map(str, lines))} still say '{NONE}' or '(fill in after the live runs)': write them by hand")
    return todo


def optional_notes(runs: dict) -> list[str]:
    judgement = json.loads(JUDGEMENT.read_text(encoding="utf-8")) if JUDGEMENT.is_file() else {}
    unjudged = [rid for rid, r in runs.items() if not r.get("error") and not judgement.get(rid)]
    return [f"optional: {len(unjudged)} runs have no entry in results/compare/judgement.json (shown as 'not judged')"] if unjudged else []


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    runs = load()
    if args.write:
        ANSWER.write_text(replace_blocks(ANSWER.read_text(encoding="utf-8"), blocks(runs)), encoding="utf-8")
        print(f"wrote the tables into {ANSWER.name}")
    if args.check:
        todo = check(runs, ANSWER.read_text(encoding="utf-8"))
        print("\n".join(f"- {t}" for t in todo) if todo else "nothing unfinished")
        print("\n".join(f"- {t}" for t in optional_notes(runs)))
        sys.exit(1 if todo else 0)
    if not args.write:
        for name, body in blocks(runs).items():
            print(f"## {name}\n{body}\n")


if __name__ == "__main__":
    main()
