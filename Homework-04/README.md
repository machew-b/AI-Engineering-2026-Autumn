# Homework 04: Model Evaluation and Problem Formulation

Level chosen: **Advanced** (investigate one benchmark dataset: read some of its problems, find out who made it and how it was validated, and
compare it with the exercise's 10-item evaluation set; no code is written). The benchmark is **SWE-bench Verified**.
The in-class exercise (label the 10 items, have an LLM grade them, fix one rubric criterion, grade again) is also done and recorded.

The write-up is in [`answer.md`](./answer.md): the `Exercise` section and the `Homework` section.

## What is in this folder

| Path | What it is |
|------|------------|
| `answer.md` | The submission write-up |
| `results/labels.jsonl` | My STEP 1 labels for the 10 items (`tools/annotate.py` output) |
| `results/judge_result_before.json` | `app.judge` output before the rubric change (agreement, review items, disagreements, reasons) |
| `results/judge_result_after.json` | `app.judge` output after the rubric change |
| `results/rubric_after.md` | `data/eval/rubric.md` after the one policy line was added |
| `.gitignore` | Keeps keys and virtual environments out of git |

The course repo is `matsuolab/lecture-ai-engineering-2026-en`. This repo is a standalone repo, not a fork, so there is no Sync fork, no `lec04`
branch and no pull request: everything is on `main`, as in Homeworks 1 to 3. The Advanced level needs no code, so this folder has no `app/`,
`tests/`, `pyproject.toml` or `uv.lock`; that is the one difference in structure from Homeworks 1 to 3. The exercise tools
(`tools/annotate.py`, `app/judge.py`) stay in the course repo.

## How the exercise results were produced

In a clone of the course repo, with `uv sync --frozen` and the Gemini key set only as an environment variable in the terminal (not stored in any
file). Commands were run as `uv run python -m ...` because Windows blocked the `pytest` and `streamlit` launchers.

```powershell
uv run --with streamlit==1.66.1 python -m streamlit run tools/annotate.py             # STEP 1: labels
uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl    # compare with the instructor, no key needed
uv run python -m app.judge --wait 2                                                   # STEP 2: LLM grading (before)
# edit data/eval/rubric.md: add one Grounding line, remove the matching Unresolved Question
uv run python -m app.judge --wait 2                                                   # STEP 3: grade again (after)
```

Both grading runs used `gemini-3.1-flash-lite` (set with `AIE_MODEL`), because the default `gemini-3.5-flash-lite` returned a 503 "model is busy" error twice.

## Research for the Advanced level

Done on November 11, 2026, with no code: the SWE-bench paper, OpenAI's "Introducing SWE-bench Verified" post and annotation instructions,
OpenAI's February 2026 post on why it stopped using the benchmark, four task pages (astropy, django, sympy, pylint), and the exercise's own
files in the course repo. The sources and what each was used for are in the Sources table of `answer.md`.
