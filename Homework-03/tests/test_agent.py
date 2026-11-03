"""Agent wiring tests.

TestModel is a fake model that calls all registered tools and returns a dummy answer
without calling a real LLM. Check that tools are registered, called, and return results
to the model, without using an API key or consuming usage allowances.
The first two tests are the course's; the others are for make_quiz and for the helpers added in this homework.
"""

import json

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import agent as agent_module
from app.agent import agent, summarize_run

BASE_TOOLS = {"search_glossary", "get_lecture_summary"}


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_base_tools_are_registered_and_called():
    model = TestModel()
    with agent.override(model=model):
        result = agent.run_sync("What is LoRA?")

    offered = {t.name for t in model.last_model_request_parameters.function_tools}
    assert BASE_TOOLS <= offered  # Check inclusion so adding tools in the exercises does not break the test

    called = {p.tool_name for p in _parts(result, ToolCallPart)}
    assert BASE_TOOLS <= called
    # Tools requiring approval (requires_approval=True) wait without executing and therefore have no return value
    waiting = len(result.output.approvals) if isinstance(result.output, DeferredToolRequests) else 0
    assert len(_parts(result, ToolReturnPart)) + waiting == len(_parts(result, ToolCallPart))
    assert result.output


def test_glossary_result_reaches_the_model():
    model = TestModel(call_tools=["search_glossary"])
    with agent.override(model=model):
        result = agent.run_sync("What is RAG?")
    returns = _parts(result, ToolReturnPart)
    assert returns and returns[0].tool_name == "search_glossary"


def test_make_quiz_is_registered_called_and_its_result_reaches_the_model():
    model = TestModel(call_tools=["make_quiz"])
    with agent.override(model=model):
        result = agent.run_sync("Give me one review question from Lecture 02")
    offered = {t.name: t for t in model.last_model_request_parameters.function_tools}
    assert "make_quiz" in offered and "review question" in offered["make_quiz"].description
    assert offered["make_quiz"].parameters_json_schema["properties"]["lecture"]["type"] == "integer"
    returns = _parts(result, ToolReturnPart)
    assert [r.tool_name for r in returns] == ["make_quiz"]
    assert "No glossary terms were found" in returns[0].content or "question" in json.loads(returns[0].content)


def test_instructions_cover_every_tool_and_keep_the_course_rules():
    text = agent_module.INSTRUCTIONS
    for name in ("search_glossary", "get_lecture_summary", "make_quiz"):
        assert name in text
    assert "It is not in the glossary" in text and "(Lecture NN)" in text


def test_summarize_run_reports_calls_requests_and_tokens():
    model = TestModel(call_tools=["search_glossary", "make_quiz"])
    with agent.override(model=model):
        result = agent.run_sync("What is LoRA?")
    summary = summarize_run(result)
    assert [c["tool"] for c in summary["tool_calls"]] == ["search_glossary", "make_quiz"]
    assert all(isinstance(c["args"], dict) for c in summary["tool_calls"])
    assert summary["requests"] == 2          # one request that asked for the tools, one that wrote the answer
    assert summary["answer"] and summary["input_tokens"] >= 0 and summary["output_tokens"] >= 0


def test_list_tools_runs_without_a_key(capsys, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    agent_module.print_tools(agent)
    out = capsys.readouterr().out
    assert "Tools visible to the model: 3" in out and "[make_quiz]" in out and "Give me a review question for Lecture 2" in out
