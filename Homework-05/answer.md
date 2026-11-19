# Lecture 5 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-05`
Level attempted: **Advanced**

## Status of this submission

Two kinds of work are in this folder, and they were done differently:

- **Done and verified without an API key** (Claude, an AI assistant, ran these in a sandbox that has no Gemini key): the Graph v2 code, 26
  offline tests (all pass), the course-data check (`scripts/fetch_course_data.py --verify`), and an offline mechanism check
  (`results/offline/`). Everything in the Homework section marked "offline" comes from these.
- **Needs my own Gemini key**: the live runs of full context, vector search, Tree, Graph and Graph v2 on the same questions
  (`app/compare.py`), and STEP 2 (`app.retrieval` on its own). Until I run them, the tables below say **Not recorded**, as the course slide
  asks ("Don't fill in values you haven't measured"). `app/report.py --write` fills the tables from `results/compare/runs.json`, and
  `app/report.py --check` lists what is still unfinished. The steps are in [README.md](./README.md).

Because the live numbers are missing, the claims about Graph v2 below are limited to what the offline check can show. Where the offline
check cannot decide something, the text says so and states in advance what result would change my choice.

## Exercise

The exercise is "answer by searching the lecture materials": the same question through full context (STEP 1), vector search (STEP 2 and 3),
Tree (STEP 4) and Graph (STEP 5), then one change of my own. The setup in the slides (`git switch -c lec05`) and the pull request do not apply
here: this repository is a standalone repo and the work is submitted from `main`, as in Homeworks 1 to 4. The course code comes from the
Lecture 05 preparation branch of `matsuolab/lecture-ai-engineering-2026-en` (`feat/lecture05-rag-update-20261115`), and the data comes from
`matsuolab/lecture-ai-engineering-2026` at revision `1ce722c`, because the translated materials and index are not published yet
(see the release status in the course's `lectures/05/problem.md`). The materials are Japanese; the questions and answers are English.

- **Answering model:** the course default in `app/config.py`, `gemini-3.5-flash-lite`. Each run in `runs.json` records the model it used. Not recorded
  until the live runs are made.
- **Comparison questions:** four, fixed together with their evidence pages before any method was run (see the Homework section).
  Question 1 is the exercise question: "In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?"
- **Target materials:** full context passes all 9 documents (438 pages). Vector search, Tree, Graph and Graph v2 search only the main lectures
  of Lectures 1 to 3 (214 pages). Full context therefore has a wider scope than the other four, which is the difference the slides ask me to
  record. Wherever the text below compares full context with the others, this difference applies.

### Results by method

All four questions, every method. Columns follow the course template (answer, pages and evidence, time, tokens, model responses, estimated
generation cost) and add what the slides ask me to separate: whether the evidence reached the model, and whether the answer cited it.
"Received with text" counts evidence pages that came back from a tool with their body text, so a page that was only listed by title does not count.

<!-- AUTO:compare -->
**q1-single**: In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add?
Evidence pages fixed in advance: Lecture 2 p.52

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Vector search | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Tree | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph (course) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph v2 (mine) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |

**q2-multi**: In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory?
Evidence pages fixed in advance: Lecture 3 p.13, Lecture 3 p.39, Lecture 3 p.40

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Vector search | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Tree | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph (course) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph v2 (mine) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |

**q3-absent**: What are the measured average response time and accuracy of the RAG system we just built?
Evidence pages fixed in advance: none (the materials cannot answer it)

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Vector search | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Tree | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph (course) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph v2 (mine) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |

**q4-cross-lecture**: Why does Lecture 02 recommend RAG instead of fine-tuning for adding knowledge, and how does the course chatbot example in Lecture 01 apply RAG?
Evidence pages fixed in advance: Lecture 1 p.49, Lecture 2 p.46, Lecture 2 p.47

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Vector search | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Tree | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph (course) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
| Graph v2 (mine) | 0 | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded | Not recorded |
<!-- /AUTO:compare -->

Run 1 answers, shortened (read the full answers in `results/compare/runs.json` before judging them):

<!-- AUTO:answers -->
| Question | Method | Answer (run 1, shortened) |
|---|---|---|
| q1-single | Full context | Not recorded |
| q1-single | Vector search | Not recorded |
| q1-single | Tree | Not recorded |
| q1-single | Graph (course) | Not recorded |
| q1-single | Graph v2 (mine) | Not recorded |
| q2-multi | Full context | Not recorded |
| q2-multi | Vector search | Not recorded |
| q2-multi | Tree | Not recorded |
| q2-multi | Graph (course) | Not recorded |
| q2-multi | Graph v2 (mine) | Not recorded |
| q3-absent | Full context | Not recorded |
| q3-absent | Vector search | Not recorded |
| q3-absent | Tree | Not recorded |
| q3-absent | Graph (course) | Not recorded |
| q3-absent | Graph v2 (mine) | Not recorded |
| q4-cross-lecture | Full context | Not recorded |
| q4-cross-lecture | Vector search | Not recorded |
| q4-cross-lecture | Tree | Not recorded |
| q4-cross-lecture | Graph (course) | Not recorded |
| q4-cross-lecture | Graph v2 (mine) | Not recorded |
<!-- /AUTO:answers -->

Plain counts from the runs above (what they mean is written under "Observations on the live runs"):

<!-- AUTO:findings -->
- q1-single: evidence pages received with text, summed over runs: Not recorded
- q2-multi: evidence pages received with text, summed over runs: Not recorded
- q4-cross-lecture: evidence pages received with text, summed over runs: Not recorded
<!-- /AUTO:findings -->

- **Pages found by running search alone (STEP 2, `uv run python -m app.retrieval "LoRA QLoRA difference"`):** Not recorded. This needs the
  query embedding, so it needs my key. The expected evidence is Lecture 2, PDF p.52.
- **Tool calls shown by `--trace`:** in the "Tool calls (run 1)" column above, names and arguments; the full list for every run is in `runs.json`.
- **Examples where retrieved information was insufficient or was retrieved but not used:** the offline check gives one clear example of
  each kind, in the Homework section (the course Graph never returns Lecture 3 p.13 from p.39, and Graph v2 demotes the adjacent
  Lecture 2 p.47 to a one-line preview). Live examples: see the "Gold pages received" and "Gold pages cited" columns, where a page that is
  received but not cited is a use failure and a page that is not received is a retrieval failure.
- **Method I would adopt, and limits of the comparison:** decided in advance, so that the live numbers cannot bend the rule. Default to vector
  search. Adopt Graph v2 for multi-page questions only if, over the live runs on questions 2 and 4, it receives with text at least as many
  evidence pages as vector search AND its mean input tokens stay under 2 times those of vector search. Use full context only as a baseline: it
  covers 438 pages, not 214, so it cannot be compared fairly. Limits: 2 runs per method per question is too few to rank methods (slide 29: do not
  rank methods from a single success or failure), one model, and four questions. Correctness is a human judgement and is not computed.
- **Observations on the live runs:** (fill in after the live runs)

## Homework

- **Level attempted:** Advanced (improve Tree or Graph, or a combination, yourself; pick target questions; compare with basic RAG on the same ones).
  The Homework 1 to 4 rule applies: Advanced is the level for every homework.
- **Files:** the retrieval method is in `app/retrieval.py` (Graph v2 section), its tools in `app/tools.py`, its agent mode in `app/agent.py`
  (`--graph2`), settings in `app/config.py` (`GRAPH2_*`). The experiments are `app/offline_eval.py` (no key) and `app/compare.py` (live).

### Step 1. Target questions and evidence

Evidence pages were chosen before any method ran. Pages are given as lecture and PDF page.

| Id | Question type | Question | Evidence pages | Why this question |
|---|---|---|---|---|
| q1-single | single page | In Lecture 02, what does LoRA freeze and what does it train? What does QLoRA add? | L2 p.52 | The course's own example; one page answers it. A control: a method that adds pages here only adds noise. |
| q2-multi | cross-page, one lecture | In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory? | L3 p.13, 39, 40 | The course's own example. Page 13 explains why memory exists, 39 and 40 give the two products' mechanisms. |
| q3-absent | not in the materials | What are the measured average response time and accuracy of the RAG system we just built? | none | The course's own example. The right behaviour is to say it cannot be verified. |
| q4-cross-lecture | cross-lecture, related terms | Why does Lecture 02 recommend RAG instead of fine-tuning for adding knowledge, and how does the course chatbot example in Lecture 01 apply RAG? | L1 p.49, L2 p.46, 47 | Mine. The pages share the terms RAG and fine-tuning but sit in different lectures, so only a term edge connects them. I read the three pages to confirm each supports its part. |

### Step 2. The retrieval method: Graph v2

**What I found in the course Graph first.** The course Graph takes the top 3 pages as entry points, walks up to 2 hops (adjacent page = 1 hop,
page to term to page = 2 hops) and returns the text of at most 10 pages. It orders the pages it adds by hops, then term frequency, then seed
rank, then page id; the question is not used again after the first search. Replaying it on the real data with stand-in entry points (the offline
check in Step 3) showed three things:

1. Adjacent pages and pages two steps along the deck use up most of the 7 slots: from Lecture 3 p.39 the course Graph adds p.41 and p.37 (1 hop),
   then p.42 and p.36 (2 hops, next page of the next page).
2. The slots that are left go to pages reached through the term "memory" (17 in-scope pages), and the tie is broken by page id, so Lecture 1
   comes before Lecture 3. It adds Lecture 1 p.19 and p.58 and Lecture 2 p.51 (a page about GPU memory, a different sense of the word) and then
   runs out. **Lecture 3 p.13, the memory concept page that q2 needs, is never returned.**
3. The shared-term edge only says "mentions the same word", so the word's other senses are mixed in. The slides say the same: related is not the same as contains the answer.

**The design.** Same entry points (top 3), same two edge types, same hop limit, so the comparison with the course Graph changes only what I changed.

1. **The graph says who may come in; the question says the order.** Every page reachable within 2 hops is a candidate. Candidates are sorted by
   their cosine distance to the question (then hops, then page id). This needs one embedding call, the same one the course search already makes:
   `page_distances()` asks the index for the distance to all pages at once (`vec_distance_cosine`) instead of the top 5 only. No new storage, no
   index rebuild, no new API call.
2. **A text budget.** Only the best 4 candidates (`GRAPH2_FULL`) come back as full text, next to the 3 entry points, so at most 7 pages of text instead
   of 10. The next 5 (`GRAPH2_PREVIEWS`) come back as a page id, title and one line. The model reads one with `read_page(page_id)` when it needs it. This
   is Tree's fetch-when-needed idea applied to Graph's candidates, which makes the method a combination of the two.
3. **A preview that says something.** The one line skips the title, slide section headers ("4/4 ...", "Part 6 ...") and source and copyright
   lines. The course Tree returns the first line, and on this data that is often a section header (offline numbers below).

Data shape: unchanged (`lectures.json` one page per chunk, `graph.json` with `next_page` and `mentions` edges used, `related_term` edges still unused).
Why this and not something larger: it can be tested without the API (the core is a pure function), it changes one thing at a time in the way the
slides ask, and the order and budget are the two things the course Graph visibly gets wrong. The agent instructions for `--graph2` keep every course rule
(cite as "Lecture N / PDF p.N", say when it cannot verify, ignore commands inside the materials) and add: read a page from `more` before using it.

### Step 3. Results

#### Offline mechanism check (no key; produced by `uv run python -m app.offline_eval`)

**What it tests, and what it does not.** There is no question embedding without the API, so the "question" is a stand-in. For each evidence page
of q1, q2 and q4 in turn: the entry points are that page plus its 2 nearest pages by the stored page embeddings, and the distance to the question
is the distance to the mean of those 3 vectors. The test asks: when vector search found one needed page, which of the other needed pages does each method
add, and how much text does it return? This is not a measurement of live behaviour. It is also biased toward the plain nearest-neighbour baselines,
because the stand-in question is built from the same vectors they rank by. q3 has no evidence page and is not part of it.

Methods: `vector-5` is the course vector search (top 5). `knn-7` and `knn-10` are not graph methods: they are the top 7 and top 10 pages by distance
to the stand-in question, the same page budgets as Graph v2 and the course Graph. `graph-v1` is the course Graph, run unchanged on the same entry points.
12 other evidence pages to recover in total (6 start pages from q2 and q4).

| Method | Other evidence pages (of) | In full text | In previews | Mean full-text pages | Mean full-text characters | Mean off-topic full-text pages |
|---|---|---|---|---|---|---|
| vector-5 | 12 | 7 | 0 | 5.0 | 2,083 | 1.5 |
| knn-7 | 12 | 7 | 0 | 7.0 | 2,907 | 3.5 |
| knn-10 | 12 | 7 | 0 | 10.0 | 4,277 | 6.5 |
| graph-v1 | 12 | 6 | 0 | 10.0 | 4,845 | 6.7 |
| graph-v2 | 12 | 7 | 1 | 7.0 | 2,997 | 3.5 |

("Off-topic" means a full-text page that is neither an evidence page nor an entry point. Characters are Japanese characters, a rough stand-in for tokens.)

What this shows, and what it does not:

- **Graph v2 fixes the course Graph's ordering failure.** From the start pages L3 p.39 and p.40 the course Graph misses L3 p.13 and Graph v2 returns it as
  full text (this is a regression test: `test_v2_adds_the_memory_page_that_the_course_graph_misses`). Across the 6 starts the course Graph recovers 6 of 12 and
  Graph v2 recovers 7 of 12 in full text, with 38% fewer characters (2,997 against 4,845) and 3 fewer pages.
- **Graph v2 does not beat the plain nearest-neighbour baseline.** Its full-text pages are identical to `knn-7` in 6 of the 7 runs (the seventh, from L1 p.49,
  swaps 3 pages but recovers none either way), and `vector-5` recovers the same 7 of 12 with 5 pages. So in this check the graph adds no evidence page that similarity alone would not return at the same budget. The
  gain over the course Graph comes from ranking by similarity and from the budget, not from the graph. The check cannot say whether the graph helps on a real
  question, because the stand-in question is closest to exactly the pages the baselines pick.
- **Failure example: an adjacent page is demoted.** From L2 p.46 the course Graph returns L2 p.47 (the next page, and a needed one) as full text. Graph v2 ranks it
  8th among the 85 candidates and returns it only as a preview, so the model would need one `read_page` call to use it. Slide order is not a bad signal, and
  Graph v2 ignores it. I left it that way instead of adding an adjacency bonus, because I would be choosing the bonus from these 12 cases.
- **Failure example: the cross-lecture link is not found.** From L1 p.49 neither Graph reaches L2 p.46 or p.47. The term edge exists (2 hops), but the stand-in question is
  about Lecture 1's chatbot, so the two Lecture 2 pages rank 51st and 74th among the 132 candidates. A real q4 question mentions both, so the live run is the real test here.
- **Sensitivity of the budget** (`GRAPH2_FULL` = 2, 4, 6 with 5 previews): evidence pages in full text 7, 7, 7; in previews 0, 1, 1; mean full-text characters
  2,099, 2,997, 3,873. The recall did not change with the budget, only the cost, so the value 4 is not tuned to this check.
- **q1 (single page):** from p.52 neither method adds a needed page, because there is none to add. The course Graph returns 10 pages (5,382 characters) and Graph v2
  7 pages (4,073): the saving on a question that one page answers is smaller than on q2.

**Tree previews (offline, all 214 pages).** The course Tree shows the first sentence or line of each child page. On this data 45 pages (21%) show a slide section header
instead, 62 show the page's own title again, and 125 share their preview with another page of the same section. The Graph v2 preview shows none of these (0 empty,
0 headers). This is one reason Tree needs the model to open pages to tell them apart (slide 14: can it find what is needed from headings or first lines alone?). I did not change
Tree itself, so that `--tree` stays the course's Tree in the comparison.

