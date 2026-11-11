# Guide: finishing the Lecture 4 exercise

The exercise needs your own labels and a live run of the grader with your Gemini key, so it is not filled in yet. It takes about 30 minutes.
The tools live in the course repo, and your homework repo is not a fork, so run them from a separate clone. Nothing here changes the course repo.

## 0. Set up (about 3 minutes)

```bash
git clone https://github.com/matsuolab/lecture-ai-engineering-2026-en.git
cd lecture-ai-engineering-2026-en
```

Set your key for this terminal only (do not write it into any file):

```powershell
# Windows PowerShell
$env:GEMINI_API_KEY = "your-key"
```

```bash
# macOS, Linux, Codespaces
export GEMINI_API_KEY="your-key"
```

You do not need the `lec04` branch or a pull request, because the results are submitted from your homework repo.

## 1. STEP 1: label the 10 items (about 8 minutes)

```bash
uv run --with streamlit==1.66.1 streamlit run tools/annotate.py
```

The first start takes 1 to 2 minutes. Open http://localhost:8501 if no browser tab opens.

- For each item, judge Grounding, Scope, Hint, Clarity and Lecture indicator (pass or fail), using the reference shown on the left and the
  criteria, not your own knowledge. If you cannot decide from the criteria, tick "Unsure" and move on (about 40 seconds per item).
- Click "Save and next" on every item, including item 10. The labels are saved to `lectures/04/labels.jsonl`.
- Do not open `lectures/04/reference/` before you have finished. The instructor's labels are not an answer key, but looking first removes the point of the comparison.

Then compare with the instructor's labels:

```bash
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
```

Write down the items where you differ and why (this is one of the six bullets in `answer.md`).

## 2. STEP 2: have the LLM grade the same items (about 5 minutes)

```bash
uv run python -m app.judge
```

- If it says "Rate limit reached", wait 1 minute, or add `--wait 2`, or set `AIE_MODEL=gemini-3.1-flash-lite`.
- `--model test` only runs the flow with a fake model. Do not use its numbers for the homework.
- Copy the result before the next step: `lectures/04/judge_result.json` to `Homework-04/results/judge_result_before.json`.
- From the printed output, write down: the agreement per criterion (for example `Grounding 8/9`), the overall agreement and coverage, the number
  of items needing review (and which), and the disagreements (misses and over-detections). Clarity is expected to be the lowest.

## 3. STEP 3: fix one criterion and grade again (about 8 minutes)

1. Take one item from "Needs review" (expected: #05 "What is RAG?", Grounding). If there are none, take an item you marked "Unsure" in STEP 1.
2. Decide whether it should pass or fail. Either is acceptable, but make the policy match what you labeled for that item in STEP 1.
   If you marked #05 as unsure, a policy of **fail** is the one that fits the Lecture 3 instruction ("do not make definitive claims by guessing
   about things not in the glossary") and what Homework 3 found (the ADK agent answered only "It is not in the glossary", and that followed the instruction more strictly).
   With a fail policy, the grader can only check an extra general explanation against an empty reference, so it cannot confirm it.
3. In `data/eval/rubric.md` add one or two lines under the criterion, for example under Grounding:
   `- A general explanation of an absent term, even after saying it is not in the glossary, counts as an unsupported assertion (fail)`,
   and delete that question from "Unresolved Questions". Change only this one thing.
4. Run `uv run python -m app.judge` again. Copy `lectures/04/judge_result.json` to `Homework-04/results/judge_result_after.json` and `data/eval/rubric.md`
   to `Homework-04/results/rubric_after.md`. Also copy `lectures/04/labels.jsonl` to `Homework-04/results/labels.jsonl`.
5. Write down: the number of items needing review after the change, and what happened to that item's judgment and to the other criteria.
   If the number did not go to 0, or something else changed, say so; "it did not change" is also a result.

## 4. Fill in `answer.md` and submit

1. In `Homework-04/answer.md`, replace each `TODO(exercise)` line in the `Exercise` section with your numbers and observations, and delete the
   "Status" paragraph. Keep the wording in the same style as the other sections.
2. Check that no key is in any file you are about to commit.
3. From your homework repo:

```bash
git add -A
git commit -m "Homework 04 exercise results"
git push origin main
```

4. In the top-level `README.md`, set Homework 04 to `Finished` and put the date you submitted.
