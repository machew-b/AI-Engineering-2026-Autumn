"""Run the same questions through the bare model, the Pydantic AI agent and the ADK agent, and save what happened.

    uv run --group adk python -m app.compare --dry-run          # show the plan, send nothing
    uv run --group adk python -m app.compare                    # all questions, all three systems, 2 runs each
    uv run --group adk python -m app.compare --systems pydantic --questions quiz --repeat 1

For every run it records the answer, which tools were called with which arguments, how many LLM requests were made
(the `requests` of the exercise), the token counts and the wall-clock time. Results go to results/compare/runs.json.
Running again replaces the runs with the same key, so a failed run can be repeated without losing the others.
No key is written anywhere; GEMINI_API_KEY is only read from the environment.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from app.config import MODEL

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "compare"

# id, question, why it is in the set
QUESTIONS = [
    ("levels", "What are the 3 homework levels in the AIE2026 course?", "exercise step 2: course-specific, answer is in the glossary"),
    ("lora-qlora", "What is the difference between LoRA and QLoRA?", "exercise step 3: two terms, so the tool should be called twice"),
    ("quiz", "Give me one review question from Lecture 02", "exercise step 5: should call make_quiz with lecture 2"),
    ("summary", "What will we learn in Lecture 03?", "should call get_lecture_summary"),
    ("unknown", "What is a vector database?", "not in the glossary: should say so instead of guessing"),
]
SYSTEMS = ("bare", "pydantic", "adk")
RETRY_WAITS = {429: 65, 503: 20}   # seconds to wait before trying again, by HTTP status
MAX_ATTEMPTS = 3


def run_key(system: str, question_id: str, run: int) -> str:
    return f"{system}:{question_id}:{run}"


# ---------------------------------------------------------------- the three systems

def run_bare(question: str) -> dict:
    """The Lecture 01 call: one request to the model, no tools."""
    from app.ask import ask_with_usage

    text, counts = ask_with_usage(question)
    return {"answer": text, "tool_calls": [], "requests": 1, **counts}


def run_pydantic(question: str, model=None) -> dict:
    """The exercise agent (app/agent.py). `model` is only passed by the offline tests."""
    from app.agent import agent, build_model, summarize_run

    return summarize_run(agent.run_sync(question, model=model or build_model()))


def run_adk(question: str, model=None) -> dict:
    """The same agent built with ADK (adk_agent/glossary_agent/agent.py), run in code instead of with `adk run`.

    LLM requests are counted as the model's own events (a tool-call event or the final answer); the tool result
    events are authored by the program, not the model.
    """
    from adk_agent.glossary_agent.agent import root_agent

    target = root_agent.clone(update={"model": model}) if model is not None else root_agent
    return asyncio.run(_run_adk(target, question))


async def _run_adk(target, question: str) -> dict:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    runner = InMemoryRunner(agent=target, app_name="glossary_agent")
    session = await runner.session_service.create_session(app_name="glossary_agent", user_id="student")
    message = types.Content(role="user", parts=[types.Part(text=question)])
    calls, answer, requests, tokens_in, tokens_out = [], [], 0, 0, 0
    async for event in runner.run_async(user_id="student", session_id=session.id, new_message=message):
        if event.partial:
            continue
        is_model_turn = bool(event.content) and event.content.role == "model"
        if is_model_turn:
            requests += 1
        usage = event.usage_metadata
        if usage:
            tokens_in += usage.prompt_token_count or 0
            tokens_out += usage.candidates_token_count or 0
        for fc in event.get_function_calls():
            calls.append({"tool": fc.name, "args": dict(fc.args or {})})
        if is_model_turn and event.is_final_response() and event.content.parts:
            answer.extend(p.text for p in event.content.parts if getattr(p, "text", None) and not getattr(p, "thought", False))
    return {"answer": "".join(answer).strip(), "tool_calls": calls, "requests": requests,
            "input_tokens": tokens_in, "output_tokens": tokens_out}


RUNNERS = {"bare": run_bare, "pydantic": run_pydantic, "adk": run_adk}


# ---------------------------------------------------------------- running, retrying, saving

def _status_of(exc: BaseException) -> int | None:
    for attr in ("status_code", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    text = f"{type(exc).__name__} {exc}"
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        return 429
    if "503" in text or "UNAVAILABLE" in text:
        return 503
    return None


def execute(system: str, question: str, runner=None, sleep=time.sleep) -> dict:
    """Run one question on one system. Rate-limit (429) and overload (503) errors are retried; anything else is recorded."""
    runner = runner or RUNNERS[system]
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            out = runner(question)
            return {**out, "seconds": round(time.perf_counter() - started, 2), "attempts": attempt, "error": None}
        except SystemExit as exc:                      # get_api_key() exits when the key is missing
            return {"error": f"stopped: {exc}", "attempts": attempt}
        except Exception as exc:  # noqa: BLE001  (every failure is recorded, none is hidden)
            last_error = f"{type(exc).__name__}: {str(exc)[:200]}"
            wait = RETRY_WAITS.get(_status_of(exc))
            if wait is None or attempt == MAX_ATTEMPTS:
                break
            print(f"  {last_error[:80]} ... waiting {wait} s before attempt {attempt + 1}")
            sleep(wait)
    return {"error": last_error, "attempts": attempt}


def load_runs(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def merge_runs(old: list[dict], new: list[dict]) -> list[dict]:
    keys = {r["key"] for r in new}
    return [r for r in old if r["key"] not in keys] + new


def plan(systems, question_ids, repeat) -> list[tuple[str, str, str, int]]:
    questions = {qid: q for qid, q, _ in QUESTIONS}
    return [(s, qid, questions[qid], n) for qid in question_ids for n in range(1, repeat + 1) for s in systems]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--systems", nargs="+", choices=SYSTEMS, default=list(SYSTEMS))
    p.add_argument("--questions", nargs="+", choices=[q[0] for q in QUESTIONS], default=[q[0] for q in QUESTIONS])
    p.add_argument("--repeat", type=int, default=2, help="runs per question and system (default 2)")
    p.add_argument("--pause", type=float, default=6.0, help="seconds between runs, to stay under the free-tier limits")
    p.add_argument("--out", type=Path, default=OUT_DIR)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    steps = plan(args.systems, args.questions, args.repeat)
    expected = sum(1 if s == "bare" else 3 for s, *_ in steps)
    print(f"[model] {MODEL}\n{len(steps)} runs, about {expected} LLM requests, pause {args.pause:g} s between runs")
    if args.dry_run:
        for system, qid, question, n in steps:
            print(f"  {run_key(system, qid, n):26s} {question}")
        return 0

    path = args.out / "runs.json"
    args.out.mkdir(parents=True, exist_ok=True)
    stored = load_runs(path)
    fresh = []
    for i, (system, qid, question, n) in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {run_key(system, qid, n)}")
        result = execute(system, question)
        fresh.append({"key": run_key(system, qid, n), "system": system, "question_id": qid, "question": question,
                      "run": n, "model": MODEL, "at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), **result})
        if result.get("error"):
            print(f"  FAILED: {result['error']}")
        path.write_text(json.dumps(merge_runs(stored, fresh), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if i < len(steps):
            time.sleep(args.pause)
    failed = [r["key"] for r in fresh if r.get("error")]
    print(f"saved {path}" + (f"; failed runs: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
