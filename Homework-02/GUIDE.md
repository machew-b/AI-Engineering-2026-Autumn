# Guide: finish the Colab runs for Homework 02

Everything that can be done without a GPU is already in this folder. What is left is running the notebooks on a
free Colab T4 and bringing the result files back. Budget about 1 hour in total (exercise 15 min, run A 20 min,
run B 20 min, optional).

## 1. Exercise: the course notebook (about 15 minutes)

1. Open https://colab.research.google.com/github/matsuolab/lecture-ai-engineering-2026/blob/main/notebooks/lora_format_tuning.ipynb
2. File > Save a copy in Drive. Then Runtime > Change runtime type > T4 GPU.
3. Run every cell from the top (sections 0 to 7). Section 4 (training) takes 4 to 5 minutes. Read the before and after tables.
4. Section 7 creates `result.json`. In the file list on the left open `/content/qlora_lab` and download
   `result.json`, `eval_before.json`, `eval_after.json`.
5. Save them in this repo as `Homework-02/results/exercise/result.json`, `.../eval_before.json`, `.../eval_after.json`.
6. Runtime > Disconnect and delete runtime.

If no GPU can be assigned, follow section 4b of the notebook and set `executed_training_myself` to `False`.

## 2. Homework run A: glossary only (about 20 minutes)

1. Open the notebook link in `README.md`. Runtime > Change runtime type > T4 GPU. Keep `RUN_NAME = "run_a"` and `INCLUDE_ABSTAIN = False`.
2. Run every cell from the top. Section 3 (before) takes 3 to 4 minutes, section 4 (training) about 10, section 5 (after) 3 to 4.
3. At the end a zip `run_a_results.zip` is downloaded. Unzip it: it contains a folder `run_a` with three files.
4. Put that folder at `Homework-02/results/run_a/`.
5. Runtime > Disconnect and delete runtime.

## 3. Homework run B: add "not in the glossary" examples (optional, about 20 minutes)

Same as run A, but in the settings cell use `RUN_NAME = "run_b"` and `INCLUDE_ABSTAIN = True`. If you used the same session
for run A, do Runtime > Restart session first. Put the result at `Homework-02/results/run_b/`. Skip it if time is short; the
tables then show "n/a" for run B and `answer.md` says so.

## 4. Bring it together (in VS Code or Codespaces, inside `Homework-02`)

```bash
uv run python -m app.report            # check the tables
uv run python -m app.report --write    # writes them into answer.md
uv run python -m app.report --check    # lists the findings still to write
uv run pytest -q
```

Then write the findings in `answer.md` (every line that starts with `TODO(` is a placeholder; each one has a short list of
questions to answer from your own tables and from the answers in `eval_after.json`). Finally, in the top-level `README.md`
set Homework 02 to `Finished` and commit everything to `main`.

No terminal? Upload the files with GitHub's "Add file > Upload files" and send the three summaries (`result.json` of each
run) to Claude in chat, which can fill the tables and findings for you. Either way, read the answers yourself before submitting.

## If something goes wrong

- `GPU not found`: Runtime > Change runtime type > T4 GPU, then run the cell again. If Colab is busy, wait.
- The data download cell fails (private repo or no network): it asks you to upload `app/glossary_data.py`, `app/scoring.py`,
  `app/retrieval.py`, `app/__init__.py` and `data/glossary.json` from this folder.
- Training stops midway: run sections 0 to 3 again and use `trainer.train(resume_from_checkpoint=True)`.
- `nan` loss or an out-of-memory error: Runtime > Restart session and run again; do not change the pinned library versions.
- Results differ a little from run to run even with a fixed seed. Compare failure types, not exact counts.
