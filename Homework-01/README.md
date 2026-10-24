# Homework 01: Introduction to AI Engineering and AI-Assisted Coding

Level chosen: **Advanced** (measure response time and tokens, compare across models and questions, discuss free-tier rate limits).
The write-up is in [`answer.md`](./answer.md).

## What is in this folder

| Path | What it is |
|------|------------|
| `app/benchmark.py` | The Advanced-level tool: times requests and counts tokens across models and questions, paced for the free-tier limits |
| `app/ask.py` | The course's `app/ask.py` with token counts added, plus an optional chat mode that keeps the history |
| `app/config.py` | Copied from the course repo (model name from `AIE_MODEL`, API key from `GEMINI_API_KEY`) |
| `results/` | Created by the benchmark: raw CSV and JSON per run, and a markdown summary table |
| `tests/` | Offline tests: benchmark, history logic, token counts, a local fake Gemini server, and a scan for leaked API keys |
| `pyproject.toml` | Dependencies, pinned to the same `google-genai` version as the course repo |
| `answer.md` | The submission write-up: what was done, the results table, the comparison and the rate-limit discussion |

The course repo is `matsuolab/lecture-ai-engineering-2026`. This repo is a standalone repo, not a fork, so the
relevant course files were copied here instead of being inherited.

## Run it

```bash
cd Homework-01
uv run pytest -q                                       # offline, no key needed
uv run python -m app.ask "What is LoRA?"               # one question, prints token counts
uv run python -m app.benchmark --dry-run               # show the plan, send nothing
uv run python -m app.benchmark                         # default plan: flash-lite x3, 3.8-flash x2, 3 questions
uv run python -m app.benchmark --models gemini-3.5-flash-lite:5 --questions general-short long-answer
uv run python -m app.ask --chat                        # optional: chat that keeps the history
```

If `uv` is not installed, run `pip install uv` first. The benchmark warns when a plan would use a large share of a
model's daily free-tier allowance. Look at `results/` before committing it and make sure no key is in there.

## Steps that need my own accounts

1. Create a Gemini API key at https://aistudio.google.com/apikey with a personal Google account.
2. Put it in the `GEMINI_API_KEY` environment variable (or, in Codespaces, a Codespaces secret for this repo, set before launching).
3. Run the commands above. The results of my run are in `results/` and are written up in `answer.md`.
4. Stop the Codespace when done, if one was used.
