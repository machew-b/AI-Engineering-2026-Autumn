"""The live runner (app/compare.py), checked offline: planning, retries, failure recording, merging, the Pydantic AI path."""
import json

import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models.test import TestModel

from app import compare


def test_plan_covers_every_question_system_and_run():
    steps = compare.plan(compare.SYSTEMS, [q[0] for q in compare.QUESTIONS], 2)
    assert len(steps) == 5 * 3 * 2
    assert len({compare.run_key(s, q, n) for s, q, _, n in steps}) == len(steps)


def test_dry_run_sends_nothing(capsys, tmp_path):
    assert compare.main(["--dry-run", "--out", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "30 runs" in out and not (tmp_path / "runs.json").exists()


def test_the_question_set_matches_the_exercise():
    ids = {q[0]: q[1] for q in compare.QUESTIONS}
    assert ids["levels"] == "What are the 3 homework levels in the AIE2026 course?"
    assert ids["lora-qlora"] == "What is the difference between LoRA and QLoRA?"
    assert ids["quiz"] == "Give me one review question from Lecture 02"


def test_execute_retries_rate_limits_and_reports_the_attempts():
    waits, calls = [], []

    def flaky(question):
        calls.append(question)
        if len(calls) < 3:
            raise ModelHTTPError(429, "gemini", {"error": "quota"})
        return {"answer": "ok", "tool_calls": [], "requests": 1, "input_tokens": 1, "output_tokens": 1}

    out = compare.execute("bare", "q", runner=flaky, sleep=waits.append)
    assert out["error"] is None and out["attempts"] == 3 and waits == [65, 65] and out["answer"] == "ok"


def test_execute_gives_up_after_three_attempts_and_records_the_error():
    def always_busy(question):
        raise ModelHTTPError(503, "gemini", "busy")

    waits = []
    out = compare.execute("bare", "q", runner=always_busy, sleep=waits.append)
    assert "503" in out["error"] and out["attempts"] == 3 and waits == [20, 20] and "answer" not in out


def test_execute_does_not_retry_other_errors():
    waits = []

    def bad_key(question):
        raise ModelHTTPError(403, "gemini", "bad key")

    out = compare.execute("bare", "q", runner=bad_key, sleep=waits.append)
    assert out["attempts"] == 1 and waits == [] and "403" in out["error"]


def test_a_missing_key_is_recorded_not_raised(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = compare.execute("bare", "q")
    assert "GEMINI_API_KEY" in out["error"]


def test_merge_replaces_runs_with_the_same_key():
    old = [{"key": "a", "v": 1}, {"key": "b", "v": 1}]
    assert compare.merge_runs(old, [{"key": "b", "v": 2}, {"key": "c", "v": 1}]) == [{"key": "a", "v": 1}, {"key": "b", "v": 2}, {"key": "c", "v": 1}]


def test_run_pydantic_with_the_test_model_reports_calls_and_requests():
    out = compare.run_pydantic("Give me one review question from Lecture 02", model=TestModel(call_tools=["make_quiz"]))
    assert [c["tool"] for c in out["tool_calls"]] == ["make_quiz"] and out["requests"] == 2 and out["answer"]


def test_main_saves_results_and_keeps_earlier_runs(tmp_path, monkeypatch):
    monkeypatch.setitem(compare.RUNNERS, "bare", lambda q: {"answer": "A", "tool_calls": [], "requests": 1, "input_tokens": 3, "output_tokens": 4})
    args = ["--systems", "bare", "--questions", "levels", "--repeat", "2", "--pause", "0", "--out", str(tmp_path)]
    assert compare.main(args) == 0
    first = json.loads((tmp_path / "runs.json").read_text(encoding="utf-8"))
    assert [r["key"] for r in first] == ["bare:levels:1", "bare:levels:2"] and first[0]["seconds"] >= 0

    monkeypatch.setitem(compare.RUNNERS, "bare", lambda q: {"answer": "B", "tool_calls": [], "requests": 1, "input_tokens": 3, "output_tokens": 4})
    assert compare.main(["--systems", "bare", "--questions", "levels", "--repeat", "1", "--pause", "0", "--out", str(tmp_path)]) == 0
    second = {r["key"]: r["answer"] for r in json.loads((tmp_path / "runs.json").read_text(encoding="utf-8"))}
    assert second == {"bare:levels:2": "A", "bare:levels:1": "B"}


def test_main_exits_with_1_when_a_run_failed(tmp_path, monkeypatch):
    def broken(q):
        raise ModelHTTPError(403, "gemini", "bad key")

    monkeypatch.setitem(compare.RUNNERS, "bare", broken)
    code = compare.main(["--systems", "bare", "--questions", "levels", "--repeat", "1", "--pause", "0", "--out", str(tmp_path)])
    assert code == 1
    saved = json.loads((tmp_path / "runs.json").read_text(encoding="utf-8"))
    assert saved[0]["error"] and "answer" not in saved[0]
