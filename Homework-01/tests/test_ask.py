"""Offline tests for app/ask.py. No network and no API key needed."""

from types import SimpleNamespace

import pytest
from google.genai import errors

from app.ask import Conversation, EmptyResponseError, TokenUsage, chat_loop, run_once


def make_response(text="ok", prompt=10, candidates=5, thoughts=None):
    usage = SimpleNamespace(
        prompt_token_count=prompt,
        candidates_token_count=candidates,
        thoughts_token_count=thoughts,
    )
    return SimpleNamespace(text=text, usage_metadata=usage)


class FakeClient:
    """Stands in for genai.Client. Records a snapshot of `contents` for every call."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.models = self  # client.models.generate_content(...)

    def generate_content(self, model, contents):
        self.calls.append({"model": model, "contents": list(contents)})
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def roles_and_texts(contents):
    return [(c.role, c.parts[0].text) for c in contents]


# ---------- token counts (Lecture 1 exercise) ----------


def test_token_usage_reads_gemini_fields():
    usage = TokenUsage.from_metadata(make_response(prompt=12, candidates=34, thoughts=7).usage_metadata)
    assert (usage.input, usage.output, usage.thinking) == (12, 34, 7)


@pytest.mark.parametrize("metadata", [None, SimpleNamespace()])
def test_token_usage_tolerates_missing_metadata(metadata):
    assert TokenUsage.from_metadata(metadata) == TokenUsage(0, 0, 0)


def test_token_usage_none_fields_count_as_zero():
    usage = TokenUsage.from_metadata(SimpleNamespace(prompt_token_count=3, candidates_token_count=None))
    assert usage == TokenUsage(3, 0, 0)


def test_describe_mentions_thinking_only_when_present():
    assert TokenUsage(1, 2, 0).describe() == "input 1, output 2"
    assert TokenUsage(1, 2, 9).describe() == "input 1, output 2 (+9 thinking)"


def test_run_once_prints_answer_and_tokens(capsys):
    conversation = Conversation(FakeClient([make_response("Hello", prompt=11, candidates=22)]), model="m")
    assert run_once(conversation, "hi") == "Hello"
    out = capsys.readouterr().out
    assert "Hello" in out
    assert "[tokens] input 11, output 22" in out


# ---------- conversation history (Implementation level) ----------


def test_first_call_sends_only_the_question():
    client = FakeClient([make_response("A1")])
    Conversation(client, model="m").send("Q1")
    assert roles_and_texts(client.calls[0]["contents"]) == [("user", "Q1")]


def test_follow_up_resends_earlier_turns_in_order():
    client = FakeClient([make_response("A1"), make_response("A2"), make_response("A3")])
    conversation = Conversation(client, model="m")
    conversation.send("Q1")
    conversation.send("Q2")
    conversation.send("Q3")

    assert roles_and_texts(client.calls[1]["contents"]) == [("user", "Q1"), ("model", "A1"), ("user", "Q2")]
    assert roles_and_texts(client.calls[2]["contents"]) == [
        ("user", "Q1"),
        ("model", "A1"),
        ("user", "Q2"),
        ("model", "A2"),
        ("user", "Q3"),
    ]
    assert conversation.turns == 3


def test_model_name_is_passed_through():
    client = FakeClient([make_response()])
    Conversation(client, model="gemini-test").send("Q")
    assert client.calls[0]["model"] == "gemini-test"


def test_api_error_does_not_pollute_history_and_retry_works():
    error = errors.APIError(429, {"error": {"message": "quota"}})
    client = FakeClient([make_response("A1"), error, make_response("A2")])
    conversation = Conversation(client, model="m")
    conversation.send("Q1")

    with pytest.raises(errors.APIError):
        conversation.send("Q2")
    assert conversation.turns == 1  # Q2 was not saved

    conversation.send("Q2")  # retry
    assert roles_and_texts(client.calls[2]["contents"]) == [("user", "Q1"), ("model", "A1"), ("user", "Q2")]


def test_empty_answer_is_not_saved_but_tokens_are_counted():
    client = FakeClient([make_response(text=None, prompt=8, candidates=0)])
    conversation = Conversation(client, model="m")
    with pytest.raises(EmptyResponseError):
        conversation.send("Q")
    assert conversation.history == []
    assert conversation.total_usage.input == 8


def test_total_usage_accumulates_and_input_grows_with_history():
    client = FakeClient([make_response("A", prompt=10, candidates=5), make_response("B", prompt=30, candidates=6)])
    conversation = Conversation(client, model="m")
    conversation.send("Q1")
    conversation.send("Q2")
    assert conversation.last_usage == TokenUsage(30, 6, 0)
    assert conversation.total_usage == TokenUsage(40, 11, 0)


def test_reset_clears_history_but_keeps_total_usage():
    client = FakeClient([make_response("A1", prompt=10), make_response("A2", prompt=4)])
    conversation = Conversation(client, model="m")
    conversation.send("Q1")
    conversation.reset()
    conversation.send("Q2")
    assert roles_and_texts(client.calls[1]["contents"]) == [("user", "Q2")]
    assert conversation.total_usage.input == 14


# ---------- interactive loop ----------


def scripted_input(lines):
    items = iter(lines)

    def fake_input(prompt=""):
        try:
            return next(items)
        except StopIteration:
            raise EOFError

    return fake_input


def test_chat_loop_keeps_history_until_exit(capsys):
    client = FakeClient([make_response("A1"), make_response("A2")])
    conversation = Conversation(client, model="m")
    chat_loop(conversation, input_fn=scripted_input(["Q1", "", "Q2", "/exit", "never asked"]))

    assert conversation.turns == 2
    assert len(client.calls) == 2  # blank line and anything after /exit were ignored
    out = capsys.readouterr().out
    assert "model> A1" in out and "model> A2" in out
    assert "session total" in out


def test_chat_loop_first_question_then_continues():
    client = FakeClient([make_response("A1"), make_response("A2")])
    conversation = Conversation(client, model="m")
    chat_loop(conversation, first_question="Q1", input_fn=scripted_input(["Q2"]))
    assert roles_and_texts(client.calls[1]["contents"])[0] == ("user", "Q1")
    assert conversation.turns == 2


def test_chat_loop_reset_and_history_commands(capsys):
    client = FakeClient([make_response("A1"), make_response("A2")])
    conversation = Conversation(client, model="m")
    chat_loop(conversation, input_fn=scripted_input(["Q1", "/history", "/reset", "/history", "Q2"]))
    out = capsys.readouterr().out
    assert "you  : Q1" in out and "model: A1" in out
    assert "[history cleared]" in out and "[history is empty]" in out
    assert roles_and_texts(client.calls[1]["contents"]) == [("user", "Q2")]


def test_chat_loop_survives_api_error_and_empty_answer(capsys):
    client = FakeClient(
        [
            errors.APIError(503, {"error": {"message": "busy"}}),
            make_response(text=None),
            make_response("A"),
        ]
    )
    conversation = Conversation(client, model="m")
    chat_loop(conversation, input_fn=scripted_input(["Q", "Q", "Q"]))
    out = capsys.readouterr().out
    assert "503" in out
    assert "was not saved" in out
    assert conversation.turns == 1


def test_chat_loop_unknown_command_is_not_sent_to_the_model(capsys):
    client = FakeClient([])
    chat_loop(Conversation(client, model="m"), input_fn=scripted_input(["/nope"]))
    assert client.calls == []
    assert "unknown command" in capsys.readouterr().out


def test_ctrl_c_at_prompt_ends_the_loop_cleanly():
    def interrupted(prompt=""):
        raise KeyboardInterrupt

    chat_loop(Conversation(FakeClient([]), model="m"), input_fn=interrupted)


# ---------- configuration ----------


def test_default_model_is_the_course_default():
    from app import config

    assert config.DEFAULT_MODEL == "gemini-3.5-flash-lite"


def test_missing_api_key_stops_with_instructions(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(SystemExit) as info:
        Conversation()
    assert "GEMINI_API_KEY" in str(info.value)
