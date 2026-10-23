# Lecture 1 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-01`

## Exercise

- Model's answer to the course-specific question (the "3 levels" of the homework), summarized:
  I asked `gemini-3.5-flash-lite` the question three times with `app.ask`. It never gave the real meaning. Runs 1 and 3
  began by saying it had no access to the syllabus (or that the answer depends on my instructor) and then listed generic
  frameworks anyway: levels of AI autonomy, ML integration, prompt engineering and homework difficulty tiers. Run 2
  sounded more sure of itself ("Based on the standard curriculum for the AIE2026 course") and even tied the course to an
  unrelated program. All three answers ended by asking me for more context.
- What I noticed when comparing it with the correct meaning:
  The correct meaning (`homework-levels` in the course repo's `data/glossary.json`) is Basic (check the lecture
  content), Implementation (write the code yourself) and Advanced (investigate and experiment). Doing any one of them
  completes that week's homework, and it is generally not graded. The model never said this. Its closest guess was a
  generic Basic / Intermediate / Advanced homework tier (runs 2 and 3). That has a similar shape but the wrong content
  (getting code to run, error handling, deploying). The answer also changed on every run. So the model cannot be trusted
  on course-specific facts unless it is given the source material.
- Token counts displayed (input / output): "What is LoRA?" gave input 6 and output 663. The "3 levels" question gave
  input 19 every time and output 590, 563 and 545. The input count stayed the same because the prompt was identical,
  while the output count changed with each answer. The code that prints them is in `app/ask.py`.

## Homework

- **Level chosen:** Advanced (measure response time and tokens, compare across models and questions, and discuss the
  free-tier rate limits)

### What I did

I wrote `app/benchmark.py`. For every model and question it sends the same question several times, one request at a time,
and records the response time and the input, output and thinking token counts.

- **Questions (3):** `general-short` ("What is LoRA?"), `course-specific` (the "3 levels" question, which a plain model
  cannot know) and `long-answer` (LoRA versus QLoRA with an example, to get a longer output).
- **Models (2):** `gemini-3.5-flash-lite` (course default, 3 runs per question = 9 requests) and `gemini-3.8-flash`
  (the stronger model, 2 runs per question = 6 requests). All 15 requests were sent in one run on October 23, 2026. I did
  not repeat the run because the stronger model has a small daily allowance.
- **Response time** is the wall-clock time of the API call only. It includes network and server time (queueing and
  thinking) and excludes the pacing sleeps between requests.
- **Tokens:** input and output come from `response.usage_metadata`. Thinking tokens are shown separately because
  they are billed like output but are not part of the visible answer.
- **Pacing:** requests to one model are spaced at least 5 s apart for `flash-lite` and 13 s apart for `3.8-flash`,
  which keeps them under the per-minute limits measured in class.
- **Failures are recorded, not hidden:** a 429, a 503 or an empty answer becomes a row in the results with its error,
  and does not count toward the averages. After 3 failures in a row the rest of that model is skipped so a bad run
  cannot burn the daily quota.
- The run reported below is saved in `results/` as `benchmark_20261023_165400.csv` (one row per request),
  `benchmark_20261023_165400.json` (the same plus the full answers) and `summary_20261023_165400.md` (the table below).

Commands used:

```bash
uv run python -m app.benchmark --dry-run
uv run python -m app.benchmark
```

### Results

15 requests took 473 s in total. The latency columns are in seconds and use only the successful requests.

| Model | Question | OK / requests | 429 | 503 | Latency mean (s) | median | min | max | Input tokens | Output tokens | Thinking tokens | Output tokens/s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemini-3.5-flash-lite | general-short | 3 / 3 | 0 | 0 | 3.03 | 3.01 | 2.87 | 3.21 | 6.0 | 632.3 | 0.0 | 208.8 |
| gemini-3.5-flash-lite | course-specific | 3 / 3 | 0 | 0 | 2.95 | 2.94 | 2.78 | 3.14 | 19.0 | 611.0 | 0.0 | 206.8 |
| gemini-3.5-flash-lite | long-answer | 3 / 3 | 0 | 0 | 2.82 | 2.73 | 2.70 | 3.04 | 22.0 | 651.0 | 0.0 | 231.5 |
| gemini-3.5-flash-lite | ALL | 9 / 9 | 0 | 0 | 2.94 | 2.94 | 2.70 | 3.21 | 15.7 | 631.4 | 0.0 | 215.7 |
| gemini-3.8-flash | general-short | 2 / 2 | 0 | 0 | 79.60 | 79.60 | 39.84 | 119.35 | 6.0 | 825.0 | 886.5 | 13.4 |
| gemini-3.8-flash | course-specific | 1 / 2 | 0 | 1 | 32.27 | 32.27 | 32.27 | 32.27 | 19.0 | 503.0 | 1242.0 | 15.6 |
| gemini-3.8-flash | long-answer | 2 / 2 | 0 | 0 | 112.65 | 112.65 | 63.15 | 162.15 | 22.0 | 735.0 | 917.0 | 8.5 |
| gemini-3.8-flash | ALL | 5 / 6 | 0 | 1 | 83.35 | 63.15 | 32.27 | 162.15 | 15.0 | 724.6 | 969.8 | 11.9 |

- Response time, `gemini-3.5-flash-lite` vs `gemini-3.8-flash`: flash-lite averaged 2.94 s per request (range 2.70 to
  3.21 s). gemini-3.8-flash averaged 83.35 s (range 32.27 to 162.15 s), about 28 times slower. Even its fastest call
  was about 10 times slower than the slowest flash-lite call.
