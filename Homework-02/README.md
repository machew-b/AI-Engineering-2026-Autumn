# Homework 02: Fundamentals of Foundation Models

Level chosen: **Advanced** (build Q&A data from the course glossary, train it into a small model with LoRA, compare
before and after, and compare with a system that searches the glossary).
The write-up is in [`answer.md`](./answer.md). The step-by-step instructions for the Colab runs are in [`GUIDE.md`](./GUIDE.md).

## What is in this folder

| Path | What it is |
|------|------------|
| `notebooks/lora_glossary_tuning.ipynb` | The Colab notebook (T4 GPU): base model before, LoRA training, after, side by side with glossary search |
| `app/glossary_data.py` | Builds the training data and the 58-question test set from the glossary (standard library only) |
| `app/scoring.py` | Scores answers: key phrases for glossary terms, "not in the glossary" for unknown terms |
| `app/retrieval.py` | The comparison system: a plain glossary lookup (`uv run python -m app.retrieval`) |
| `app/report.py` | Turns the files downloaded from Colab into the tables in `answer.md` |
| `scripts/make_sft_dataset.py` | The course script, extended: writes the JSONL files so you can read them |
| `data/glossary.json` | Snapshot of the course glossary (`version: 2026-draft-1`), copied from `matsuolab/lecture-ai-engineering-2026` |
| `results/` | `retrieval_baseline.json/.md` (measured offline), plus `exercise/`, `run_a/`, `run_b/` from the Colab runs |
| `tests/` | Offline tests: data split and leakage, scoring, glossary search, report tables, notebook consistency, secret scan |
| `answer.md` | The submission write-up |

The course repo is `matsuolab/lecture-ai-engineering-2026`. This repo is a standalone repo, not a fork, so the files used
(the glossary, the dataset script idea, the notebook settings) were copied here.

## Run it

```bash
cd Homework-02
uv run pytest -q                          # offline, no GPU and no key needed
uv run python -m app.retrieval            # glossary-search baseline -> results/retrieval_baseline.*
uv run python scripts/make_sft_dataset.py --out-dir data/generated   # look at the data (ignored by git)
uv run python -m app.report               # print the result tables (after the Colab runs)
uv run python -m app.report --write       # put them into answer.md
uv run python -m app.report --check       # list what is still unfinished in answer.md
```

The training itself needs a GPU, so it runs in Google Colab (free T4), not here. Open the notebook with
https://colab.research.google.com/github/machew-b/AI-Engineering-2026-Autumn/blob/main/Homework-02/notebooks/lora_glossary_tuning.ipynb

## Steps that need my own accounts

1. A Google account for Colab (no API key is needed in this homework).
2. Run the course exercise notebook once, then run A (and optionally run B) of `lora_glossary_tuning.ipynb`, following `GUIDE.md`.
3. Put the downloaded result files under `results/`, run `uv run python -m app.report --write`, finish the findings in `answer.md`.
4. Delete the Colab runtime after each run.
