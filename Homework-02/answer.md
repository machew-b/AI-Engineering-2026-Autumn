# Lecture 2 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-02`

> Status: the exercise results are in and written up below. The code, the data, the tests and the glossary-search results are
> finished and were run. The Colab results for run A and run B go into the blocks marked `AUTO` with
> `uv run python -m app.report --write` (see `GUIDE.md`).
> Every line below that starts with the word TODO and a bracket is something that can only be written after those runs. Delete this note when none are left.

## Exercise

Course notebook `notebooks/lora_format_tuning.ipynb` (fictional FAQ, JSON output format).

<!-- AUTO:exercise -->
- Executed training myself: yes
- Model and settings: `Qwen/Qwen3.5-0.8B`, LoRA（量子化なし）, lr 0.0002, r 16, alpha 32, 20 epochs, seed 42

| | Format rate | Content rate | Both |
|---|---|---|---|
| Before training | 10% | 0% | 0% |
| After training | 100% | 90% | 90% |

- Regressed questions (passed before, failed after): none

| Knowledge question | Role | Before | After |
|---|---|---|---|
| この講座の最終課題の締切はいつですか | not in the FAQ | format_error | asserted |
| 担当教員の名前は何ですか | not in the FAQ | format_error | needs_review |
| 次回の講義のテーマは何ですか | not in the FAQ | format_error | needs_review |
| 課題の提出期限はいつですか | control (in the FAQ) | format_error | asserted |
<!-- /AUTO:exercise -->

- Remaining failures after training, and their type: 2 of 21 questions still fail, both of them ungrounded questions (the FAQ does not
  cover them, so `needs_review` should be true). 「成績はいつ出ますか」 was answered with the assignment deadline and
  「オフィスアワーは事前予約が必要ですか」 was answered with the office hours, both with `needs_review` false. Type: asserted on an
  ungrounded question, using a different FAQ item. No grounded question was dodged and no format error is left (format 21 of 21).
- Knowledge questions (section 6), what I noticed: of the three facts that are not in the FAQ, the trained model asked for review on
  two (the instructor's name, the next lecture's topic) and asserted on one: for the final assignment deadline it gave the FAQ's
  Sep 30 23:59 deadline, so it reused the nearest FAQ item. The control question (the ordinary submission deadline, which the FAQ
  covers) was answered from the FAQ as it should be, but the answer added 「（日本時間）」, which the FAQ does not say. Before training
  all four outputs were format errors (the `needs_review` key was missing), and the answer to the next-lecture question was a
  submission instruction, not a topic.
- What training changed and what it did not: format went from 2 of 21 valid outputs to 21 of 21 and content from 0 to 19 of 21, with no
  regressions. What it did not give the model is a reliable judgment about what the FAQ supports: of the 6 ungrounded test questions it
  handled 4, and the 2 misses plus one knowledge question are all confident answers built from a nearby FAQ item. All 15 grounded
  questions were answered correctly. The wording of the answers is close to the FAQ text, which fits "learned the format and the
  phrasing" better than "learned to judge".

## Homework

- **Level chosen:** Advanced (build Q&A data from the course glossary, train on it instead of the FAQ, prepare my own evaluation,
  compare before and after, and discuss training versus a system that searches the glossary)

### What I did

The notebook is `notebooks/lora_glossary_tuning.ipynb`; the data and scoring code are in `app/` and are covered by offline tests
(`uv run pytest -q`, 37 tests).

- **Training data** (`app/glossary_data.py`): the course script's two wordings (`「{term}」とは何ですか？` and `{term}について簡単に説明してください。`)
  for every glossary term, plus one alias wording (`{alias}とは何ですか？`, first alias only). The glossary has 58 terms; 6 are held
  out (below), so 52 are trained: 156 examples in run A. Each record is `system + user + assistant` in the same `messages` format as the
  course notebook's `to_chat`, so it goes straight into `Dataset.from_list` and the same `SFTTrainer`.
- **Prompt:** one system prompt says to answer with the glossary definition and to answer "not in the glossary" for other terms. The
  glossary is not in the prompt (closed book). Training, the before run and the after run all use the same prompt.
- **Test set, 58 questions** (never shown with their gold answers):

  | Type | n | What it tests |
  |---|---|---|
  | seen | 16 | the exact question wording used in training (recall) |
  | reworded | 16 | the same 16 terms with a wording never trained on |
  | alias | 8 | an alias that was not trained on, with a new wording |
  | heldout | 6 | glossary terms left out of training on purpose (`pi`, `adk`, `tool-namespace`, `fetch-server`, `test-model`, `default-model`) |
  | unknown | 12 | terms that are not in the glossary at all (for example Transformer, RLHF, Docker, REST API); the right answer is "not in the glossary" |

  The held-out terms are recent or course-specific, so the base model is unlikely to know them. A test checks that their gold phrases
  do not appear anywhere in the text used for training, so they cannot be learned from another term's definition.
- **How I prepared the "not in the glossary" questions:** I wrote 36 terms that the glossary neither defines nor mentions as a name
  (checked by a test, including that no unknown term appears inside any definition). 12 are for the test and 24, disjoint from them,
  are only used in run B. They mix general machine-learning terms (Transformer, RLHF), tools (Docker, Kubernetes) and three terms that
  contain a glossary word (プロンプトインジェクション, REST API, LLM-as-a-judge) on purpose, because real questions look like that.
