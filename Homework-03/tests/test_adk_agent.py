"""The ADK agent (Advanced a), checked offline with a scripted fake model: no key, no network.

Needs google-adk (`uv run --group adk pytest -q`); without it these tests are skipped.
"""
import json

import pytest

pytest.importorskip("google.adk")

from google.adk.models.base_llm import BaseLlm  # noqa: E402
from google.adk.models.llm_response import LlmResponse  # noqa: E402
from google.genai import types  # noqa: E402
from pydantic_ai.models.test import TestModel  # noqa: E402

from adk_agent.glossary_agent.agent import root_agent  # noqa: E402
from app import compare  # noqa: E402
from app.agent import INSTRUCTIONS, agent  # noqa: E402
from app.config import MODEL  # noqa: E402


class ScriptedLlm(BaseLlm):
    """Asks for the given (tool, args) calls one per request, then answers. Remembers every request it received."""

    model: str = "scripted"
    script: list = []
    requests: list = []

    async def generate_content_async(self, llm_request, stream=False):
        self.requests.append(llm_request)
        step = sum(1 for c in llm_request.contents for p in c.parts if p.function_response)
        usage = types.GenerateContentResponseUsageMetadata(prompt_token_count=100 + step, candidates_token_count=5)
        if step < len(self.script):
            name, args = self.script[step]
            part = types.Part(function_call=types.FunctionCall(name=name, args=args))
            yield LlmResponse(content=types.Content(role="model", parts=[part]), usage_metadata=usage)
        else:
            text = types.Part(text="Final answer (Lecture 02)")
            yield LlmResponse(content=types.Content(role="model", parts=[text]), usage_metadata=usage)


def scripted(*script):
    return ScriptedLlm(script=list(script), requests=[])


def test_adk_agent_is_built_from_the_exercise_agents_instructions_and_tools():
    assert root_agent.name == "glossary_agent"
    assert root_agent.instruction == INSTRUCTIONS            # the very same text, not a copy
    assert root_agent.model == MODEL
    assert [t.__name__ for t in root_agent.tools] == ["search_glossary", "get_lecture_summary", "make_quiz"]


def test_both_frameworks_show_the_model_the_same_tool_descriptions():
    fake = scripted()
    compare.run_adk("hello", model=fake)
    request = fake.requests[0]
    adk_tools = {d.name: d for d in request.config.tools[0].function_declarations}

    pyd = TestModel(call_tools=[])
    agent.run_sync("hello", model=pyd)
    pyd_tools = {t.name: t for t in pyd.last_model_request_parameters.function_tools}

    assert set(adk_tools) == set(pyd_tools) == {"search_glossary", "get_lecture_summary", "make_quiz"}
    for name, tool in pyd_tools.items():
        first_line = tool.description.strip().splitlines()[0]
        assert first_line in adk_tools[name].description      # the docstring is the description in both
    assert "Put only one term" in adk_tools["search_glossary"].description
    assert adk_tools["make_quiz"].parameters_json_schema["properties"]["lecture"]["type"] == "integer"
    assert adk_tools["make_quiz"].parameters_json_schema["required"] == ["lecture"]
    assert "system_instruction" in request.config.model_fields_set and INSTRUCTIONS.strip() in str(request.config.system_instruction)


def test_adk_loop_calls_the_tool_and_returns_its_result_to_the_model():
    fake = scripted(("search_glossary", {"query": "LoRA"}))
    out = compare.run_adk("What is LoRA?", model=fake)
    assert out["tool_calls"] == [{"tool": "search_glossary", "args": {"query": "LoRA"}}]
    assert out["requests"] == 2 and len(fake.requests) == 2          # one request asked for the tool, one wrote the answer
    assert out["answer"] == "Final answer (Lecture 02)"
    assert out["input_tokens"] == 100 + 101 and out["output_tokens"] == 10
    returned = [p.function_response for c in fake.requests[1].contents for p in c.parts if p.function_response]
    assert returned and returned[0].name == "search_glossary"
    # ADK wraps a tool's string result as {"result": "..."} before giving it back to the model
    assert list(returned[0].response) == ["result"] and json.loads(returned[0].response["result"])[0]["term"] == "LoRA"


def test_adk_runs_make_quiz_and_two_searches_in_order():
    fake = scripted(("search_glossary", {"query": "LoRA"}), ("search_glossary", {"query": "QLoRA"}), ("make_quiz", {"lecture": 2}))
    out = compare.run_adk("question", model=fake)
    assert [c["tool"] for c in out["tool_calls"]] == ["search_glossary", "search_glossary", "make_quiz"]
    assert out["tool_calls"][2]["args"] == {"lecture": 2} and out["requests"] == 4


def test_adk_make_quiz_with_a_lecture_that_has_no_terms_does_not_break_the_run():
    out = compare.run_adk("question", model=scripted(("make_quiz", {"lecture": 0})))
    assert out["answer"] == "Final answer (Lecture 02)" and out["requests"] == 2


def test_running_twice_does_not_change_the_shared_agent():
    compare.run_adk("a", model=scripted())
    assert root_agent.model == MODEL