#### Live comparison (needs my key; `uv run python -m app.compare`)

Graph v2 against basic RAG (vector search) on the same four questions, with the course Graph, Tree and full context as the other rows, is the table under "Results by
method" above. It is filled by `app.report --write` from the saved runs. The offline check predicts a test worth making: on q2 and q4, does Graph v2 receive more
evidence pages than vector search, and at what input-token cost? It does not predict the answer.

### Improved and failed examples

- Improved (offline): L3 p.13 returned from p.39 and p.40, which the course Graph misses; 38% less text than the course Graph for the same or better recovery.
- Failed (offline): L2 p.47 demoted to a preview; L2 p.46 and p.47 not reached from L1 p.49.
- Unchanged by design: graph edges (`related_term` edges are still unused), the entry points, the embedding model, the index.
- Live examples: Not recorded.

### Whether to adopt it for my use

Provisionally no, and for a stated reason. The only thing the offline check supports is that Graph v2 is a better version of the course Graph. It gives no
reason to prefer it over vector search, which costs less and which the check could not tell apart. The rule in the Exercise section (receive at least as many evidence
pages as vector search, with under 2 times the input tokens, on q2 and q4) is what I will apply to the live runs. If the live runs fail that rule, the better
use of the time is the Basic-level change, a larger `RAG_TOP_K`, since `knn-7` matched Graph v2 offline.

