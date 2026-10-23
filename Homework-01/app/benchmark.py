"""Homework 1, Advanced level: measure response time and tokens across models and questions.

What it does
    For every model and question it sends the question several times, one at a time,
    and records the response time and the input / output / thinking token counts.
    Requests are paced to stay under the free-tier requests-per-minute limits, and
    failures (429, 503, empty answers) are recorded as rows, never hidden.

Usage
    uv run python -m app.benchmark --dry-run              # show the plan, send nothing
    uv run python -m app.benchmark                        # default plan
    uv run python -m app.benchmark --models gemini-3.5-flash-lite:3 gemini-3.8-flash:2 --retries 2
    uv run python -m app.benchmark --questions general-short course-specific

Output (in results/, one set per run): benchmark_<time>.csv, .json (with the answers), summary.md

Notes
    * Response time is wall-clock time of the API call only. It includes network time
      and the server's queueing and thinking time, and excludes the pacing sleeps.
    * Output tokens are the visible answer. Thinking tokens are reported separately.
    * The limits below are the ones measured in class (Lecture 1 slides). They can
      change, so check AI Studio for your own key's current limits.
"""

import argparse
import csv
import json
import re
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import errors

from app.ask import TokenUsage
from app.config import api_error_message, get_api_key

QUESTIONS = {
    "general-short": "What is LoRA?",
    "course-specific": "In the AIE2026 course homework, what are the '3 levels'?",
    "long-answer": "Explain the difference between LoRA and QLoRA, with a short example of when to use each.",
}

# model -> (requests per minute, requests per day), as measured in class. None = unknown.
# gemini-3.8-flash is "about 10-20 per day", so the conservative 10 is used for warnings.
KNOWN_LIMITS = {
    "gemini-3.5-flash-lite": (15, 500),
    "gemini-3.8-flash": (5, 10),
}
DEFAULT_RPM = 10  # for models not listed above
PACING_MARGIN_S = 1.0  # extra seconds on top of 60 / rpm

DEFAULT_MODELS = ["gemini-3.5-flash-lite:3", "gemini-3.8-flash:2"]
RETRYABLE = (429, 503)
# Google API keys: the older format starts with "AIza", newer ones start with "AQ."
KEY_PATTERN = re.compile(r"AIza[0-9A-Za-z_\-]{35}|AQ\.[0-9A-Za-z_\-]{20,}")

CSV_FIELDS = [
    "timestamp_utc",
    "model",
    "question_id",
    "run",
    "ok",
    "attempts",
    "status_code",
    "latency_s",
    "input_tokens",
    "output_tokens",
    "thinking_tokens",
    "answer_chars",
    "error",
]


@dataclass
class Row:
    timestamp_utc: str
    model: str
    question_id: str
    run: int
    ok: bool
    attempts: int
    status_code: int | None
    latency_s: float | None
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    answer_chars: int
    error: str
    answer: str


# ---------- planning ----------


def parse_model_spec(spec: str, default_runs: int) -> tuple[str, int]:
    """'gemini-3.8-flash:2' -> ('gemini-3.8-flash', 2). Without ':N', default_runs is used."""
    name, sep, runs = spec.partition(":")
    if not name:
        raise ValueError(f"empty model name in {spec!r}")
    if not sep:
        return name, default_runs
    if not runs.isdigit() or int(runs) < 1:
        raise ValueError(f"runs must be a positive integer in {spec!r}")
    return name, int(runs)


def min_interval(model: str, override: float | None = None) -> float:
    """Minimum seconds between the starts of two requests to the same model."""
    if override is not None:
        return override
    rpm = KNOWN_LIMITS.get(model, (DEFAULT_RPM, None))[0]
    return 60.0 / rpm + PACING_MARGIN_S


def plan_warnings(specs: list[tuple[str, int]], n_questions: int) -> list[str]:
    warnings = []
    for model, runs in specs:
        _, per_day = KNOWN_LIMITS.get(model, (None, None))
        requests = runs * n_questions
        if per_day is not None and requests > per_day:
            warnings.append(f"{model}: {requests} requests planned but the daily limit is about {per_day}")
        elif per_day is not None and requests > per_day * 0.5:
            warnings.append(f"{model}: {requests} requests planned, over half of the daily limit (about {per_day})")
    return warnings


