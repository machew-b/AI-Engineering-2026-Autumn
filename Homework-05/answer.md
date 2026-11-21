# Lecture 5 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-05`
Level attempted: **Advanced**

## Status of this submission

Everything in this folder has been run. The work was split like this:

- **Run by Claude (an AI assistant) in a sandbox with no Gemini key:** the Graph v2 code, the tests (35, all pass), the course-data check, and the
  offline mechanism check (`results/offline/`).
- **Run by me on my own machine with my Gemini key:** STEP 2 (`app.retrieval`), one `--graph2 --trace` run, and the live comparison (`app/compare.py`:
  36 runs, saved in `results/compare/runs.json`). The numbers in the tables come from those saved runs through `app/report.py --write`; none was typed in by hand.
- **Done by Claude from my saved runs:** reading the 36 saved answers and filling the Judgement column (`results/compare/judgement.json`), recomputing which pages
  each answer cites, and drafting the observations below. These are AI judgements, not an independent human grading (see "Use of AI tools").

Where a live result confirms or contradicts an offline claim, the text says so.

## Exercise

The exercise is "answer by searching the lecture materials": the same question through full context (STEP 1), vector search (STEP 2 and 3),
Tree (STEP 4) and Graph (STEP 5), then one change of my own. The setup in the slides (`git switch -c lec05`) and the pull request do not apply
here: this repository is a standalone repo and the work is submitted from `main`, as in Homeworks 1 to 4. The course code comes from the
Lecture 05 preparation branch of `matsuolab/lecture-ai-engineering-2026-en` (`feat/lecture05-rag-update-20261115`), and the data comes from
`matsuolab/lecture-ai-engineering-2026` at revision `1ce722c`, because the translated materials and index are not published yet
(see the release status in the course's `lectures/05/problem.md`). The materials are Japanese; the questions and answers are English.

- **Answering model:** `gemini-3.5-flash-lite`, the course default in `app/config.py`, for all 36 runs (it is stored in every record of `runs.json`).
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
| Full context | 1 | all in context | 1/1 | L2 p.52; L2 p.51 | none | 8.92 | 117,027 / 276 | 1.0 | 0.035798 | correct |
| Vector search | 2 | 1/1, 1/1 | 1/1, 1/1 | L2 p.52; L2 p.51 | `search_materials('LoRA freeze train QLoRA add')` | 10.03 | 3,005 / 206 | 2.0 | 0.001418 | correct, correct |
| Tree | 2 | 1/1, 1/1 | 1/1, 1/1 | L2 p.51; L2 p.52 | `browse_tree()`, `browse_tree('lec02-main')`, `browse_tree('lec02-main-s045')`, `browse_tree('lec02-main-p052')`, `browse_tree('lec02-main-p051')` | 15.80 | 13,699 / 419 | 6.0 | 0.004886 | correct, correct |
| Graph (course) | 2 | 1/1, 1/1 | 1/1, 1/1 | L2 p.51; L2 p.52 | `search_graph('LoRA freeze train QLoRA add Lecture 02')` | 8.07 | 5,769 / 280 | 2.0 | 0.002429 | correct, correct |
| Graph v2 (mine) | 2 | 1/1, 1/1 | 1/1, 1/1 | L2 p.51; L2 p.52 | `search_graph_v2('LoRA freeze train QLoRA add Lecture 02')` | 8.79 | 5,880 / 277 | 2.0 | 0.001909 | correct, correct |

**q2-multi**: In the Lecture 03 examples, how does compaction differ from memory across sessions? Do all daily notes go into long-term memory?
Evidence pages fixed in advance: Lecture 3 p.13, Lecture 3 p.39, Lecture 3 p.40

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 1 | all in context | 2/3 | L3 p.39; L3 p.40 | none | 6.74 | 117,031 / 291 | 1.0 | 0.035837 | correct |
| Vector search | 2 | 3/3, 3/3 | 3/3, 3/3 | L3 p.39; L3 p.13; L3 p.40 | `search_materials('compaction memory across sessions daily notes long-term memory')`, `search_materials('OpenClaw dreaming 長期メモリ 残す基準')` | 17.39 | 6,599 / 415 | 3.0 | 0.002745 | correct, correct |
| Tree | 2 | 2/3, 2/3 | 2/3, 2/3 | L3 p.39; L3 p.40 | `browse_tree()`, `browse_tree('lec03-main')`, `browse_tree('lec03-main-s037')`, `browse_tree('lec03-main-p037')`, `browse_tree('lec03-main-p038')`, `browse_tree('lec03-main-p039')`, `browse_tree('lec03-main-p040')`, `browse_tree('lec03-main-p041')` | 32.70 | 15,134 / 495 | 8.5 | 0.005778 | partial, correct |
| Graph (course) | 2 | 2/3, 2/3 | 2/3, 2/3 | L3 p.39; L3 p.38; L3 p.40 | `search_graph('compaction memory across sessions daily notes long-term memory Lecture 03')` | 14.50 | 5,340 / 426 | 2.0 | 0.002667 | correct, correct |
| Graph v2 (mine) | 2 | 3/3, 3/3 | 2/3, 3/3 | L3 p.39; L3 p.40; L3 p.65; L3 p.38 | `search_graph_v2('compaction memory across sessions daily notes long-term memory Lecture 03')` | 22.01 | 8,678 / 414 | 2.5 | 0.002816 | partial, correct |

**q3-absent**: What are the measured average response time and accuracy of the RAG system we just built?
Evidence pages fixed in advance: none (the materials cannot answer it)

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 1 | no evidence page exists | says it cannot verify | none | none | 4.11 | 117,021 / 27 | 1.0 | 0.035174 | correct |
| Vector search | 2 | no evidence page exists | says it cannot verify, says it cannot verify | L2 p.13 | `search_materials('average response time accuracy RAG system')`, `search_materials('RAG システム 構築 平均 応答時間 精度')` | 21.69 | 8,063 / 226 | 3.0 | 0.002983 | correct, correct |
| Tree | 2 | no evidence page exists | says it cannot verify, says it cannot verify | none | `browse_tree()`, `browse_tree('lec03-main')`, `browse_tree('lec01-main')`, `browse_tree('lec02-main')` | 31.51 | 5,670 / 144 | 5.0 | 0.002060 | correct, correct |
| Graph (course) | 2 | no evidence page exists | says it cannot verify, says it cannot verify | L2 p.13 | `search_graph('RAG system average response time accuracy measured')`, `search_graph('RAG システム lecture')` | 30.54 | 14,912 / 205 | 3.0 | 0.003887 | correct, correct |
| Graph v2 (mine) | 2 | no evidence page exists | says it cannot verify, says it cannot verify | L2 p.13; L2 p.18; L1 p.27 | `search_graph_v2('average response time accuracy RAG system')`, `search_graph_v2('measured average response time accuracy RAG')` | 30.84 | 10,640 / 284 | 2.5 | 0.003901 | correct, correct |

**q4-cross-lecture**: Why does Lecture 02 recommend RAG instead of fine-tuning for adding knowledge, and how does the course chatbot example in Lecture 01 apply RAG?
Evidence pages fixed in advance: Lecture 1 p.49, Lecture 2 p.46, Lecture 2 p.47

| Method | Runs | Gold pages received with text (per run) | Gold pages cited (per run) | Cited pages (run 1) | Tool calls (run 1) | Seconds (mean) | Input / output tokens (mean) | Model responses (mean) | Est. cost USD (mean) | Judgement (per run) |
|---|---|---|---|---|---|---|---|---|---|---|
| Full context | 1 | all in context | 3/3 | L2 p.20; L2 p.23; L2 p.46; L2 p.47; L1 p.19; L1 p.49 | none | 4.25 | 117,037 / 425 | 1.0 | 0.036174 | partial |
| Vector search | 2 | 3/3, 3/3 | 3/3, 3/3 | L2 p.46; L2 p.47; L2 p.53; L1 p.19; L1 p.49 | `search_materials('RAG fine-tuning knowledge Lecture 02')`, `search_materials('Lecture 01 chatbot RAG application')` | 27.23 | 5,961 / 697 | 2.5 | 0.003531 | correct, correct |
| Tree | 2 | 3/3, 3/3 | 3/3, 3/3 | L2 p.46; L2 p.47; L1 p.36; L1 p.49 | `browse_tree()`, `browse_tree('lec02-main')`, `browse_tree('lec01-main')`, `browse_tree('lec02-main-s045')`, `browse_tree('lec01-main-s029')`, `browse_tree('lec02-main-p046')`, `browse_tree('lec02-main-p047')`, `browse_tree('lec01-main-p049')` | 101.78 | 37,454 / 679 | 9.0 | 0.009664 | correct, correct |
| Graph (course) | 2 | 3/3, 3/3 | 3/3, 3/3 | L2 p.46; L2 p.47; L2 p.53; L1 p.19; L1 p.49 | `search_graph('Lecture 02 RAG fine tuning knowledge')`, `search_graph('Lecture 01 chatbot RAG example')` | 21.55 | 14,383 / 578 | 3.0 | 0.004663 | correct, correct |
| Graph v2 (mine) | 2 | 3/3, 3/3 | 3/3, 3/3 | L2 p.46; L2 p.47; L2 p.27; L1 p.49 | `search_graph_v2('RAG versus fine tuning Lecture 02 chatbot Lecture 01')` | 16.35 | 9,948 / 522 | 2.5 | 0.003742 | correct, correct |
<!-- /AUTO:compare -->

Run 1 answers, shortened (read the full answers in `results/compare/runs.json` before judging them):

<!-- AUTO:answers -->
| Question | Method | Answer (run 1, shortened) |
|---|---|---|
| q1-single | Full context | 教材の記述によると、LoRA および QLoRA について以下の説明があります。 - **LoRAが固定するもの（freezeする）**: モデルの元の重み（事前学習済みの重み）を固定して学習しないようにします。（Document: `lec02-main / 基盤モデルの仕組み`, Section: 選んだモデルを、いつ・どう直すか, PDF p.52） - **LoRAが学習するもの**: 追加した小さな「差分」（細長い2つの小さな… |
| q1-single | Vector search | Lecture 02 explains PEFT (Parameter-Efficient Fine-Tuning) methods, specifically focusing on LoRA and QLoRA: * **LoRA (Low-Rank Adaptation):** * **What it freezes:** The original model weights ($W$) are fixed and not tra… |
| q1-single | Tree | Lecture 02の資料（PDF p.51–52）によると、LoRAとQLoRAの仕組みは以下のようになっています。 * **LoRA（Low-Rank Adaptation）が凍結（Freeze）するものと訓練するもの：** * **凍結するもの：** 元のモデルの重み（$W$）はそのまま固定（Freeze）し、学習させません。 * **訓練するもの：** 本体の代わりに、変化分を表す小さな行列（低ランクの行列 $A$ と $B$）… |
| q1-single | Graph (course) | Lecture 02の資料に基づくと、LoRAおよびQLoRAの仕組みについて以下のように説明されています（Lecture 02 / PDF p.51-52）。 * **LoRAが凍結（固定）するもの** * モデルの元の重み（本体）は固定し、学習は行いません（Lecture 02 / PDF p.52）。 * **LoRAが学習するもの** * 変化分を表す小さな行列 $A$・$B$（細長い2つの小さな行列の積、低ランク）だけを学習し… |
| q1-single | Graph v2 (mine) | In Lecture 02 (Lecture 02 / PDF p.51–52), **LoRA** and **QLoRA** are introduced under Parameter-Efficient Fine-Tuning (PEFT) methods: * **What LoRA freezes:** The original model weights ($W$) are **frozen** (kept fixed a… |
| q2-multi | Full context | 学習サポートエージェントです。質問にお答えするヒントを案内しますね！ 資料の中では、第3回（AIエージェント）の「Part 6 メモリ」において、セッション内の要約（コンパクション）とセッションをまたぐ長期記録・メモリ、および日々のメモの扱いについて解説されています。 以下のページを確認してみましょう： - **コンパクションとセッションをまたぐメモリの違い**: PDF p.39（Document: `lec03-main / AIエ… |
| q2-multi | Vector search | 講義資料に基づいて、それぞれの疑問に対する考え方のヒントを以下に示します。 ### 1. コンパクションとセッションをまたぐメモリの違い * **コンパクション（履歴の要約）** * **範囲：** 「コンテキストの中（同じセッション）」で機能します。 * **動作：** 長い作業などでコンテキストの上限に近づいた際や古い履歴を、要約に置き換えて情報を詰める仕組みです（Lecture 03 / PDF p.39）。 * **セッションを… |
| q2-multi | Tree | To answer your questions about compaction and memory across sessions, let's look at how Lecture 3 structures these concepts: 1. **Compaction vs. Memory across sessions:** - **Compaction** happens **within the same sessio… |
| q2-multi | Graph (course) | Lecture 03の資料をもとに、それぞれの疑問について考えてみましょう。 ### 1. コンパクションとメモリ（セッションをまたぐ仕組み）の違い * **コンパクション（Compaction）** * **範囲：** 「同じセッション（コンテキストの中）」で働きます（Lecture 3 / PDF p.39）。 * **動作：** 会話が長くなりコンテキストの上限に近づいたとき、古い履歴を要約して置き換えることでトークンを圧縮します… |
| q2-multi | Graph v2 (mine) | Lecture 03 explains memory and context management by distinguishing between what happens *within* a single session versus *across* sessions (Lecture 3 / PDF pp. 39, 40). To help you think about these concepts: 1. **Compa… |
| q3-absent | Full context | Cannot verify. The provided materials do not contain measurements of the average response time and accuracy for the RAG system described in the question. |
| q3-absent | Vector search | 講義資料（Lecture 01〜03）を確認しましたが、講義内で構築した特定のRAGシステムに関する「測定された平均応答時間」や「精度（正答率）」の具体的な数値データは記載されていません。 講義資料では、RAGシステムを含むLLMの評価に関して以下の点が指摘されています。 - LLMは確率で次の言葉を選ぶため、同じ質問でも答えが毎回変わり、1回試しただけでは実際の正答率は分からない（Lecture 2 / PDF p.13）。 - その… |
| q3-absent | Tree | メイン講義資料（Lecture 01〜03）を確認しましたが、RAG（Retrieval-Augmented Generation）システムを実際に構築して平均応答時間や精度を測定したという記述やデータは見当たりませんでした。 これらの講義ではAIエンジニアリングの概論や基盤モデルの仕組み、AIエージェントなどを扱っており、RAGシステムの構築やベンチマーク測定はスコープ外となっています。 |
| q3-absent | Graph (course) | 講義資料（Lecture 01～03）を確認したところ、現時点の教材では「RAGシステムを実際に構築して平均応答時間や精度を測定した具体的な数値」は記載されていません。 そのため、その質問に対する答えは教材からは確認できません。 --- ### ヒント・考え方 LLMやRAGのシステムを評価する際には、以下のような点に注意する必要があります： 1. **ばらつきの確認**: LLMは確率的に言葉を選ぶため、1回試しただけでは正確な性能は… |
| q3-absent | Graph v2 (mine) | 講義資料（Lecture 01〜03）を確認しましたが、実際に構築したRAGシステムの**「測定された平均応答時間」や「具体的な正答率（精度）の数値」を示すデータは記載されていません**。 代わりに、講義資料では以下の重要なポイントが強調されています。 - **1回の正解を信じない**: LLMは確率で次の言葉を選ぶため、同じ質問でも答えが毎回変わります。そのため、「1回試して動いた」では実際の正答率は分からず、同じ質問を複数回（例: … |
| q4-cross-lecture | Full context | ご質問ありがとうございます！ 講義資料の該当箇所を確認し、学習のヒントとなるように整理しました。一緒に考えていきましょう。 ### 1. なぜ Lecture 02 では知識の追加に Fine-Tuning ではなく RAG を推奨するのか？ Lecture 02 の資料では、モデルの仕組み（知識の土台がどこで作られるか、追加学習の特性）に踏み込んで説明されています。以下のポイントに注目してみましょう。 * **モデルの仕組みと知識の限… |
| q4-cross-lecture | Vector search | Based on the course materials, here is how Lecture 02 compares RAG and fine-tuning (FT) for adding knowledge, and how Lecture 01 applies RAG in its chatbot example: ### Why Lecture 02 Recommends RAG Instead of Fine-Tunin… |
| q4-cross-lecture | Tree | To answer your question, let's break it down into two parts based on the lecture materials: ### 1. Why Lecture 02 Recommends RAG Instead of Fine-Tuning for Adding Knowledge * **Nature of the Fix:** Lecture 02 distinguish… |
| q4-cross-lecture | Graph (course) | Lecture 02 and Lecture 1 provide specific guidance on why RAG is recommended over fine-tuning for knowledge, as well as how RAG is applied in the lecture chatbot example: ### 1. Why Lecture 02 Recommends RAG Instead of F… |
| q4-cross-lecture | Graph v2 (mine) | According to the lecture materials, here are the concepts explaining why RAG is recommended over fine-tuning for adding knowledge, and how the course chatbot example applies it: ### Why Lecture 02 Recommends RAG Instead … |
<!-- /AUTO:answers -->

Plain counts from the runs above (what they mean is written under "Observations on the live runs"):

<!-- AUTO:findings -->
- q1-single: evidence pages received with text, summed over runs: Vector search 2/2; Graph (course) 2/2; Graph v2 (mine) 2/2
- q2-multi: evidence pages received with text, summed over runs: Vector search 6/6; Graph (course) 4/6; Graph v2 (mine) 6/6
- q4-cross-lecture: evidence pages received with text, summed over runs: Vector search 6/6; Graph (course) 6/6; Graph v2 (mine) 6/6
<!-- /AUTO:findings -->

- **Pages found by running search alone (STEP 2, `uv run python -m app.retrieval "LoRA QLoRA difference"`):** five pages, all from Lecture 2, in this order: p.52, p.51, p.60, p.47, p.61.
  The expected evidence page (p.52, LoRA and QLoRA) came first, and p.51 (the PEFT page that introduces both) came second, so the supporting evidence was present. The other three are pages on nearby
  topics: p.47 is about RAG versus fine-tuning, and p.60 and p.61 are the exercise pages. Only p.52 is needed for the answer, so this is a case where search returns the evidence plus three
  pages of similar topics.
- **Tool calls shown by `--trace`:** in the "Tool calls (run 1)" column above, names and arguments; the full list for every run is in `runs.json`.
- **Examples where retrieved information was insufficient, or retrieved but not used:**
  - Not retrieved: on q2 the course Graph and Tree never returned L3 p.13 (0 of 2 runs each); vector search and Graph v2 returned it in 2 of 2. The course Graph's two answers and Tree's second
    answer were still correct, because p.39 and p.40 carry the answer, so p.13 is supporting evidence, not required evidence (see Limitations).
  - Retrieved but not used: in Graph v2 q2 run 1 and Tree q2 run 1 the text of p.40 reached the model, and the answer still handed the second half of the question back as
    a hint ("check whether everything is copied...") instead of answering it. Retrieval was fine; the "guide with hints" rule in the instructions won. Judged partial.
  - Full context q4 had every page in the input and returned only pointers to pages and questions to think about, no explanation. Judged partial.
- **Method I would adopt, and limits of the comparison:** vector search stays the default. The rule I wrote before the runs (Graph v2 only if it receives at least as many evidence
  pages as vector search on q2 and q4 AND its mean input tokens stay under 2 times) was met: 6 of 6 against 6 of 6 on both questions, and 1.3 times (8,678 against 6,599) and 1.7 times
  (9,948 against 5,961) the input tokens. The rule is only a necessary condition ("only if"), and the result is a tie on evidence at a higher cost, so it is not a reason to switch.
  Graph v2 is better than the course Graph on q2 (6 of 6 evidence pages against 4 of 6), and that is all the live runs support. Full context is a baseline only: it covers 438 pages, not
  214, costs about 13 times as much as vector search per run, and cannot be compared fairly. Limits: 2 runs per method per question is too few to rank methods (slide 29: do not rank methods
  from a single success or failure), one model, four questions, and the times are noisy (the same vector query took 16.5 s once and 3.6 s the next time).
- **Observations on the live runs** (drafted by Claude from the saved runs, see "Use of AI tools"):
  - Every method answered q1 and q3 correctly in every run, and q3 (not in the materials) was handled correctly by all five methods: all 9 q3 runs said the measured values are not in the
    materials. Six of them (vector search, Graph and Graph v2) then cited pages such as p.13 or p.18 for the general point that one run proves little, which is related text and not evidence for the missing numbers.
  - The runs differ on cost, not on correctness. Mean input tokens per run over the four questions: vector 5,907, Graph v2 8,786, course Graph 10,101, Tree 17,989, full context 117,029.
    Mean estimated cost per run: $0.0027, $0.0031, $0.0034, $0.0056 and $0.0358. The whole comparison cost $0.26.
  - Tree is the slowest and the most expensive retrieval method (mean 45 s; one q4 run took 148 s and 36,610 input tokens, listing almost all of Lecture 1). Full context is the fastest
    (mean 6 s) because it makes one request and no tool calls, and the most expensive.
  - Graph v2 never used its new tool: `read_page` was called in 0 of 8 runs, and no evidence page was ever only in the preview tier, so the preview part of the design was not tested.
    The model searched a second time instead in 3 of 8 runs, and those runs used 12,687 to 15,614 input tokens against 4,669 to 5,880 for a single search. The model's number of searches
    matters more for cost than the page budget.

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

#### Live comparison (my key; `uv run python -m app.compare`, 36 runs, saved in `results/compare/runs.json`)

The tables under "Results by method" are the full result. Evidence pages received with text, summed over the 2 runs (a page counts only if a tool returned its body text):

| Question | Vector search | Course Graph | Graph v2 | Tree |
|---|---|---|---|---|
| q1-single (1 evidence page) | 2 of 2 | 2 of 2 | 2 of 2 | 2 of 2 |
| q2-multi (3 evidence pages) | 6 of 6 | 4 of 6 | 6 of 6 | 4 of 6 |
| q4-cross-lecture (3 evidence pages) | 6 of 6 | 6 of 6 | 6 of 6 | 6 of 6 |

Mean input tokens per run:

| Question | Vector search | Course Graph | Graph v2 | Tree | Full context |
|---|---|---|---|---|---|
| q1-single | 3,005 | 5,769 | 5,880 | 13,699 | 117,027 |
| q2-multi | 6,599 | 5,340 | 8,678 | 15,134 | 117,031 |
| q3-absent | 8,063 | 14,912 | 10,640 | 5,670 | 117,021 |
| q4-cross-lecture | 5,961 | 14,383 | 9,948 | 37,454 | 117,037 |

What the live runs say about the offline claims:

- **Confirmed: the course Graph misses L3 p.13 on q2.** It did in 2 of 2 real runs, and so did Tree. Graph v2 returned it in 2 of 2, as vector search did. The offline check had predicted this
  for the Graph from stand-in entry points; here the entry points came from real queries.
- **Confirmed: Graph v2 does not beat vector search.** Equal evidence on all three answerable questions, and more input tokens on every one of them (1.96, 1.32 and 1.67 times on q1, q2 and q4).
- **Not confirmed: the size of the saving over the course Graph.** Offline, Graph v2 returned 38% less text. Live, mean input tokens over the four questions were 8,786 against 10,101, 13% less, and per
  question the difference goes both ways: 29% less on q3, 31% less on q4, about equal on q1, and 63% more on q2. The reason is the number of searches: in the runs where the model searched twice, a second
  result set was added to the input.
- **Not tested: the preview tier.** `read_page` was never called and no evidence page was only a preview (see Observations above).
- **A small positive that my gold pages did not capture.** On q4 Graph v2 cited L2 p.27 in both runs, a quiz-answer page that says the first move for outdated knowledge is to search and pass new material
  (RAG). I read it and it supports the point, so Graph v2 found valid evidence outside my fixed list. Vector search did not cite it.

### Improved and failed examples

- Improved (live): q2, L3 p.13 received in 2 of 2 Graph v2 runs where the course Graph and Tree received it in 0 of 2. Improved (offline): 38% less text than the course Graph with the same or better recovery.
- Improved (live), small: q4 Graph v2 found L2 p.27 as extra supporting evidence.
- Failed (live): the preview tier and `read_page` were never used; the second search the model chose to make cost more than the budget saved; Graph v2 costs more than vector search on every question
  for the same evidence; q2 run 1 answered only half the question (a hint instead of the answer), although p.40 had been received.
- Failed (offline): L2 p.47 demoted to a preview; L2 p.46 and p.47 not reached from L1 p.49. (Live, q4 got all three evidence pages with every method, so the offline worry did not show up.)
- Unchanged by design: graph edges (`related_term` edges are still unused), the entry points, the embedding model, the index.

### Whether to adopt it for my use

No. Use vector search as the default. On the questions I tested it returns the same evidence for the least text, and Graph v2 uses 1.3 to 2 times the input tokens per question (about 1.15 times the estimated cost over the whole set) with no gain. Graph v2 is worth keeping
as a corrected version of the course Graph, which should be used instead of it when a graph method is wanted: it returned p.13 where the course Graph did not, for about the same cost. What would change
my mind: a question set where vector search's top 5 misses an evidence page (none of my three answerable questions did), or runs where the model uses `read_page` and the preview tier saves tokens.
The pre-registered rule in the Exercise section was met, but it asked only for a tie on evidence, so I treat it as too weak and did not follow it to adoption.

### Limitations

- The offline numbers use a stand-in question and 6 start pages; they are a mechanism check, not an accuracy result. The stand-in favours nearest-neighbour baselines.
- Two runs per method per question, one model, four questions. The live tables show which pages arrived and which were cited; they cannot rank the methods.
- My gold pages were fixed before the runs and are not all required evidence. All answers to q1 were correct, and p.51 also holds the LoRA and QLoRA explanation, so p.52 is not the only supporting page; the two q2 answers from the course Graph and the second Tree answer were correct without p.13.
  So "gold pages received" measures whether the pages I chose arrived, not whether the answer was supported. I did not change the gold pages afterwards.
- The citation counts depend on a parser. My first parser missed forms such as "PDF pp. 39, 40" and the full-context citation format, and undercounted. I fixed it (35 tests cover the formats) and `report.py` re-reads
  the citations from the saved answers, so `runs.json` itself is unchanged. One answer (Tree q2 run 2) cites pages with no lecture number next to them and is counted through a fallback that assumes
  the one lecture it names.
- The Judgement column was written by Claude, not by an independent human, and I skimmed the longer answers (q4) rather than reading every line.
- Many answers are in Japanese (the materials are Japanese) and the others in English, which does not change which pages were used but makes reading the answers slower.
- Times are noisy and depend on the network and the API on the day; compare tokens and cost, not seconds.
- One data revision (`1ce722c`), Japanese pages only; the English index was not available when this was written.
- Full context searched 438 pages and the other methods 214, so full context is not a like-for-like row.

### Use of AI tools

Claude (an AI assistant) read the course repository, found the ordering problem in the course Graph, wrote the Graph v2 code, tests and scripts, ran the offline parts in a sandbox without a Gemini key, and
drafted this file. I ran the live commands on my machine with my key (STEP 2, one trace run and the 36-run comparison). Claude then read the saved runs, fixed the citation parser after finding it
undercounted, wrote the Judgement column and drafted the live results and observations. I have not independently re-graded every answer, so the Judgement column should be read as an AI's reading.
Course page text is not copied here (the materials may not be shared); the pages are described in my own words.

### Observations and questions

- The course Graph's slot budget is spent mostly on slide neighbours, so "related pages" often means "pages next to the entry point". Ranking by the question fixed the p.13 case, in the live runs as well as offline.
  It is almost the same thing as a larger top-k restricted to the neighbourhood, and I could not show that the graph restriction itself is useful: vector search returned the same evidence pages.
- A shared-term edge is noisy when the word has several senses (here, memory of an agent and memory of a GPU). Ordering candidates by the term's frequency does not help; the question does.
- What the model does matters as much as what the retriever returns. All three partial answers came from the "guide with hints" rule, not from missing evidence, and the number of searches the model chose
  changed input tokens by a factor of 2 to 3 for the same method and question.
- Question: would the unused `related_term` edges (term to term) help a cross-lecture question where vector search's top 5 does miss a page? None of my four questions was hard enough to show it.
