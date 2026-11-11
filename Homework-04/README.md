# Homework 04: Model Evaluation and Problem Formulation

Level chosen: **Advanced** (investigate one benchmark dataset: read some of its problems, find out who made it and how it was validated, and
compare it with the exercise's 10-item evaluation set; no code is written).
The benchmark is **SWE-bench Verified**. The write-up is in [`answer.md`](./answer.md).

## What is in this folder

| Path | What it is |
|------|------------|
| `answer.md` | The submission write-up: the `Exercise` section (still to be filled in after the live run) and the `Homework` section (done) |
| `EXERCISE-GUIDE.md` | Step-by-step guide for the in-class exercise (label the 10 items, have the LLM grade them, fix one rubric criterion, grade again) |
| `results/` | Where the exercise output files go (`labels.jsonl`, `judge_result_before.json`, `judge_result_after.json`, `rubric_after.md`); see `results/README.md` |
| `.gitignore` | Keeps keys and virtual environments out of git |

The course repo is `matsuolab/lecture-ai-engineering-2026-en`. This repo is a standalone repo, not a fork, so there is no Sync fork, no `lec04`
branch and no pull request: everything is on `main`, as in Homeworks 1 to 3. The Advanced level needs no code, so this folder has no `app/`,
`tests/`, `pyproject.toml` or `uv.lock`; that is the one difference in structure from Homeworks 1 to 3. The exercise tools (`tools/annotate.py`,
`app/judge.py`) stay in the course repo and are used from a clone of it (see `EXERCISE-GUIDE.md`).

## What I did

The research was done on November 11, 2026, with no code and no API key:

1. Chose SWE-bench Verified from the table in the slides (reasons in `answer.md`).
2. Read four of its tasks (an astropy, a django, a sympy and a pylint task) and noted what each asks and what would be hard.
3. Looked up the creation and validation procedure in the SWE-bench paper, OpenAI's "Introducing SWE-bench Verified" post and annotation
   instructions, and OpenAI's February 2026 post on why it stopped using the benchmark.
4. Read the exercise's own files in the course repo (the 10 cases, `rubric.md`, the instructor's labels) and compared the two sets on scale,
   number of people validating and scoring method.

## Before you submit

The `Homework` section in `answer.md` is written from sources that were read with the help of an AI tool (see its Notes). The submission
slide says to write down what you verified yourself, so do this and then edit the "AI tools" line at the end of `answer.md` to say what you checked:

1. Open the four task pages listed in the Sources table of `answer.md` and confirm that each issue says what the table says (about 5 minutes).
2. Open the three OpenAI pages and the arXiv paper and confirm the numbers (93 developers, 1,699 samples, 3 labels per sample, 68.3% removed,
   500 final, 138 audited, 59.4%). The first OpenAI post lists most of them in one place.
3. Optional: open the dataset on Hugging Face (`princeton-nlp/SWE-bench_Verified`) and look up the four `instance_id` values in the viewer.
4. Fill in the `Exercise` section by following `EXERCISE-GUIDE.md`, then set Homework 04 to `Finished` in the top-level `README.md`.
