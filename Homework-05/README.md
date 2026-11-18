# Homework 5 (Lecture 5): Answer by Searching the Lecture Materials, Advanced level

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo). Deadline: Nov 23, 2026 (from the top-level README).

Level: **Advanced**. The task is to improve Tree, Graph or a combination, pick target questions, and compare with basic RAG on the same ones.
I built **Graph v2**: the course Graph's entry points and edges, with candidates ranked by the question, a text budget, and one-line previews
that the model can open with a `read_page` tool (a Graph and Tree combination). The write-up is in [answer.md](./answer.md).

## What is in this folder

| Path | What it is |
|---|---|
| `answer.md` | The submission: Exercise and Homework sections, in the course's template order. |
| `app/retrieval.py` | The course retrieval code, plus the Graph v2 section (`graph_v2`, `page_distances`, `preview_line`). |
| `app/tools.py`, `app/agent.py`, `app/config.py` | The course files with `search_graph_v2`, `read_page`, `--graph2` and `GRAPH2_*` settings added. |
| `app/offline_eval.py` | Offline mechanism check. No API key. Writes `results/offline/`. |
| `app/compare.py` | Live comparison: 4 questions, 5 methods, saved run by run to `results/compare/runs.json`. |
| `app/report.py` | Writes the tables in `answer.md` from `runs.json`, and lists what is unfinished (`--check`). |
| `scripts/fetch_course_data.py` | Downloads the course data and checks it by SHA-256. |
| `tests/` | 26 offline tests (no key, no network once the data is fetched). |
| `results/offline/` | `offline_eval.json` (every run) and `offline_summary.md`. |

Not copied from the course, on purpose: the MCP code (Lecture 6), the Lecture 3 glossary tools (this lecture's agent does not register them), `uv.lock`
(`uv sync` creates it) and the data. The slides mark the materials "no sharing with third parties without permission", so `data/rag_data/` is in
`.gitignore` and `scripts/fetch_course_data.py` downloads it from the course repository at revision `1ce722c`, the one named in the Lecture 05 problem
page, and refuses files that differ from the ones I used. The code comes from the Lecture 05 preparation branch
`feat/lecture05-rag-update-20261115` of `matsuolab/lecture-ai-engineering-2026-en`; the localized materials and index are not published there yet.

## Setup

```bash
cd Homework-05
uv sync
uv run python -m scripts.fetch_course_data      # downloads 4 files (about 2 MB) and checks them
export GEMINI_API_KEY=...                       # the same variable as Lecture 1 (in Codespaces: add the secret, then restart)
uv run pytest -q                                # 26 passed
uv run python -m app.agent --graph2 --list-tools
```

## What I ran without a key, and what still needs the key

Already done (no key needed, repeatable with the commands below): the tests, the data check, and

```bash
uv run python -m app.offline_eval               # rewrites results/offline/ (about 1 minute of pure Python)
```

Needs `GEMINI_API_KEY`. These are the cells of `answer.md` that say **Not recorded** until you run them:

1. STEP 2, search alone (fill in the "Pages found by running search alone" bullet by hand):
   `uv run python -m app.retrieval "LoRA QLoRA difference"`
2. The live comparison. See the plan first, then run it. It is 36 runs (roughly 80 to 100 model requests): one full-context run per question (about 117,000 input tokens
   each) and two runs of every other method. By the slide's numbers it costs about 20 cents in total. It pauses between runs and waits and retries on 429
   and 503, and it saves after every run, so running the same command again continues where it stopped:
   ```bash
   uv run python -m app.compare --dry-run
   uv run python -m app.compare
   ```
   If full context hits the input limit or a rate limit, the run is saved with its error. Keep that apart from the methods that worked (slide 23).
   Use `--methods vector graph graph2` to skip full context.
3. Put the numbers into `answer.md`, then check what is left:
   ```bash
   uv run python -m app.report --write
   uv run python -m app.report --check
   ```
4. Read the answers in `results/compare/runs.json` yourself. Correctness is a human judgement, so the script never guesses it. If you want it in the
   tables, create `results/compare/judgement.json`, for example `{"graph2:q2-multi:1": "correct", "vector:q2-multi:1": "partial"}` (`correct`, `partial` or `wrong`),
   and run `--write` again.
5. Write by hand what `--check` lists as "lines ... still say Not recorded": the answering model line, the STEP 2 bullet (use the output of step 1 above),
   "Live examples" under "Improved and failed examples", and the "Observations on the live runs" bullet. In the last one say whether the adoption rule in the
   Exercise section (Graph v2 receives at least as many evidence pages as vector search on q2 and q4, with under 2 times the input tokens) held. If the live runs
   contradict a sentence in the Homework section, change the sentence, not the numbers.
6. Commit and push `Homework-05/` (`runs.json` has answers and token counts, no keys; `.env` is ignored).

`--check` exits with 1 while anything is unfinished (it names the line numbers) and prints "nothing unfinished" when all is filled in.

## Where the pieces are, if you want to read the method

`app/retrieval.py`, after the line "Graph v2 (Homework 5, Advanced)":

- `expand_candidates`: every page within 2 hops of the entry points (adjacent page = 1 hop, shared term = 2 hops), with the route. Same edges as the course Graph.
- `graph_v2`: pure function. Sorts the candidates by distance to the question, returns the best `GRAPH2_FULL` with text and the next `GRAPH2_PREVIEWS` as one line.
- `search_graph_v2`: the live path: one embedding call, the top 3 as entry points, then `graph_v2`.
- `preview_line`: the one-line preview that skips headers and source lines.

Settings (`app/config.py`): `GRAPH2_START_K = 3`, `GRAPH2_HOPS = 2`, `GRAPH2_FULL = 4`, `GRAPH2_PREVIEWS = 5`.
