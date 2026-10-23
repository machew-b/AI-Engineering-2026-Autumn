# Homework 01: Introduction to AI Engineering and AI-Assisted Coding

Level chosen: **Implementation** (keep the conversation history while asking follow-up questions).
The write-up is in [`answer.md`](./answer.md).

## What is in this folder

| Path | What it is |
|------|------------|
| `app/ask.py` | The course's `app/ask.py` with token counts and conversation history added |
| `app/config.py` | Copied from the course repo (model name from `AIE_MODEL`, API key from `GEMINI_API_KEY`) |
| `tests/` | Offline tests: history logic, token counts, a local fake Gemini server, and a scan for leaked API keys |
| `pyproject.toml` | Dependencies, pinned to the same `google-genai` version as the course repo |
| `answer.md` | The submission file, with `TODO (live run)` marks for results that need my own API key |

The course repo is `matsuolab/lecture-ai-engineering-2026`. This repo is a standalone repo, not a fork, so the
relevant course files were copied here instead of being inherited.

## Run it

```bash
cd Homework-01
uv run pytest -q                                      # offline, no key needed
uv run python -m app.ask "What is LoRA?"              # one question, prints token counts
uv run python -m app.ask --chat                       # chat that keeps the history
AIE_MODEL=gemini-3.8-flash uv run python -m app.ask --chat
```

If `uv` is not installed in the Codespace, run `pip install uv` first.
In chat mode: `/history`, `/reset`, `/exit`.

## Steps that only I can do (they use my own accounts)

1. Create a Gemini API key at https://aistudio.google.com/apikey with a personal Google account.
2. In GitHub **Settings, Codespaces, Secrets**, add `GEMINI_API_KEY` and give it access to this repo
   (`machew-b/AI-Engineering-2026-Autumn`). Do this before launching the Codespace.
3. Launch a Codespace, run the commands above, and fill in every `TODO (live run)` in `answer.md`.
4. Stop the Codespace when done (bottom left, Codespaces, Stop Current Codespace).

Never paste the key into code, chat, commits or screenshots.