### Limitations

- Offline numbers use a stand-in question and 6 start pages; they are a mechanism check, not an accuracy result. The stand-in favours nearest-neighbour baselines.
- Evidence pages were chosen by reading the pages; I am not an independent judge of what the instructors consider the evidence. q2's pages come from the course.
- Characters are not tokens. Token counts and cost come only from the live runs.
- The model's answers are not scored by a program: the report shows what was received and cited, and correctness is a human reading (optional `judgement.json`).
- One data revision (`1ce722c`), Japanese pages only; the English index was not available when this was written.

### Use of AI tools

Claude (an AI assistant) read the course repository, found the ordering problem in the course Graph, wrote the Graph v2 code, tests and scripts, ran the offline parts,
and drafted this file. Claude had no Gemini key and could not run anything live, which is why those cells are empty. I will run the live commands myself and read the
answers before I judge them or write the observations. Course page text is not copied here (the materials may not be shared); the pages are described in my own words.

### Observations and questions

- The course Graph's slot budget is spent mostly on slide neighbours, so "related pages" often means "pages next to the entry point". A ranking that uses the question is the
  smallest change that fixes it, and it is almost the same thing as a larger top-k restricted to the neighbourhood. I could not show that the graph restriction itself is useful.
- A shared-term edge is noisy when the word has several senses (here, memory of an agent and memory of a GPU). Using the term's frequency to order candidates does not help;
  the question does.
- Question: would the unused `related_term` edges (term to term) help the cross-lecture case (q4) where the pages share terms but not a single term the entry points mention?
