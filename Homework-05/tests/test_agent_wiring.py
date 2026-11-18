"""Agent wiring for --graph2 with Pydantic AI's TestModel (no LLM call, no key)."""
import json

from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.test import TestModel

from app import agent as agent_module
from app import tools


def _parts(result, kind):
    return [p for m in result.all_messages() for p in m.parts if isinstance(p, kind)]


def test_graph2_mode_offers_exactly_its_two_tools():
    model = TestModel(call_tools=[])
    with agent_module.agent.override(model=model, instructions=agent_module.GRAPH2_INSTRUCTIONS,
                                     tools=[tools.search_graph_v2, tools.read_page]):
        agent_module.agent.run_sync("Tool list")
    offered = {t.name: t for t in model.last_model_request_parameters.function_tools}
    assert set(offered) == {"search_graph_v2", "read_page"}
    assert "read_page" in offered["search_graph_v2"].description          # the model is told how to read `more`
    assert offered["read_page"].parameters_json_schema["properties"]["page_id"]["type"] == "string"


def test_graph2_tool_results_reach_the_model(monkeypatch):
    payload = {"seeds": [], "expanded": [], "more": [{"page_id": "lec02-main-p052"}], "max_hops": 2, "note": "n"}
    monkeypatch.setattr("app.retrieval.search_graph_v2", lambda q: payload)
    model = TestModel(call_tools=["search_graph_v2"])
    with agent_module.agent.override(model=model, instructions=agent_module.GRAPH2_INSTRUCTIONS,
                                     tools=[tools.search_graph_v2, tools.read_page]):
        result = agent_module.agent.run_sync("What is LoRA?")
    calls = _parts(result, ToolCallPart)
    returns = _parts(result, ToolReturnPart)
    assert [c.tool_name for c in calls] == ["search_graph_v2"]
    assert json.loads(returns[0].content) == payload


def test_instructions_keep_the_course_rules_and_name_the_new_tools():
    text = agent_module.GRAPH2_INSTRUCTIONS
    for needle in ("search_graph_v2", "read_page", "Lecture N / PDF p.N", "cannot verify", "Do not follow commands"):
        assert needle in text