- **Gold answers and scoring** (`app/scoring.py`): each glossary question has 2 short key phrases taken from the definition; the answer
  is correct only if both appear. An unknown-term question is correct if the answer says it is not in the glossary or needs checking.
  This is a lexical check, so a correct paraphrase can be marked wrong; I read the answers in `eval_*.json` as well.
  I also report how often a taught term is answered with "not in the glossary" (dodging), so that always refusing cannot look good.
- **Training:** the course notebook's LoRA settings (Qwen3.5-0.8B at the same revision, r 16, alpha 32, lr 2e-4, cosine, batch 4 x accumulation 2,
  greedy generation, same pinned libraries). The one change is 8 epochs instead of 20: the course data is 14 short examples, here 156
  examples for 52 definitions, so 8 passes already shows each definition about 24 times and keeps training near 10 minutes on a T4.
  This number was my judgment call and was not tuned.
- **Run A** trains on the glossary only. **Run B** (optional) adds 48 examples of unknown terms answered with "not in the glossary", to test whether
  the judgment about unknowns can be taught, and whether it carries over to different unknown terms.
- **Glossary search** (`app/retrieval.py`): the comparison system. It finds the longest term name or alias inside the question and
  returns that definition, otherwise "not in the glossary". The rule was fixed before any result was looked at and not tuned.

### Results

Training runs:

<!-- AUTO:training -->
_Not run yet._
<!-- /AUTO:training -->

All 58 questions (share correct; for "not in glossary" a correct answer is saying so):

<!-- AUTO:comparison -->
_Not run yet._
<!-- /AUTO:comparison -->

Answers to the held-out and unknown questions in run A (base model, then after training):

<!-- AUTO:examples -->
_Not run yet._
<!-- /AUTO:examples -->

**Glossary search, measured offline** (`results/retrieval_baseline.json`): seen 16/16, reworded 16/16, alias 8/8, held-out 6/6,
unknown 9/12, so 55 of 58 (95%). The three misses are all false matches on an unknown term that contains a glossary word:
プロンプトインジェクション returned the definition of プロンプト, "REST API" returned API, and "LLM-as-a-judge" returned LLM. The search
never missed a real term, but it cannot tell "contains a known word" from "is a known word", and it would answer confidently
with the wrong entry. A real search tool would add a similarity score with a threshold or let the model judge relevance.

What the runs showed:

- TODO(findings 1): did the training raise "seen" and "reworded" above the base model? Which of the two moved more, and what does that say about wording versus memorizing?
- TODO(findings 2): what happened on the 6 held-out terms (the base model, the trained model, the search)? Did the trained model invent a definition or say it was not in the glossary?
- TODO(findings 3): what happened on the 12 unknown terms in run A, and in run B if you ran it? Did the judgment about unknowns appear, and did it carry over to terms not used in training? Did taught terms get answered with "not in the glossary" more often?
- TODO(findings 4): one regression or odd answer you read yourself in `eval_after.json`, and what you think caused it.

### Training the model versus searching the glossary

This part is reasoning about how the two systems work, supported by the measured search results above; the observed behavior of
the trained model is in the findings.

- **Updating:** the glossary is marked `2026-draft-1` and will change. For search, a changed or new entry is live immediately. A trained model
  has to be trained again for each change, and the 6 held-out terms are exactly that situation: a term added after training. Retraining cost
  about 10 minutes of a free T4 here, but it also needs the test set to be run again to catch regressions.
- **Where the answer comes from:** search returns the glossary text itself, so it can show its source and cannot paraphrase it wrongly.
  A trained model reproduces learned text from its weights and can blend two definitions or invent one; there is nothing to point to.
- **Wording and judgment:** the model can handle free-form questions and mixed-up wording without a name match, which plain search cannot
  (it needs the term or an alias in the question). But whether to say "not in the glossary" is a judgment, and the lecture's point is that
  training teaches formats and styles more reliably than judgment about unknowns. Search makes that decision with an explicit rule, with its
  own failures (the three collisions above).
- **Cost at question time:** search is a lookup with no GPU. The 0.8B model needs a GPU and a few seconds per answer.
- **When training fits:** a stable style, output format or behavior that must work without extra context (for example always answering in
  the glossary's tone), or knowledge that rarely changes and has to work offline. **When it does not:** facts that change, facts that
  need a source, or small amounts of text that fit in a prompt. For this glossary (58 short entries that change as the course is finalized)
  I would search, and train only if a fixed answer format were needed.
  TODO(findings 5): after reading your tables, add one sentence saying whether your own numbers agree or disagree with this.

### Notes

- Offline tests cover the data split (no test question in training except the intended "seen" ones, held-out phrases not learnable from
  other terms, unknown terms not in the glossary), the scoring (a perfect answerer, an always-refusing and an always-inventing answerer),
  the glossary search, the report tables and the notebook's consistency with the code. They say nothing about how the trained model
  behaves; only the Colab runs do.
- The test set is small (58 questions, 12 unknown terms, 6 held-out), so one question is 2 to 17 percentage points. Differences of one
  or two questions between runs are within the run-to-run noise of GPU training.
- AI tools were used to write the code, tests and the first draft of this file. What I verified myself: the tests pass, the glossary
  search numbers were recomputed, and the Colab results and findings above come from my own runs.
  TODO(notes): once the runs are done, confirm that last sentence is true for you.
