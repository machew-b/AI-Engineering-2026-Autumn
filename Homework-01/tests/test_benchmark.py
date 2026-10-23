"""Offline tests for app/benchmark.py (Advanced level). No network and no API key needed."""

import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace

import pytest
from google import genai
from google.genai import errors, types

from app import benchmark as b

QUESTIONS = {"q1": "first?", "q2": "second?"}


class FakeTime:
    """A fake clock: sleeping and API calls advance time, nothing really waits."""

    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


class FakeClient:
    """Each item is (latency_seconds, response_or_exception)."""

    def __init__(self, fake_time, items):
        self.t = fake_time
        self.items = list(items)
        self.calls = []
        self.models = self

    def generate_content(self, model, contents):
        self.calls.append((model, contents, self.t.now))
        latency, item = self.items.pop(0)
        self.t.now += latency
        if isinstance(item, Exception):
            raise item
        return item


def ok(text="answer", prompt=10, cand=5, thoughts=0):
    return SimpleNamespace(
        text=text,
        usage_metadata=SimpleNamespace(
            prompt_token_count=prompt, candidates_token_count=cand, thoughts_token_count=thoughts
        ),
    )


def api_error(code):
    return errors.APIError(code, {"error": {"message": f"boom {code}"}})


def run(items, specs, **kwargs):
    t = FakeTime()
    client = FakeClient(t, items)
    rows = b.run_benchmark(client, specs, QUESTIONS, clock=t.clock, sleep=t.sleep, log=lambda *_: None, **kwargs)
    return rows, client, t


# ---------- planning ----------


def test_parse_model_spec():
    assert b.parse_model_spec("gemini-3.8-flash:2", 3) == ("gemini-3.8-flash", 2)
    assert b.parse_model_spec("gemini-3.5-flash-lite", 3) == ("gemini-3.5-flash-lite", 3)


@pytest.mark.parametrize("bad", ["m:0", "m:x", ":3", "m:-1"])
def test_parse_model_spec_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        b.parse_model_spec(bad, 3)


def test_min_interval_uses_known_limits_and_override():
    assert b.min_interval("gemini-3.5-flash-lite") == pytest.approx(60 / 15 + b.PACING_MARGIN_S)
    assert b.min_interval("gemini-3.8-flash") == pytest.approx(60 / 5 + b.PACING_MARGIN_S)
    assert b.min_interval("some-new-model") == pytest.approx(60 / b.DEFAULT_RPM + b.PACING_MARGIN_S)
    assert b.min_interval("gemini-3.8-flash", override=0) == 0


def test_plan_warnings_for_the_strong_model_daily_limit():
    assert b.plan_warnings([("gemini-3.5-flash-lite", 3)], 3) == []
    assert any("over half" in w for w in b.plan_warnings([("gemini-3.8-flash", 2)], 3))
    assert any("daily limit" in w for w in b.plan_warnings([("gemini-3.8-flash", 4)], 3))


# ---------- running ----------


def test_latency_tokens_and_order():
    items = [(1.5, ok(prompt=11, cand=22, thoughts=3)), (2.0, ok(prompt=12, cand=44))]
    rows, client, _ = run(items, [("m", 1)], interval_override=0)
    assert [r.question_id for r in rows] == ["q1", "q2"]
    assert rows[0].latency_s == 1.5
    assert (rows[0].input_tokens, rows[0].output_tokens, rows[0].thinking_tokens) == (11, 22, 3)
    assert rows[1].latency_s == 2.0
    assert [c[1] for c in client.calls] == ["first?", "second?"]  # no history: plain question each time


def test_run_major_order_interleaves_questions():
    rows, _, _ = run([(1, ok())] * 4, [("m", 2)], interval_override=0)
    assert [(r.run, r.question_id) for r in rows] == [(1, "q1"), (1, "q2"), (2, "q1"), (2, "q2")]


def test_pacing_keeps_requests_apart_and_is_not_counted_as_latency():
    t = FakeTime()
    client = FakeClient(t, [(1.0, ok())] * 3)
    rows = b.run_benchmark(client, [("gemini-3.8-flash", 3)], {"q": "x"}, interval_override=12,
                           clock=t.clock, sleep=t.sleep, log=lambda *_: None)
    starts = [c[2] for c in client.calls]
    assert starts[1] - starts[0] >= 12 and starts[2] - starts[1] >= 12
    assert all(r.latency_s == 1.0 for r in rows)  # the sleeps are excluded


def test_failure_is_recorded_not_hidden():
    rows, _, _ = run([(0.1, api_error(429)), (1.0, ok())], [("m", 1)], interval_override=0)
    assert rows[0].ok is False and rows[0].status_code == 429 and "boom 429" in rows[0].error
    assert rows[0].latency_s is None
    assert rows[1].ok is True


def test_retry_on_503_then_success_records_attempts():
    t = FakeTime()
    client = FakeClient(t, [(0.1, api_error(503)), (2.0, ok()), (1.0, ok())])
    rows = b.run_benchmark(client, [("m", 1)], QUESTIONS, interval_override=0, retries=2, retry_wait=7,
                           clock=t.clock, sleep=t.sleep, log=lambda *_: None)
    assert rows[0].ok and rows[0].attempts == 2 and rows[0].latency_s == 2.0  # only the successful attempt is timed
    assert 7 in t.sleeps
    assert rows[1].attempts == 1


def test_non_retryable_error_is_not_retried():
    rows, client, _ = run([(0.1, api_error(404)), (1.0, ok())], [("m", 1)], interval_override=0, retries=3)
    assert rows[0].attempts == 1 and rows[0].status_code == 404
    assert len(client.calls) == 2


