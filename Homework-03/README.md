# Homework 03: AI Agents

Level chosen: **Advanced (a)** (keep the exercise agent's instructions and tools, rewrite only the agent-building part with Google's ADK,
run it with `adk run`, and compare the code and the answers).
The write-up is in [`answer.md`](./answer.md).

## What is in this folder

| Path | What it is |
|------|------------|
| `adk_agent/glossary_agent/agent.py` | The Advanced task: the exercise agent rebuilt with ADK. It imports `INSTRUCTIONS` and the tools from `app/`, so nothing is copied |
| `adk_agent/glossary_agent/__init__.py` | One line (`from . import agent`) so that `adk run` finds the agent |
| `app/agent.py` | The course's Pydantic AI agent, with `make_quiz` registered and one line added to `INSTRUCTIONS`; `--trace` and `--list-tools` work as in the exercise |
| `app/tools.py` | The course's `search_glossary` and `get_lecture_summary`, plus `make_quiz` (exercise step 4) |
| `app/ask.py`, `app/config.py` | Lecture 1's bare-model script (with token counts) and the shared settings, copied from the course repo |
| `app/compare.py` | Runs the same questions through the bare model, the Pydantic AI agent and the ADK agent, and saves answers, tool calls, LLM requests, tokens and time |
| `app/report.py` | Turns `results/compare/runs.json` into the tables in `answer.md` (`--write`) and lists what is still unfinished (`--check`) |
| `data/` | `glossary.json` (`version: 2026-draft-1`) and `lectures/*.md`, copied from the course repo |
| `results/compare/` | Created by `app.compare`: `runs.json`, one record per run |
| `tests/` | Offline tests: tools, the agent's wiring, the ADK agent with a scripted fake model, the live runner, the report tables, `answer.md`, and a scan for leaked keys |
| `pyproject.toml` | Same pins as the course repo (without the MCP extra), plus an `adk` group with `google-adk==2.13.0` |
| `answer.md` | The submission write-up |

The course repo is `matsuolab/lecture-ai-engineering-2026-en`; the files were copied from its `lec03-start` tag. This repo is a standalone repo, not a
fork, so there is no Sync fork, no `lec03` branch and no pull request: everything is on `main`, as in Homeworks 1 and 2.
The Lecture 05 MCP code in the course's `app/agent.py` was left out because Homework 3 does not use it.

## Run it

```bash
cd Homework-03
uv run --group adk pytest -q                                          # offline, no key needed (50 tests)
uv run python -m app.agent --list-tools                               # the tools the model sees, make_quiz included (no key)
uv run python -m app.agent --trace "What is the difference between LoRA and QLoRA?"   # needs the key
uv run python -m app.agent --trace "Give me one review question from Lecture 02"      # needs the key
uv run --group adk python -m app.compare --dry-run                    # show the plan, send nothing
uv run --group adk python -m app.compare                              # 5 questions x 3 systems x 2 runs, needs the key
PYTHONPATH=. uv run --with google-adk==2.13.0 adk run adk_agent/glossary_agent        # chat with the ADK agent, needs the key
uv run python -m app.report --write                                   # put the tables into answer.md
uv run python -m app.report --check                                   # list what is still unfinished in answer.md
```

Without the `adk` group the ADK tests are skipped and `app.compare` cannot run the ADK agent. `uv` creates `uv.lock` on the first run.

## Steps that need my own accounts

The tests, the tools and the ADK agent's wiring were checked offline. What Gemini actually does with these prompts can only be seen with a key.

1. Make `GEMINI_API_KEY` available (in Codespaces, the secret from Lecture 1, with this repo selected; restart the Codespace if it was added later).
2. Run the commands above in this order: `--list-tools`, the two `--trace` questions, `app.compare`, then `adk run` with one question
   (for example the "3 homework levels" question), then `exit`. `app.compare` retries 429 and 503 errors by itself and records any run that still fails;
   run it again with `--systems`, `--questions` and `--repeat 1` to repeat only those.
3. `uv run python -m app.report --write`, then fill in the `TODO(...)` lines in `answer.md` from the tables and what `adk run` printed.
   `uv run python -m app.report --check` lists the ones left.
4. Look in `results/` before committing and make sure no key is in there (`uv run pytest -q` scans for it).
5. Stop the Codespace when done, and change the status of Homework 03 in the top-level README to `Finished`.
