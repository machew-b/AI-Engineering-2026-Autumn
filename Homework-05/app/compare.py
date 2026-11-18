"""Live comparison for Homework 5: the same questions through full context, vector search, Tree, Graph and Graph v2.

Needs GEMINI_API_KEY (generation and query embedding) and the course data (scripts/fetch_course_data.py).
Every run is saved to results/compare/runs.json as soon as it finishes; running the command again skips runs
that are already saved, so an interruption (or a 429) costs nothing.

    uv run python -m app.compare --dry-run                 # show the plan, send nothing
    uv run python -m app.compare                           # everything (36 runs, roughly 80 to 100 requests, about 20 cents)
    uv run python -m app.compare --methods vector graph2 --questions q2-multi   # a subset
"""
import argparse
import json
import re
import time
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ToolCallPart, ToolReturnPart

from app import agent as agent_module
from app import tools
from app.config import MODEL

RESULTS = Path(__file__).resolve().parents[1] / "results" / "compare" / "runs.json"

# Questions 1 to 3 are the course's own (problem.md). Question 4 is mine: it needs three pages from two lectures.
# gold = the evidence pages (lecture, PDF page) fixed before any run. q3 has none: the materials cannot answer it.
QUESTIONS = [
    {"id": "q1-single", "gold": [[2, 52]],
     "question": "In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?"},
    {"id": "q2-multi", "gold": [[3, 13], [3, 39], [3, 40]],
     "question": "In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory?"},
    {"id": "q3-absent", "gold": [],
     "question": "What are the measured average response time and accuracy of the RAG system we just built?"},
    {"id": "q4-cross-lecture", "gold": [[1, 49], [2, 46], [2, 47]],
     "question": "Why does Lecture 02 recommend RAG instead of fine-tuning for adding knowledge, and how does the course chatbot example in Lecture 01 apply RAG?"},
]
METHODS = ["full-context", "vector", "tree", "graph", "graph2"]
CITATION = re.compile(r"Lecture\s*0*(\d+)\s*/\s*(?:PDF\s*)?p\.?\s*(\d+)", re.IGNORECASE)
PAGE_ID = re.compile(r"^lec(\d+)-main-p(\d+)$")
WAITS = {429: 65, 503: 20}


def cited_pages(answer: str) -> list[list[int]]:
    """Every "Lecture N / PDF p.N" in the answer, as [lecture, page], without duplicates, in order."""
    seen, out = set(), []
    for lecture, page in CITATION.findall(answer or ""):
        key = (int(lecture), int(page))
        if key not in seen:
            seen.add(key)
            out.append(list(key))
    return out


def _key(page_id: str) -> list[int] | None:
    m = PAGE_ID.match(page_id or "")
    return [int(m.group(1)), int(m.group(2))] if m else None


