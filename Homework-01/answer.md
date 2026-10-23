# Lecture 1 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-01`

<!-- Fill in every "TODO (live run)" after running the commands, then delete this comment. -->

## Exercise

- Model's answer to the course-specific question (the "3 levels" of the homework), summarized:
  `TODO (live run)`: run `uv run python -m app.ask "In the AIE2026 course homework, what are the '3 levels'?"` and summarize what it said.
- What I noticed when comparing it with the correct meaning:
  `TODO (live run)`.
  Reference for the comparison (`homework-levels` in the course repo's `data/glossary.json`): the three levels are
  Basic (check the lecture content), Implementation (write the code yourself) and Advanced (investigate and experiment).
  Doing any one of them completes that week's homework, and it is generally not graded.
- Token counts displayed (input / output): `TODO (live run)`, e.g. from `uv run python -m app.ask "What is LoRA?"`.
  The code that prints them is in `app/ask.py`.

## Homework

- **Level chosen:** Advanced (measure response time and tokens, compare across models and questions, and discuss the
  free-tier rate limits)

### What I did

I wrote `app/benchmark.py`. For every model and question it sends the same question several times, one request at a time,
and records the response time and the input, output and thinking token counts.

- **Questions (3):** `general-short` ("What is LoRA?"), `course-specific` (the "3 levels" question, which a plain model
  cannot know) and `long-answer` (LoRA versus QLoRA with an example, to get a longer output).
- **Models (2):** `gemini-3.5-flash-lite` (course default, 3 runs per question = 9 requests) and `gemini-3.8-flash`
  (the stronger model, 2 runs per question = 6 requests). `TODO (live run)`: change this line if I used a different plan.
- **Response time** is the wall-clock time of the API call only. It includes network and server time (queueing and
  thinking) and excludes the pacing sleeps between requests.
- **Tokens:** input and output come from `response.usage_metadata`. Thinking tokens are shown separately because
  they are billed like output but are not part of the visible answer.
- **Pacing:** requests to one model are spaced at least 5 s apart for `flash-lite` and 13 s apart for `3.8-flash`,
  which keeps them under the per-minute limits measured in class.
- **Failures are recorded, not hidden:** a 429, a 503 or an empty answer becomes a row in the results with its error,
  and does not count toward the averages. After 3 failures in a row the rest of that model is skipped so a bad run
  cannot burn the daily quota.
- Raw results (CSV and JSON with the full answers) and the summary table are in `results/`.

Commands used (`TODO (live run)`: paste the exact ones I ran):

```bash
uv run python -m app.benchmark --dry-run
uv run python -m app.benchmark
```

### Results

`TODO (live run)`: paste the summary table from `results/summary_<time>.md` here.

- Response time, `gemini-3.5-flash-lite` vs `gemini-3.8-flash`: `TODO (live run)`
- Response time by question (short vs long answer): `TODO (live run)`
- Output tokens and thinking tokens by model and question: `TODO (live run)`
- Did the course-specific question get a different kind of answer (refusal vs confident guess), and was it consistent across runs? `TODO (live run)`
- Run-to-run variation (min and max latency for the same question): `TODO (live run)`
- Anything that did not work or showed no difference, recorded as it happened: `TODO (live run)`

### Free-tier rate limits

Limits measured in class (they can change, so I check AI Studio for my own key):

| Model | Requests per minute | Requests per day |
|---|---|---|
| `gemini-3.5-flash-lite` | 15 | 500 |
| `gemini-3.8-flash` | 5 | about 10 to 20 (may return 503) |

What follows from the numbers:

- At 5 requests per minute, sending the 6 requests to `gemini-3.8-flash` back to back would put 6 requests inside one
  minute, over the limit. With 13 s between starts they take about 65 seconds (5 gaps), which stays under it.
  That is why the script paces requests.
- The daily budget is the tighter limit for the stronger model: 6 requests are 30% to 60% of 10 to 20 per day, so the
  whole experiment can be repeated only once or twice a day. The 9 requests to `flash-lite` use under 2% of its 500.
- The glossary notes that limits can be counted in requests or in tokens, so a long answer (many output and thinking
  tokens) can cost more of the allowance than a short one even though it is still one request.
- Observed: number of 429s and 503s, and whether the pacing avoided them: `TODO (live run)`
- Observed: effective requests per minute I reached, and how that compares with the limit: `TODO (live run)`
- Conclusion: which model I would use for repeated experiments and which for a few checks, and why: `TODO (live run)`

### What I verified myself

`TODO (live run)`: tick only what I actually did.

- [ ] Read `app/benchmark.py` and can explain how latency, pacing and failure handling work
- [ ] Ran the benchmark with my own key and opened the CSV to check that the numbers match the summary table
- [ ] Compared at least one answer from each model by reading it, not only the numbers
- [ ] Checked that no API key appears in `results/`, `answer.md` or any screenshot

### Notes

- The offline tests cover the script (`uv run pytest -q`, 48 tests): pacing, latency measurement, retries, failure
  recording and the summary maths, plus a run of the real SDK against a local fake server that returns a 503.
  They say nothing about Gemini's actual speed or limits; only the live run does.
- Also in the folder, outside the chosen level: a chat mode in `app/ask.py` that keeps the conversation history
  (`uv run python -m app.ask --chat`). It is not part of this submission's results.
- No API key appears in any file (a test scans this folder for both Google key formats).