def describe_plan(specs, questions) -> str:
    lines = ["Plan:"]
    for model, runs in specs:
        n = runs * len(questions)
        lines.append(
            f"  {model}: {runs} run(s) x {len(questions)} question(s) = {n} requests, "
            f"at least {min_interval(model):.0f}s apart (about {n * min_interval(model) / 60:.1f} min)"
        )
    return "\n".join(lines)


# ---------- running ----------


def _clean_error(text: str, limit: int = 200) -> str:
    text = KEY_PATTERN.sub("[REDACTED]", " ".join(str(text).split()))
    return text if len(text) <= limit else text[: limit - 3] + "..."


def run_benchmark(
    client,
    specs: list[tuple[str, int]],
    questions: dict[str, str],
    *,
    interval_override: float | None = None,
    retries: int = 0,
    retry_wait: float = 20.0,
    max_consecutive_failures: int = 3,
    clock=time.perf_counter,
    sleep=time.sleep,
    log=print,
) -> list[Row]:
    """Send every question `runs` times to every model. Returns one Row per request."""
    rows: list[Row] = []
    for model, runs in specs:
        interval = min_interval(model, interval_override)
        last_start: float | None = None
        consecutive_failures = 0

        for run in range(1, runs + 1):
            for qid, text in questions.items():  # run-major order spreads time effects across questions
                stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

                if consecutive_failures >= max_consecutive_failures:
                    msg = f"skipped after {consecutive_failures} failures in a row"
                    rows.append(Row(stamp, model, qid, run, False, 0, None, None, 0, 0, 0, 0, msg, ""))
                    log(f"  {model} {qid} run {run}: {msg}")
                    continue

                attempts = 0
                while True:
                    attempts += 1
                    if last_start is not None:
                        wait = interval - (clock() - last_start)
                        if wait > 0:
                            sleep(wait)
                    last_start = clock()
                    try:
                        response = client.models.generate_content(model=model, contents=text)
                        latency = clock() - last_start
                    except errors.APIError as e:
                        if e.code in RETRYABLE and attempts <= retries:
                            log(f"  {model} {qid} run {run}: {e.code}, retrying in {retry_wait:.0f}s")
                            sleep(retry_wait)
                            continue
                        rows.append(
                            Row(stamp, model, qid, run, False, attempts, e.code, None, 0, 0, 0, 0,
                                _clean_error(f"{e.code}: {e.message}"), "")
                        )
                        log(f"  {model} {qid} run {run}: FAILED ({api_error_message(e.code, '')})")
                        consecutive_failures += 1
                        break

                    usage = TokenUsage.from_metadata(response.usage_metadata)
                    answer = response.text or ""
                    ok = bool(answer)
                    rows.append(
                        Row(stamp, model, qid, run, ok, attempts, None, round(latency, 3),
                            usage.input, usage.output, usage.thinking, len(answer),
                            "" if ok else "empty response", answer)
                    )
                    consecutive_failures = 0 if ok else consecutive_failures + 1
                    log(
                        f"  {model} {qid} run {run}: {latency:.2f}s, {usage.describe()}"
                        + ("" if ok else "  (empty response)")
                    )
                    break
    return rows


# ---------- summarizing ----------


def _mean(values):
    return statistics.fmean(values) if values else None