def retrieved_pages(tool_returns: list[tuple[str, str]]) -> dict[str, list[list[int]]]:
    """Pages the model actually received, from the tool results: "full" (body text) and "listed" (title only).

    This separates "the evidence never reached the model" from "it reached the model and was not used"."""
    full, listed = {}, {}
    for name, content in tool_returns:
        try:
            data = json.loads(content)
        except (TypeError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        if name == "search_materials":
            items = [("full", x) for x in data.get("results", [])]
        elif name in ("search_graph", "search_graph_v2"):
            items = [("full", x) for k in ("seeds", "expanded") for x in data.get(k, [])]
            items += [("listed", x) for x in data.get("more", [])]
        elif name == "read_page":
            items = [("full", data)]
        elif name == "browse_tree":
            node = data.get("node", {})
            items = [("full", {"page_id": node.get("id")})] if node.get("kind") == "page" else []
            items += [("listed", {"page_id": c.get("id")}) for c in data.get("children", []) if c.get("kind") == "page"]
        else:
            items = []
        for kind, item in items:
            key = _key(item.get("page_id") or item.get("id") or "")
            if key:
                (full if kind == "full" else listed)[tuple(key)] = key
    listed_only = [v for k, v in listed.items() if k not in full]
    return {"full": sorted(full.values()), "listed": sorted(listed_only)}


def make_mode(method: str):
    a = agent_module
    if method == "tree":
        return a.agent.override(instructions=a.TREE_INSTRUCTIONS, tools=[tools.browse_tree])
    if method == "graph":
        return a.agent.override(instructions=a.GRAPH_INSTRUCTIONS, tools=[tools.search_graph])
    if method == "graph2":
        return a.agent.override(instructions=a.GRAPH2_INSTRUCTIONS, tools=[tools.search_graph_v2, tools.read_page])
    if method == "full-context":
        return a.agent.override(instructions=a.FULL_CONTEXT_INSTRUCTIONS, tools=[])
    return nullcontext()  # vector search: the agent as it is


def run_once(method: str, question: dict, model_factory=None) -> dict:
    """One run. Returns the record that is saved; never raises on a model error."""
    from app.retrieval import get_all_materials
    model_factory = model_factory or agent_module.build_model
    prompt = question["question"]
    if method == "full-context":
        prompt = agent_module.FULL_CONTEXT_PROMPT.format(materials=get_all_materials(), question=question["question"])
    record = {"method": method, "question_id": question["id"], "model": MODEL,
              "time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "error": None, "attempts": 0}
    for attempt in range(1, 4):
        record["attempts"] = attempt
        started = time.perf_counter()
        try:
            with make_mode(method):
                result = agent_module.agent.run_sync(prompt, model=model_factory())
        except ModelHTTPError as e:
            record["error"] = f"HTTP {e.status_code}"
            if e.status_code in WAITS and attempt < 3:
                time.sleep(WAITS[e.status_code])
                continue
            return record
        except Exception as e:  # a failed run is recorded, not hidden
            record["error"] = f"{type(e).__name__}: {str(e)[:200]}"
            return record
        seconds = time.perf_counter() - started
        parts = [p for m in result.all_messages() for p in m.parts]
        calls = [{"name": p.tool_name, "args": p.args if isinstance(p.args, (dict, str)) else str(p.args)}
                 for p in parts if isinstance(p, ToolCallPart)]
        returns = [(p.tool_name, p.content if isinstance(p.content, str) else json.dumps(p.content, default=str))
                   for p in parts if isinstance(p, ToolReturnPart)]
        usage = result.usage() if callable(result.usage) else result.usage
        answer = str(result.output)
        record.update({
            "error": None, "answer": answer, "tool_calls": calls, "cited": cited_pages(answer),
            "retrieved": retrieved_pages(returns), "seconds": round(seconds, 2),
            "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens, "requests": usage.requests,
            "cost_usd": float(usage.cost) if usage.cost is not None else None,
        })
        return record
    return record


def run_id(method: str, qid: str, n: int) -> str:
    return f"{method}:{qid}:{n}"


def load(path: Path = RESULTS) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def save(runs: dict, path: Path = RESULTS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(runs, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")


def plan(methods, questions, runs, full_runs):
    """(run id, method, question, run number) for every run that is wanted and not saved yet."""
    todo = []
    for q in questions:
        for m in methods:
            for n in range(1, (full_runs if m == "full-context" else runs) + 1):
                todo.append((run_id(m, q["id"], n), m, q, n))
    return todo


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=METHODS)
    parser.add_argument("--questions", nargs="+", choices=[q["id"] for q in QUESTIONS], default=[q["id"] for q in QUESTIONS])
    parser.add_argument("--runs", type=int, default=2, help="runs per question for the retrieval methods")
    parser.add_argument("--full-runs", type=int, default=1, help="runs per question for full context (about 117k input tokens each)")
    parser.add_argument("--pause", type=float, default=6.0, help="seconds between runs (free-tier rate limit)")
    parser.add_argument("--redo", action="store_true", help="run again even if a run is saved")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    saved = load()
    todo = plan(args.methods, [q for q in QUESTIONS if q["id"] in args.questions], args.runs, args.full_runs)
    pending = [t for t in todo if args.redo or t[0] not in saved or saved[t[0]].get("error")]
    print(f"[model] {MODEL}\n{len(todo)} runs wanted, {len(todo) - len(pending)} already saved, {len(pending)} to run")
    if args.dry_run:
        for rid, *_ in pending:
            print("  ", rid)
        return
    for i, (rid, method, question, _) in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] {rid} ...", flush=True)
        saved[rid] = run_once(method, question)
        save(saved)
        r = saved[rid]
        print("   ", r["error"] or f"{r['seconds']} s, {r['input_tokens']:,} in / {r['output_tokens']:,} out, cited {r['cited']}")
        if i < len(pending):
            time.sleep(args.pause)


if __name__ == "__main__":
    main()
