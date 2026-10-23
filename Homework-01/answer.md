# Lecture 1 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: branch `lec01` to `main` in my own repo (not the course repo)

> **Status: draft prepared with an AI assistant.** Everything marked `TODO (live run)` needs a real
> call to the Gemini API with my own key. Nothing in those fields has been filled in on purpose,
> because I will only write results I actually saw. Delete this note once the TODOs are done.

## Exercise

- Model's answer to the course-specific question (the "3 levels" of the homework), summarized:
  `TODO (live run)`: run `uv run python -m app.ask "In the AIE2026 course homework, what are the '3 levels'?"` and summarize what it said.
- What I noticed when comparing it with the correct meaning:
  `TODO (live run)`.
  Reference for the comparison (`homework-levels` in the course repo's `data/glossary.json`): the three levels are
  Basic (check the lecture content), Implementation (write the code yourself) and Advanced (investigate and experiment).
  Doing any one of them completes that week's homework, and it is generally not graded.
- Token counts displayed (input / output): `TODO (live run)`, e.g. from `uv run python -m app.ask "What is LoRA?"`.
  The code that prints them is done and tested (see below).

## Homework

- **Level chosen:** Implementation
- **What I did:** Changed `app/ask.py` so I can keep asking follow-up questions while the conversation history is preserved.
  - Added a `Conversation` class that stores the history as `user` and `model` messages and sends all of it as `contents` on every call.
    This is needed because the Gemini API is stateless: the model only knows what is in the request.
  - Added a chat mode: `uv run python -m app.ask --chat` (optionally with a first question).
    Commands: `/history` shows saved turns, `/reset` forgets them, `/exit` quits.
    Calling it without `--chat` still asks one question with no history, as before.
  - A turn is saved only after the call succeeds. If the API returns 429 or 503, or the model returns no text,
    the question is not added to the history, so retrying the same question does not leave a dangling message behind.
  - Completed the Lecture 1 exercise TODO in the same file: every call prints input and output token counts
    (from `response.usage_metadata`), plus thinking tokens when the model reports them, and in chat mode a running session total.
- **Results (what was actually verified, and how):**
  - 23 offline tests pass (`uv run pytest -q`, run in a clean environment with `google-genai==2.31.0`).
    They check that the second request contains `[user, model, user]` in the right order, that failed calls do not
    pollute the history, that `/reset` works, and that missing token fields do not crash.
  - One test runs the real `google-genai` SDK against a small local fake Gemini server. It confirms that the history is
    really serialized into the HTTP request body and that the SDK fills `prompt_token_count`, `candidates_token_count`
    and `thoughts_token_count`, which are the fields the code reads.
  - I also ran the real CLI in single and chat mode against that fake server. The history size seen by the server went
    1, then 3 messages on the follow-up, then back to 1 after `/reset`. The token numbers in that run were made up by the
    fake server, so they say nothing about Gemini.
  - **Not verified yet:** a conversation with the real model. `TODO (live run)`: start `--chat` with my own key, ask a
    question and then a follow-up that only makes sense with context (for example "explain that in one sentence"),
    and write down whether the model used the earlier turn. Record the result as it is, even if it did not work.
- **Models used:** `gemini-3.5-flash-lite` (course default) in the code and tests. Live runs: `TODO (live run)`.
  I avoided `gemini-3.5-flash` because the slides say it was deprecated on 2026-10-08.
- **AI tools used:** Claude (Anthropic) wrote the code, the tests and the first draft of this file. What I checked myself
  is limited to what is listed under Results; I still need to read the code, run it with my own key and fill in the TODOs.
  No API key appears in any file (a test scans this folder for Google key patterns).
- **Insights and questions** (these are expectations from how the API works, to be confirmed in the live run):
  - Because the whole history is resent every turn, the input token count should grow turn by turn even when the
    follow-up question is short. This is the same quantity that the rate limit and the context window are measured in.
  - Each turn still counts as one request, so the free-tier limits on requests per minute and per day are used up at the
    same pace as with single questions, but token use per request keeps rising.
  - Open question: when should old turns be trimmed or summarized, and how does the model behave when the history gets long?
