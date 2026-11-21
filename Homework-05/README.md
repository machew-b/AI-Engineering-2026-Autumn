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
| `tests/` | 35 offline tests (no key, no network once the data is fetched). |
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
uv run pytest -q                                # 35 passed
uv run python -m app.agent --graph2 --list-tools
```

## Status and how to reproduce

The homework is complete: the offline check, STEP 2, and the 36 live runs are done and written into `answer.md`.
`results/compare/runs.json` holds every live run (answers, tool calls, tokens, cost), and `results/compare/judgement.json` holds the Judgement column (written by Claude, see
"Use of AI tools" in `answer.md`).

To reproduce:

```bash
uv run python -m app.offline_eval               # no key: rewrites results/offline/
uv run python -m app.compare --dry-run          # shows the 36 runs (needs no key); without --dry-run it needs GEMINI_API_KEY
uv run python -m app.compare                    # skips runs already in runs.json; add --redo to run them again
uv run python -m app.report --write             # rewrites the tables in answer.md from runs.json and judgement.json
uv run python -m app.report --check             # prints "nothing unfinished" when answer.md has no placeholder left
```

Notes: `runs.json` is the raw measurement and is never edited by hand. `report.py` re-reads the cited pages from each saved answer with the current citation parser, so a parser fix changes
the tables and not the saved runs. Set `PYTHONUTF8=1` on Windows (the materials are Japanese). The whole live comparison cost about $0.26.

## Where the pieces are, if you want to read the method

`app/retrieval.py`, after the line "Graph v2 (Homework 5, Advanced)":

- `expand_candidates`: every page within 2 hops of the entry points (adjacent page = 1 hop, shared term = 2 hops), with the route. Same edges as the course Graph.
- `graph_v2`: pure function. Sorts the candidates by distance to the question, returns the best `GRAPH2_FULL` with text and the next `GRAPH2_PREVIEWS` as one line.
- `search_graph_v2`: the live path: one embedding call, the top 3 as entry points, then `graph_v2`.
- `preview_line`: the one-line preview that skips headers and source lines.

Settings (`app/config.py`): `GRAPH2_START_K = 3`, `GRAPH2_HOPS = 2`, `GRAPH2_FULL = 4`, `GRAPH2_PREVIEWS = 5`.