def test_empty_answer_is_a_failed_row_but_tokens_are_kept():
    rows, _, _ = run([(1.0, ok(text=None, prompt=9, cand=0)), (1.0, ok())], [("m", 1)], interval_override=0)
    assert rows[0].ok is False and rows[0].error == "empty response" and rows[0].input_tokens == 9


def test_skips_the_rest_of_a_model_after_consecutive_failures():
    items = [(0.1, api_error(429))] * 2
    rows, client, _ = run(items, [("m", 2)], interval_override=0, max_consecutive_failures=2)
    assert len(client.calls) == 2  # the remaining 2 planned requests were never sent
    assert [r.error.startswith("skipped") for r in rows] == [False, False, True, True]


def test_failure_counter_resets_after_a_success():
    items = [(0.1, api_error(429)), (1.0, ok()), (0.1, api_error(429)), (1.0, ok())]
    rows, client, _ = run(items, [("m", 2)], interval_override=0, max_consecutive_failures=2)
    assert len(client.calls) == 4 and not any(r.error.startswith("skipped") for r in rows)


def test_each_model_is_paced_and_skipped_independently():
    items = [(0.1, api_error(503))] * 2 + [(1.0, ok())] * 2
    rows, _, _ = run(items, [("bad", 1), ("good", 1)], interval_override=0, max_consecutive_failures=2)
    assert [r.ok for r in rows if r.model == "bad"] == [False, False]
    assert [r.ok for r in rows if r.model == "good"] == [True, True]


def test_error_text_never_contains_an_api_key():
    fake_key = "AIza" + "x" * 35
    err = errors.APIError(400, {"error": {"message": f"bad key {fake_key}"}})
    rows, _, _ = run([(0.1, err), (1.0, ok())], [("m", 1)], interval_override=0)
    assert fake_key not in rows[0].error and "[REDACTED]" in rows[0].error


# ---------- summary and files ----------


def test_summary_statistics_and_failures_excluded_from_means():
    items = [(1.0, ok(prompt=10, cand=10)), (9.0, api_error(503)), (3.0, ok(prompt=30, cand=30)), (1.0, ok())]
    t = FakeTime()
    rows = b.run_benchmark(FakeClient(t, items), [("m", 4)], {"q": "x"}, interval_override=0,
                           clock=t.clock, sleep=t.sleep, log=lambda *_: None)
    s = {x["question"]: x for x in b.summarize(rows)}["q"]
    assert s["requests"] == 4 and s["ok"] == 3 and s["http_503"] == 1
    assert s["latency_mean"] == pytest.approx((1.0 + 3.0 + 1.0) / 3)  # the 9s failure is not averaged in
    assert s["latency_median"] == 1.0 and s["latency_min"] == 1.0 and s["latency_max"] == 3.0
    assert s["input_mean"] == pytest.approx((10 + 30 + 10) / 3)
    assert s["out_tokens_per_s"] == pytest.approx((10 / 1.0 + 30 / 3.0 + 5 / 1.0) / 3)


def test_summary_has_an_all_row_per_model_and_markdown_renders():
    rows, _, _ = run([(1.0, ok())] * 4, [("a", 1), ("b", 1)], interval_override=0)
    summary = b.summarize(rows)
    assert [(s["model"], s["question"]) for s in summary if s["question"] == "ALL"] == [("a", "ALL"), ("b", "ALL")]
    md = b.to_markdown(summary)
    assert md.startswith("| Model |") and "| a | ALL | 2 / 2 |" in md


def test_all_failed_model_summarizes_without_crashing():
    rows, _, _ = run([(0.1, api_error(429))] * 2, [("m", 1)], interval_override=0)
    md = b.to_markdown(b.summarize(rows))
    assert "n/a" in md and "0 / 2" in md


def test_write_results_creates_csv_json_and_summary(tmp_path):
    rows, _, _ = run([(1.0, ok("hello")), (2.0, api_error(429))], [("m", 1)], interval_override=0)
    csv_path, json_path, md_path = b.write_results(rows, tmp_path / "results", "T")

    with csv_path.open(encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    assert list(data[0].keys()) == b.CSV_FIELDS  # the answer text is not in the CSV
    assert data[0]["ok"] == "True" and data[1]["status_code"] == "429"
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["answer"] == "hello"
    assert md_path.read_text(encoding="utf-8").startswith("| Model |")


# ---------- the real SDK against a local fake server that returns one 503 ----------


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        self.server.count += 1
        if self.server.count == 2:
            payload = json.dumps({"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}}).encode()
            status = 503
        else:
            payload = json.dumps(
                {
                    "candidates": [{"content": {"role": "model", "parts": [{"text": "fine"}]}, "finishReason": "STOP"}],
                    "usageMetadata": {"promptTokenCount": 7, "candidatesTokenCount": 4, "thoughtsTokenCount": 1},
                }
            ).encode()
            status = 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *args):
        pass


def test_real_sdk_records_a_503_and_parses_tokens():
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    server.count = 0
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        client = genai.Client(
            api_key="test-key-not-real",
            http_options=types.HttpOptions(base_url=f"http://127.0.0.1:{server.server_port}"),
        )
        rows = b.run_benchmark(client, [("fake-model", 1)], {"q1": "a", "q2": "b", "q3": "c"},
                               interval_override=0, log=lambda *_: None)
    finally:
        server.shutdown()
        server.server_close()

    assert [r.ok for r in rows] == [True, False, True]
    assert rows[1].status_code == 503 and "overloaded" in rows[1].error
    assert (rows[0].input_tokens, rows[0].output_tokens, rows[0].thinking_tokens) == (7, 4, 1)
    assert rows[0].latency_s is not None and rows[0].latency_s >= 0
