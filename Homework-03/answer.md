# Lecture 3 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-03`

## Exercise

The course exercise: ask the learning support agent the Lecture 1 question, read its tool calls with `--trace`, and add the
`make_quiz` tool. Steps 1 and 6 of the exercise (Sync fork, the `lec03` branch, the pull request) do not apply here: this repository is a
standalone repo and the work is submitted from `main`, as in Homeworks 1 and 2. The course files were copied into this folder from
the course repo's `lec03-start` tag (`matsuolab/lecture-ai-engineering-2026-en`).

<!-- AUTO:exercise -->
_Not run yet._
<!-- /AUTO:exercise -->

- Differences between the Lecture 1 (bare LLM) answer and the agent's:
  TODO(exercise-1): compare the `levels` row above with `homework-levels` in `data/glossary.json` (Basic, Implementation, Advanced; any one level completes the homework; generally not graded). Did the bare model say any of it, and does the agent end with a lecture number?
- Tool calls shown by `--trace` (tool names and arguments):
  TODO(exercise-2): copy the tool calls of the `lora-qlora` row (one search per term, as the docstring says?) and the `quiz` row (`make_quiz` with `lecture` 2?).
- Number of LLM calls for one question (`requests`):
  TODO(exercise-3): the "LLM requests per run" column above: 1 for the bare model, and for the agent one request per tool round plus one for the answer.