def summarize(rows: list[Row]) -> list[dict]:
    """One line per (model, question) plus one 'ALL' line per model."""
    out = []
    models = list(dict.fromkeys(r.model for r in rows))
    for model in models:
        model_rows = [r for r in rows if r.model == model]
        groups = [(qid, [r for r in model_rows if r.question_id == qid])
                  for qid in dict.fromkeys(r.question_id for r in model_rows)]
        groups.append(("ALL", model_rows))
        for qid, group in groups:
            good = [r for r in group if r.ok]
            lat = [r.latency_s for r in good]
            out_tok = [r.output_tokens for r in good]
            rate = [r.output_tokens / r.latency_s for r in good if r.latency_s]
            out.append(
                {
                    "model": model,
                    "question": qid,
                    "requests": len(group),
                    "ok": len(good),
                    "http_429": sum(1 for r in group if r.status_code == 429),
                    "http_503": sum(1 for r in group if r.status_code == 503),
                    "latency_mean": _mean(lat),
                    "latency_median": statistics.median(lat) if lat else None,
                    "latency_min": min(lat) if lat else None,
                    "latency_max": max(lat) if lat else None,
                    "input_mean": _mean([r.input_tokens for r in good]),
                    "output_mean": _mean(out_tok),
                    "thinking_mean": _mean([r.thinking_tokens for r in good]),
                    "out_tokens_per_s": _mean(rate),
                }
            )
    return out


def _fmt(value, digits=1):
    return "n/a" if value is None else f"{value:.{digits}f}"


def to_markdown(summary: list[dict]) -> str:
    header = (
        "| Model | Question | OK / requests | 429 | 503 | Latency mean (s) | median | min | max "
        "| Input tokens | Output tokens | Thinking tokens | Output tokens/s |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    lines = []
    for s in summary:
        lines.append(
            f"| {s['model']} | {s['question']} | {s['ok']} / {s['requests']} | {s['http_429']} | {s['http_503']} "
            f"| {_fmt(s['latency_mean'], 2)} | {_fmt(s['latency_median'], 2)} | {_fmt(s['latency_min'], 2)} "
            f"| {_fmt(s['latency_max'], 2)} | {_fmt(s['input_mean'])} | {_fmt(s['output_mean'])} "
            f"| {_fmt(s['thinking_mean'])} | {_fmt(s['out_tokens_per_s'])} |"
        )
    return header + "\n".join(lines) + "\n"


def write_results(rows: list[Row], out_dir: Path, stamp: str) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / f"benchmark_{stamp}.csv"
    json_path = out_dir / f"benchmark_{stamp}.json"
    md_path = out_dir / f"summary_{stamp}.md"

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(asdict(r) for r in rows)
    json_path.write_text(json.dumps([asdict(r) for r in rows], ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(summarize(rows)), encoding="utf-8")
    return [csv_path, json_path, md_path]


# ---------- command line ----------


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure response time and tokens across models and questions")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, metavar="MODEL[:RUNS]",
                        help="models to test, each optionally followed by :RUNS (default: %(default)s)")
    parser.add_argument("--runs", type=int, default=3, help="runs for models given without :RUNS")
    parser.add_argument("--questions", nargs="+", choices=list(QUESTIONS), default=list(QUESTIONS))
    parser.add_argument("--retries", type=int, default=0, help="retries on 429/503 (default 0: record the failure)")
    parser.add_argument("--retry-wait", type=float, default=20.0, help="seconds to wait before a retry")
    parser.add_argument("--min-interval", type=float, default=None,
                        help="override the pacing (seconds between requests to one model)")
    parser.add_argument("--stop-after", type=int, default=3, metavar="N",
                        help="skip the rest of a model after N failures in a row (protects the daily quota)")
    parser.add_argument("--out-dir", type=Path, default=Path("results"))
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit without calling the API")
    args = parser.parse_args()

    try:
        specs = [parse_model_spec(m, args.runs) for m in args.models]
    except ValueError as e:
        parser.error(str(e))
    questions = {qid: QUESTIONS[qid] for qid in args.questions}

    print(describe_plan(specs, questions))
    for warning in plan_warnings(specs, len(questions)):
        print(f"  WARNING: {warning}")
    if args.dry_run:
        return

    client = genai.Client(api_key=get_api_key())
    started = time.perf_counter()
    rows = run_benchmark(
        client, specs, questions,
        interval_override=args.min_interval, retries=args.retries,
        retry_wait=args.retry_wait, max_consecutive_failures=args.stop_after,
    )
    wall = time.perf_counter() - started

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = write_results(rows, args.out_dir, stamp)
    print(f"\nFinished {len(rows)} request(s) in {wall:.0f}s.\n")
    print(to_markdown(summarize(rows)))
    print("Saved:")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
