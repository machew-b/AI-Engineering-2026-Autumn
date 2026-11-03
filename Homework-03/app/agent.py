"""Lecture 03: a learning support agent built with Pydantic AI.

Usage:
    uv run python -m app.agent "What are the 3 homework levels in the AIE2026 course?"
    uv run python -m app.agent --trace "What is the difference between LoRA and QLoRA?"   # Show tool calls
    uv run python -m app.agent --list-tools                                               # Tools visible to the model (no API key)

Agent = model + loop + tools.
The model calls functions in tools.py as "tools" and uses their results to compose answers.

Copied from the course repo (matsuolab/lecture-ai-engineering-2026-en, app/agent.py, tag lec03-start) with these changes:
  - the Lecture 05 MCP parts (--mcp, load_mcp_servers, build_mcp_agent) are removed, because Homework 3 does not use them
  - make_quiz (exercise step 4) is registered, and INSTRUCTIONS says when to use it
  - summarize_run() turns a finished run into plain data, so app/compare.py can compare this agent with the ADK one
"""

import argparse
import inspect
import json

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ToolCallPart, ToolReturnPart
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.test import TestModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

# The ADK agent (adk_agent/glossary_agent/agent.py) imports this text as it is, so both agents get the same instructions.
INSTRUCTIONS = """\
You are a learning support agent for the AI Engineering Pilot Course (AIE2026).
- Always check the glossary with search_glossary before answering about terms or course-specific information.
- Use get_lecture_summary when asked about the content of a session.
- Use make_quiz when asked for a review question or a quiz about a session.
- If something is absent from the glossary, say "It is not in the glossary" instead of making assertions based on guesses.
- End your answer by indicating the relevant session (Lecture NN).
- Guide learners with hints on how to think, rather than writing homework answers for them.
"""

# Pass the model at runtime (so tests can substitute TestModel without calling an API)
agent = Agent(instructions=INSTRUCTIONS)
agent.tool_plain(tools.search_glossary)
agent.tool_plain(tools.get_lecture_summary)
agent.tool_plain(tools.make_quiz)  # Lecture 03 exercise, step 4


def build_model() -> GoogleModel:
    return GoogleModel(MODEL, provider=GoogleProvider(api_key=get_api_key()))


def print_tools(target: Agent) -> None:
    """Display tools visible to the model (names, descriptions, arguments). Do not call an LLM.

    Pass the tools to TestModel (the fake model used for testing) and read them back.
    """
    model = TestModel(call_tools=[])
    target.run_sync("Tool list", model=model)
    tools_seen = model.last_model_request_parameters.function_tools
    print(f"Tools visible to the model: {len(tools_seen)}")
    for tool in tools_seen:
        print(f"\n[{tool.name}]")
        print("  " + inspect.cleandoc(tool.description or "").replace("\n", "\n  "))
        params = tool.parameters_json_schema.get("properties", {})
        print(f"  Arguments: {json.dumps(params, ensure_ascii=False)}")


def print_trace(result) -> None:
    """Display which tools were called with which arguments and what they returned."""
    print("\n--- trace ---")
    for message in result.all_messages():
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                print(f"[tool call]   {part.tool_name}({part.args})")
            elif isinstance(part, ToolReturnPart):
                print(f"[tool return] {part.tool_name} -> {str(part.content)[:120]}…")
    print(f"[usage] {result.usage}")


def _args_as_dict(args) -> dict:
    if isinstance(args, str):
        try:
            return json.loads(args)
        except json.JSONDecodeError:
            return {"_raw": args}
    return dict(args or {})


def summarize_run(result) -> dict:
    """A finished run as plain data: answer, tool calls (name and arguments), LLM requests and token counts."""
    calls = [
        {"tool": p.tool_name, "args": _args_as_dict(p.args)}
        for m in result.all_messages()
        for p in m.parts
        if isinstance(p, ToolCallPart)
    ]
    usage = result.usage() if callable(result.usage) else result.usage
    return {
        "answer": str(result.output),
        "tool_calls": calls,
        "requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the learning support agent a question")
    parser.add_argument("question", nargs="?")
    parser.add_argument("--trace", action="store_true", help="Show tool calls")
    parser.add_argument("--list-tools", action="store_true", help="List tools visible to the model and exit (no API key needed)")
    args = parser.parse_args()

    if args.list_tools:
        print_tools(agent)
        return
    if not args.question:
        parser.error("Please provide a question")

    print(f"[model] {MODEL}")
    try:
        result = agent.run_sync(args.question, model=build_model())
    except ModelHTTPError as e:
        print(api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    print(result.output)
    if args.trace:
        print_trace(result)


if __name__ == "__main__":
    main()