- Tool added and the description in its docstring: `make_quiz(lecture: int) -> str` in `app/tools.py`, registered in `app/agent.py` with
  `agent.tool_plain(tools.make_quiz)`. The docstring is the description the model reads:

  > Pick one term from the given lecture and return a review question and its answer.
  >
  > Use when the learner asks for a review question, a quiz or practice questions about a session, such as "Give me a review question
  > for Lecture 2". Pass the session number as an integer (for example, 2). Do not use it to explain a term; use search_glossary for
  > that. Ask the learner the question first, and give the answer only after they have tried or ask for it.

  How it works: it collects the glossary terms whose `lecture` equals the argument, picks one with `random.choice`, and returns
  `{"lecture", "question", "answer"}` as JSON (the question is `What does "PEFT" mean?`, the answer is that term's definition). For a
  lecture without terms (0, 4, 99, ...) it returns a plain message that lists the sessions that do have terms, instead of failing; the
  course's `pytest` calls every tool with a dummy `lecture=0`, so this case has to work. I also added one line to `INSTRUCTIONS`
  ("Use make_quiz when asked for a review question or a quiz about a session"). The course suggests that line only if the model does not
  call the tool; I added it at the start as a judgment call, and I did not test the agent without it.
  Checked offline: `uv run python -m app.agent --list-tools` shows `make_quiz` with this docstring and an integer `lecture` argument, and
  `uv run pytest -q` passes (see Notes).

## Homework

- **Level chosen:** Advanced, option (a): keep the exercise agent's instructions and tools, rewrite only the agent-building part with
  Google's ADK, run it with `adk run`, and compare the code and the answers

### What I did

- **Which option, and why:** I chose (a) over (b) (running the coding agent Pi) because (a) can be checked part by part without a live model:
  the ADK agent is built from the same text and the same functions, and its loop can be driven by a scripted fake model. (b) is an
  interactive agent that edits files, and I could not verify it the same way.
- **The ADK agent** is `adk_agent/glossary_agent/agent.py` (about ten lines of code) and `adk_agent/glossary_agent/__init__.py` (`from . import agent`).
  It imports `INSTRUCTIONS` from `app/agent.py` and the three functions from `app/tools.py`, so the instructions and the tool descriptions
  are the very same objects as in the Pydantic AI agent, not copies. No file in `app/` was changed for it. The one difference from the slide
  is the model: the slide writes `"gemini-3.5-flash-lite"`, which is also the course default, and I read `MODEL` from `app/config.py`
  instead, so `AIE_MODEL` (the course's advice when the default returns 503) works for both agents.
- **Same tools, same instructions, same model:** both agents use `gemini-3.5-flash-lite` unless `AIE_MODEL` is set, with `search_glossary`,
  `get_lecture_summary` and `make_quiz`. The tools and the instructions are identical; what is not identical is how each framework turns
  them into a request (compared below).
- **Running it:** with the course's command, from this folder:
  `PYTHONPATH=. uv run --with google-adk==2.13.0 adk run adk_agent/glossary_agent` (I pinned the version I tested, 2.13.0; the
  slides warn that ADK 2.0 changed a lot, so I wrote the code against the installed package and not against articles).
  `adk run` is interactive, so for repeatable numbers I also run the ADK agent from code (`app/compare.py`, `run_adk`), with a session and
  the event stream, and count what the framework reports.
- **The comparison** (`app/compare.py`): 5 questions, 2 runs each, on 3 systems: the bare model (Lecture 1), the Pydantic AI agent and the
  ADK agent. For every run it saves the answer, the tool calls with their arguments, the number of LLM requests, the token counts and the
  time (`results/compare/runs.json`). The questions:

  | Id | Question | Why it is there |
  |---|---|---|
  | `levels` | What are the 3 homework levels in the AIE2026 course? | exercise step 2: course-specific, the answer is in the glossary |
  | `lora-qlora` | What is the difference between LoRA and QLoRA? | exercise step 3: two terms, so two searches expected |
  | `quiz` | Give me one review question from Lecture 02 | exercise step 5: `make_quiz` with `lecture` 2 expected |
  | `summary` | What will we learn in Lecture 03? | `get_lecture_summary` expected |
  | `unknown` | What is a vector database? | not in the glossary: the instructions say to say so and not to guess |

- **How requests are counted in ADK:** the number of events whose content is from the model (a tool-call turn or the final answer). The
  tool results come back as events from the program, so they are not counted. In the offline test this gives 2 for one tool call and 4
  for three, the same as `requests` in the Pydantic AI usage. Token counts are the sums of `usage_metadata` over the model events.
- **Retries and pacing:** a 429 is retried after 65 s and a 503 after 20 s, at most 3 attempts; other errors are recorded and not retried.
  Failed runs are kept in the file with their error and left out of the tables. There is a 6 s pause between runs.

Commands used:

```bash
uv run --group adk python -m app.compare --dry-run        # 30 runs, about 70 LLM requests
uv run --group adk python -m app.compare
PYTHONPATH=. uv run --with google-adk==2.13.0 adk run adk_agent/glossary_agent
uv run python -m app.report --write
```

### Results

Pydantic AI against ADK, same instructions and tools (run 1 for the tool calls, means over the successful runs for the numbers):

<!-- AUTO:comparison -->
_Not run yet._
<!-- /AUTO:comparison -->

The answers (run 1, shortened; the full text is in `results/compare/runs.json`):

<!-- AUTO:answers -->
_Not run yet._
<!-- /AUTO:answers -->

What the runs showed:

- **Tools and instructions:**
  TODO(adk-tools): did ADK call the same tools in the same order as Pydantic AI for each question (the "same tool order" column)? Where they differ, say how (for example one search with both terms in the query, or no search at all) and whether it matches what the docstring asks for.
- **Answers:**
  TODO(adk-answers): compare the two answers for `levels`, `quiz` and `unknown`: both correct against the glossary? both end with a lecture number? did the `unknown` question get "It is not in the glossary"?
- **Cost of the loop:**
  TODO(adk-cost): requests, tokens and seconds per question, and whether one framework needed more requests than the other for the same question.
- **`adk run`:**
  TODO(adk-run): one question typed into `adk run`, what it printed, and whether it matches what the code run showed.
- **Run-to-run differences:**
  TODO(adk-variation): runs 1 and 2 of the same question on the same system: did the tool calls or the wording change?

### Comparing the code

These differences are about the code and the requests, and I checked each one in the code or in the offline tests:

| | Pydantic AI (`app/agent.py`) | ADK (`adk_agent/glossary_agent/agent.py`) |
|---|---|---|
| Import | `from pydantic_ai import Agent` | `from google.adk.agents import Agent` |
| Instructions | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)` (singular) |
| Tools | registered after the agent exists, one call per function: `agent.tool_plain(tools.make_quiz)` | passed in the constructor: `tools=[tools.search_glossary, ...]` |
| Model | not part of the agent; passed when it runs: `agent.run_sync(q, model=build_model())` | part of the agent: `model="gemini-3.5-flash-lite"`; the key is read from the environment |
| Name | not needed | required: leaving `name` out raises a validation error |
| Tool description | the docstring and the type hints | the docstring and the type hints; the first docstring line is the same in both and `lecture` is an integer in both (test) |
| Tool result | the returned string goes to the model as it is | wrapped as `{"result": "<the string>"}` before it goes to the model (test) |
| Running | `run_sync` returns an object with `output`, `all_messages()` and `usage` | `adk run` for chatting; in code, a runner with a session and an async stream of events |
| Where a tool call shows up | `ToolCallPart` in the messages (the course's `--trace`) | `function_call` in an event; I read them in `app/compare.py` |
| Testing without a model | `TestModel` ships with the library | I wrote a small scripted `BaseLlm` (`tests/test_adk_agent.py`) |

- **Which key is used:** ADK builds its Gemini client from the environment. The Google client library reads `GOOGLE_API_KEY` first and
  `GEMINI_API_KEY` second and prefers the first when both are set, so in Codespaces, with only `GEMINI_API_KEY` registered, the same
  secret works for both agents.
- **What the course's `--trace` does not give for ADK:** the exercise's `--trace`, `--list-tools` and the tests are in `app/agent.py` and
  only work for the Pydantic AI agent, as the slide says ("not needed"). `app/compare.py` is my replacement for the trace on the ADK side.
- **Which I would use:** TODO(adk-choice): your own conclusion after the runs, in two or three sentences, using only what the tables show.

### Notes

- Offline tests (`uv run --group adk pytest -q`, no key and no network): the tools including `make_quiz` and its edge cases (lectures 0, 4, 99),
  the agent's wiring with `TestModel`, the ADK agent with a scripted fake model (same instructions object, same tool names, descriptions
  and argument types, the loop calls the tool and gives the result back, request and token counting), the live runner (retries, failure
  recording, merging runs), the report tables, and a scan that no API key is in the folder. `adk run` was started once with a dummy key to
  confirm it finds and loads `adk_agent/glossary_agent`; it then stopped at the network call, as expected without a key. They say nothing
  about what Gemini does with these prompts; only the live runs do.
- The comparison is small: 5 questions, 2 runs each, one model, one day. Model answers change between runs, so a difference of one tool call
  or one request between the two frameworks is not evidence of a framework difference.
- TODO(notes-live): say when you ran the live runs and with which model (`AIE_MODEL` or the default), and if any run failed with 429 or 503.
- AI tools helped me write the code, the tests and the first draft of this file; the live runs, the reading of the answers and the conclusions are my own.