- Response time by question (short vs long answer): On flash-lite the question made almost no difference: general-short
  3.03 s, course-specific 2.95 s, long-answer 2.82 s. The long-answer question did not even produce a longer answer
  (651 output tokens on average vs 632 for "What is LoRA?"). On gemini-3.8-flash the means were 79.60 s, 32.27 s and
  112.65 s, but each one comes from only one or two successful runs and is dominated by run-to-run variation (see below),
  so I cannot say the question itself caused the difference.
- Output tokens and thinking tokens by model and question: flash-lite used no thinking tokens and wrote between 578 and
  676 output tokens per call, whichever question it was. gemini-3.8-flash wrote 503 to 878 visible output tokens per call
  and, on top of that, 819 to 1,242 thinking tokens per call (mean 969.8, more than its visible output). Input tokens were
  identical in every run of a question (6, 19 and 22) because the prompt was the same. The "Output tokens/s" column
  counts only visible output, so it understates how much work gemini-3.8-flash does.
- Did the course-specific question get a different kind of answer (refusal vs confident guess), and was it consistent
  across runs? Neither model gave the real meaning, and both did the same thing: they said the definition depends on the
  institution or syllabus, then guessed with generic lists, then asked me for more context. flash-lite did this in all
  three benchmark runs (and in my three earlier `app.ask` runs), each time with a somewhat different mix of frameworks.
  gemini-3.8-flash has only one successful answer to this question, because its second run returned a 503, so I cannot
  judge its consistency. That answer offered three candidate frameworks: homework difficulty tiers (labelled "most
  common": core, optimization, challenge), David Marr's three levels of analysis, and prompting or agent levels. It did
  not name Basic, Implementation and Advanced. Its first guess has the right general shape but the wrong content.
- Run-to-run variation (min and max latency for the same question): flash-lite was very consistent (every question stayed
  within about 0.5 s). gemini-3.8-flash was not. For general-short, run 2 took 119.35 s vs 39.84 s in run 1 (3.0 times
  longer), and for long-answer 162.15 s vs 63.15 s (2.6 times longer). The total tokens (visible plus thinking) were almost
  the same in the two runs (1,699 vs 1,724 and 1,648 vs 1,656), so the effective speed fell from about 43 to 14 tokens per
  second and from about 26 to 10. Token count does not explain the slowdown. I cannot tell the cause from my data; server
  load or queueing at the time are possible explanations, which fits the 503 "high demand" error in the same run.
- Other differences I saw when reading the answers: for "What is LoRA?", both gemini-3.8-flash answers also pointed out
  the other meaning of the word (LoRa, Long Range, the wireless technology), while flash-lite never mentioned it in its
  three runs. For LoRA vs QLoRA, both models gave the same core comparison (16-bit base model for LoRA, 4-bit for QLoRA,
  an A100-class GPU for LoRA and a consumer GPU for QLoRA). gemini-3.8-flash added more specific figures, but its two runs
  quoted different memory savings (65 to 75% in run 1, about 60% in run 2). I did not check these figures for accuracy.
- Anything that did not work or showed no difference: one request failed. gemini-3.8-flash, course-specific, run 2
  returned a 503 (the model reported high demand). It was recorded as a failed row and left out of the averages, so that
  cell rests on a single run. There were no 429 errors. On flash-lite the long-answer question showed no difference in
  output length or time compared with the short question.

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
- Observed: number of 429s and 503s, and whether the pacing avoided them: no 429s on either model. One 503, on
  gemini-3.8-flash. The pacing (5 s for flash-lite, 13 s for 3.8-flash) avoided every rate-limit error.
- Observed: effective requests per minute I reached, and how that compares with the limit: 15 requests in 473 s is about
  1.9 per minute overall. flash-lite was held back only by its 5 s spacing, which allows up to 12 per minute (limit 15).
  gemini-3.8-flash stayed under 1 per minute, because each of its calls took 32 to 162 s, longer than the 13 s spacing. So
  the per-minute limit of 5 was never close. The real constraints for 3.8-flash were its long latency, the 503, and the small
  daily allowance: I sent 6 requests to it today (one returned 503), which is 30% to 60% of 10 to 20 per day, so I will not
  repeat the full run.
- Conclusion: for repeated experiments I would use gemini-3.5-flash-lite: about 3 s per call, very consistent, no failures
  in 9 requests, and an allowance of 500 per day. I would keep gemini-3.8-flash for a few one-off checks, since it was
  about 28 times slower, failed once, and its daily allowance is easy to use up. For these three simple questions the extra
  detail it gave did not seem worth that waiting time, but I only compared the answers by reading them, not for accuracy,
  and this is one run on one day, so server load may have affected the result.

### What I verified myself

- [x] Ran the exercise questions and the benchmark with my own key on my own computer
- [ ] Read `app/benchmark.py` and can explain how latency, pacing and failure handling work
- [ ] Opened the CSV and the JSON in `results/` and read at least one answer from each model
- [ ] Checked that no API key appears in `results/`, `answer.md` or any screenshot

### Notes

- The offline tests cover the script (`uv run pytest -q`, 48 tests): pacing, latency measurement, retries, failure
  recording and the summary maths, plus a run of the real SDK against a local fake server that returns a 503.
  They say nothing about Gemini's actual speed or limits; only the live run does.
- Also in the folder, outside the chosen level: a chat mode in `app/ask.py` that keeps the conversation history
  (`uv run python -m app.ask --chat`). It is not part of this submission's results.
- No API key appears in any file (a test scans this folder for both Google key formats).
