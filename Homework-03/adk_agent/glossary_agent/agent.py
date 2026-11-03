"""Homework 3, Advanced (a): the exercise agent rebuilt with Google's ADK.

Only the agent-building part is new. INSTRUCTIONS and the tools are the exercise agent's own code, imported as they are
(app/agent.py and app/tools.py are not changed for this).

Run from the Homework-03 folder:
    PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL

# The slide hard-codes "gemini-3.5-flash-lite", which is also the course default. Reading MODEL from app/config.py
# gives the same value and keeps AIE_MODEL working (for example when the default model returns 503).
root_agent = Agent(
    model=MODEL,
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
