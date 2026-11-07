# Lecture 3 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-03`

## Exercise

The course exercise: ask the learning support agent the Lecture 1 question, read its tool calls with `--trace`, and add the
`make_quiz` tool. Steps 1 and 6 of the exercise (Sync fork, the `lec03` branch, the pull request) do not apply here: this repository is a
standalone repo and the work is submitted from `main`, as in Homeworks 1 and 2. The course files were copied into this folder from
the course repo's `lec03-start` tag (`matsuolab/lecture-ai-engineering-2026-en`).

<!-- AUTO:exercise -->
| Question | System | Tool calls (run 1) | LLM requests per run | Answer (run 1, shortened) |
|---|---|---|---|---|
| What are the 3 homework levels in the AIE202… | Bare model (Lecture 1) | none | 1/1 | Based on the curriculum structure typically used in AIE courses (such as the Advanced AI … |
| What are the 3 homework levels in the AIE202… | Pydantic AI agent | `get_lecture_summary(1)`, `get_lecture_summary(2)`, `get_lecture_summary(3)`, `get_lecture_summary(4)`, `get_lecture_summary(5)`, `search_glossary('homework')` | 7/7 | The three homework levels in the AIE2026 course are: 1. **Basic**: Review the lecture con… |
| What is the difference between LoRA and QLoR… | Bare model (Lecture 1) | none | 1/1 | Both **LoRA (Low-Rank Adaptation)** and **QLoRA (Quantized Low-Rank Adaptation)** are tec… |
| What is the difference between LoRA and QLoR… | Pydantic AI agent | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | 2/2 | To understand the difference between LoRA and QLoRA, it helps to look at how each handles… |
| Give me one review question from Lecture 02 | Bare model (Lecture 1) | none | 1/1 | Since you didn't mention the specific course or topic of "Lecture 02," could you please p… |
| Give me one review question from Lecture 02 | Pydantic AI agent | `make_quiz(2)` | 2/2 | Here is a review question from Lecture 02: **Question:** What does "Rank (LoRA r)" mean? … |
<!-- /AUTO:exercise -->

- Differences between the Lecture 1 (bare LLM) answer and the agent's:
  The bare model (`app.ask`, no tools) did not know the course. In both runs it made up a generic scheme ("Level 1: Beginner / Core", "Level 2: Intermediate / Applied", "Level 3: Advanced / Capstone") and in run 1 tied the course to an "Advanced AI Engineering bootcamp". The real levels are Basic (review the lecture), Implementation (write your own code) and Advanced (research and experimentation). The agent gave the real three levels in all runs, said that completing any one finishes the homework and that it is generally not graded, and ended with `(Lecture 01)`, as the glossary says. The other two exercise questions went the same way: asked for a review question from Lecture 02, the bare model asked which course I meant (run 1) or made up a Python list-versus-tuple question (run 2), and for "What will we learn in Lecture 03?" it asked which course I meant, while the agent called `make_quiz` and `get_lecture_summary` and answered from the course material.
- Tool calls shown by `--trace` (tool names and arguments):
  The two `--trace` runs from the exercise (command line, default model):

  ```text
  [tool call]   search_glossary({'query': 'LoRA'})
  [tool call]   search_glossary({'query': 'QLoRA'})
  [usage] RunUsage(cost=Decimal('0.0010510'), details={'text_prompt_tokens': 1445}, input_text_tokens=1445, input_tokens=1445, output_tokens=247, requests=2, tool_calls=2)

  [tool call]   make_quiz({'lecture': 2})
  [usage] RunUsage(cost=Decimal('0.0004816'), details={'text_prompt_tokens': 1047}, input_text_tokens=1047, input_tokens=1047, output_tokens=67, requests=2, tool_calls=1)
  ```

  LoRA and QLoRA were searched one term per call, as the `search_glossary` docstring asks, and `make_quiz` got `lecture` as the integer 2. The comparison runs (table above) did the same in every run. For the `levels` question the Pydantic AI agent searched differently from that: in both runs it called `get_lecture_summary` for lectures 1 to 5 and then `search_glossary('homework')` (run 2: `'homework level'`), and the ADK agent made one call, `search_glossary('homework levels')`.
- Number of LLM calls for one question (`requests`):
  The bare model always makes 1 request. The agent made 2 requests for `lora-qlora` (2 tool calls), 2 for `quiz` (1 tool call), 2 for `summary` and 2 for `unknown`: one request that asks for the tool and one that writes the answer. The two searches for LoRA and QLoRA were asked for in the same request, so 2 tool calls cost only 2 requests. The exception is `levels` on Pydantic AI: 7 requests for 6 tool calls, in both runs, with about 11,200 input tokens against 1,185 for the same question on ADK.
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
| Question | Pydantic AI tool calls (run 1) | ADK tool calls (run 1) | Same tool order in every run | Requests (Pydantic AI, mean) | Requests (ADK, mean) | Seconds (Pydantic AI, mean) | Seconds (ADK, mean) | Tokens in / out (Pydantic AI, mean) | Tokens in / out (ADK, mean) |
|---|---|---|---|---|---|---|---|---|---|
| levels | `get_lecture_summary(1)`, `get_lecture_summary(2)`, `get_lecture_summary(3)`, `get_lecture_summary(4)`, `get_lecture_summary(5)`, `search_glossary('homework')` | `search_glossary('homework levels')` | no | 7.0 | 2.0 | 7.3 | 2.2 | 11226 / 178 | 1185 / 108 |
| lora-qlora | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | `search_glossary('LoRA')`, `search_glossary('QLoRA')` | yes | 2.0 | 2.0 | 3.2 | 2.8 | 1445 / 242 | 1569 / 262 |
| quiz | `make_quiz(2)` | `make_quiz(2)` | yes | 2.0 | 2.0 | 2.2 | 1.8 | 1020 / 79 | 1140 / 50 |
| summary | `get_lecture_summary(3)` | `get_lecture_summary(3)` | yes | 2.0 | 2.0 | 2.3 | 2.3 | 1333 / 255 | 1459 / 252 |
| unknown | `search_glossary('vector database')` | `search_glossary('vector database')` | yes | 2.0 | 2.0 | 2.1 | 1.8 | 959 / 121 | 1085 / 25 |
<!-- /AUTO:comparison -->

The answers (run 1, shortened; the full text is in `results/compare/runs.json`):

<!-- AUTO:answers -->
| Question | Pydantic AI answer (run 1, shortened) | ADK answer (run 1, shortened) |
|---|---|---|
| levels | The three homework levels in the AIE2026 course are: 1. **Basic**: Review the lecture content. 2. **Implement… | The three homework levels in the AIE2026 course are: 1. **Basic**: Review lecture content. 2. **Implementatio… |
| lora-qlora | To understand the difference between LoRA and QLoRA, it helps to look at how each handles model weights to sa… | To understand the difference between **LoRA** and **QLoRA**, let's look at how each approach handles model we… |
| quiz | Here is a review question from Lecture 02: **Question:** What does "Rank (LoRA r)" mean? Give it a try! If yo… | Here is a review question from Lecture 02: **What does "Overfitting" mean?** Give it your best shot! Let me k… |
| summary | In Lecture 03, you will learn about **AI Agents**. The main topics and aims include: * **Basic structure of a… | In Lecture 03, you will focus on **AI Agents**. Here are the main aims and topics covered: - **The Basic Stru… |
| unknown | It is not in the glossary. To help you think about it: in AI engineering, we often convert data (like text, i… | It is not in the glossary. |
<!-- /AUTO:answers -->

What the runs showed:

- **Tools and instructions:**
  The tool calls had the same names in the same order on 4 of the 5 questions (`lora-qlora`, `quiz`, `summary`, `unknown`), in both runs and on both frameworks. The exception is `levels`. ADK made one call, `search_glossary('homework levels')`, in both runs. Pydantic AI made six calls in both runs: `get_lecture_summary` for lectures 1 to 5, then a glossary search. Both agents use the very same instructions text and docstrings, and both answered correctly, so the text does not explain the difference. I did not find the cause. It could be sampling (2 runs each is too few to rule it out, although all 4 runs agree inside each framework) or a difference in what each framework sends with the request; I did not test either.
- **Answers:**
  The `levels` answer was correct in all four agent runs (the three real levels, any one completes the homework, not graded); in ADK run 1 the ending was `(Lecture 1)` and not `(Lecture 01)`. On `quiz`, both agents asked the question without giving the answer, as the `make_quiz` docstring says; the term is random, so the questions differ (Pydantic AI: "Rank (LoRA r)" and "LoRA", ADK: "Overfitting" and "LoRA"), and Pydantic AI added a hint in run 2. The clearest difference is `unknown` ("What is a vector database?"). ADK answered exactly "It is not in the glossary." in both runs. Pydantic AI also said that, and then added its own explanation of what a vector database is (a hint in run 1, a definition in run 2 with a note that the glossary does not define it), and run 1 ended with `Lecture 03`. The instruction says to say it is not in the glossary instead of making assertions based on guesses, so ADK followed it more strictly here. The bare model gave a full textbook definition with no sign that the course does not cover it.
- **Cost of the loop:**
  Over the 10 runs of each agent, Pydantic AI used 30 requests, 31,967 input tokens, 1,750 output tokens and 34.1 s; ADK used 20 requests, 12,877 input tokens, 1,394 output tokens and 21.6 s. Almost all of the gap is the `levels` question (7 against 2 requests, 11,226 against 1,185 input tokens on average, 7.3 s against 2.2 s). On the other four questions both used the same number of requests (16 in total each), and ADK sent about 120 more input tokens per run (9,514 against 10,507 over the 8 runs of each). One known reason is that ADK adds the sentence "You are an agent. Your internal name is \"glossary_agent\"." to the instructions (seen in the offline test), but that is only about 15 tokens, and I did not look into the rest. The times of the two are close on those four questions (ADK was faster on three of them by 0.3 to 0.4 s, and equal on one); this is small, and network time varies from call to call. The seconds do not include the 65 s wait before the retry described in the notes. The bare model always used 1 request and 7 to 18 input tokens, since it has no tools and no instructions to send.
- **`adk run`:**
  I started `adk run` with the course's command, answered `n` to its telemetry question, and typed the Lecture 1 question. It printed (shortened to the answer):

  ```text
  [user]: What are the 3 homework levels in the AIE2026 course?
  [glossary_agent]: In the AIE2026 course, the 3 homework levels are:
  1. **Basic**: Review lecture content.
  2. **Implementation**: Write your own code.
  3. **Advanced**: Research and experimentation.
  Completing *any one* of these levels is enough to finish the homework for that lecture, and as a rule, homework is not graded.
  (Lecture 01)
  ```

  This matches the code runs (and the glossary). `adk run` shows only the answer: it does not print which tool was called, so the trace has to come from the event stream, which is what `app/compare.py` reads.
- **Run-to-run differences:**
  The tool names did not change between run 1 and run 2 of any question on either framework (on `levels`, Pydantic AI changed only the search text, `'homework'` against `'homework level'`). The wording changed in every run, and the quiz term changed because `make_quiz` picks it at random. The small gap in the ending, `(Lecture 1)` once on ADK and `Lecture 02` without brackets once on Pydantic AI, shows that the "(Lecture NN)" format in the instructions is followed most of the time but not always.

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
- **Which I would use:** On these runs I would build a small agent like this with ADK: it gave the same correct answers, used 20 requests against 30, and followed the "not in the glossary" rule more strictly. My evidence is thin, though: 2 runs per question, and most of the difference comes from one question where Pydantic AI took a path I could not explain. For learning and testing I would still pick Pydantic AI, because the exercise's `--trace`, `--list-tools` and `TestModel` come with it, while for ADK I had to write my own fake model and my own event reader. So: Pydantic AI for building and checking an agent, and ADK worth a second look when token cost per question matters.

### Notes

- Offline tests (`uv run --group adk pytest -q`, no key and no network): the tools including `make_quiz` and its edge cases (lectures 0, 4, 99),
  the agent's wiring with `TestModel`, the ADK agent with a scripted fake model (same instructions object, same tool names, descriptions
  and argument types, the loop calls the tool and gives the result back, request and token counting), the live runner (retries, failure
  recording, merging runs), the report tables, and a scan that no API key is in the folder. `adk run` was started once with a dummy key to
  confirm it finds and loads `adk_agent/glossary_agent`; it then stopped at the network call, as expected without a key. They say nothing
  about what Gemini does with these prompts; only the live runs do.
- The comparison is small: 5 questions, 2 runs each, one model, one day. Model answers change between runs, so a difference of one tool call
  or one request between the two frameworks is not evidence of a framework difference.
- The live runs were on November 3, 2026 (the 30 comparison runs between about 09:35 and 09:40 UTC), with the default model `gemini-3.5-flash-lite` and `AIE_MODEL` not set, on Windows with Python 3.14. All 30 runs succeeded. One run, `adk:lora-qlora:1`, got a 429 (the free tier's limit of 15 requests per minute) and succeeded on its second attempt after the 65 s wait; it is recorded with `attempts: 2`. After each ADK run Windows printed a long `RuntimeError: Event loop is closed` traceback from the Google client library closing its connection; it comes after the answer was saved and did not change any result.
- I ran every live command myself; the numbers above come from `results/compare/runs.json` and the pasted terminal output. AI tools helped me write the code, the tests and the wording of this file.
