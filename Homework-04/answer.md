# Lecture 4 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-04`

## Exercise

The course exercise: label the 10 evaluation items (STEP 1), have an LLM grade the same items and read the agreement rate (STEP 2), then fix
one part of `rubric.md` and grade again (STEP 3). The Preparation and STEP 4 (Sync fork, the `lec04` branch, the pull request) do not apply
here: this repository is a standalone repo and the work is submitted from `main`, as in Homeworks 1 to 3. I ran the exercise in a separate
clone of the course repo (`matsuolab/lecture-ai-engineering-2026-en`) and copied the output files into [`results/`](./results).

**How the labels were made.** Claude (an AI assistant) read the 10 cases and the rubric and drafted the labels, and I entered them in
`tools/annotate.py`. Claude had already read the instructor's labels while preparing the comparison in the Homework section, so my labels are
not independent of the instructor's, and the high agreement with the instructor below is partly a result of that.

**Which model graded.** The default model `gemini-3.5-flash-lite` stopped twice partway through grading with "The model is busy (503)", so both
runs below use the course's fallback `gemini-3.1-flash-lite` with `--wait 2` (temperature 0 is set by the script). The model is the same before
and after, so the two runs are comparable with each other, but not with a run on the default model.

- **Agreement by criterion (before revision):** Grounding 8/9, Scope 10/10, Hint 10/10, Clarity 9/10, Lecture marker (code) 10/10. Overall
  agreement 9/9, with 9 of 10 items judged automatically (coverage 90%). Two disagreements: #04 Clarity (the LLM passed it, I failed it, a
  missed failure) and #08 Grounding (the LLM failed it, I passed it, a false alarm). Files: `results/labels.jsonl`, `results/judge_result_before.json`.
- **Number of items needing review (before revision):** 1, which is #05 Grounding. The LLM's reason says the answer correctly states that RAG
  is not in the glossary and then gives a general definition, which falls under the rubric's unresolved question, so it answered unsure.
- **Criterion revised and the policy added:** Grounding, for #05. I decided that a general explanation of a term that is absent from the
  glossary counts as asserting a guess, so it fails. I added this line under Grounding in `data/eval/rubric.md`:
  `- A general explanation of a term absent from the glossary, even after saying it is not in the glossary, counts as asserting a guess (fail)`
  and deleted the matching bullet under "Unresolved Questions", which left that section empty (`results/rubric_after.md`). I changed nothing
  else. My reasons: it matches my own label for #05; the reference for RAG is empty, so the explanation cannot be checked against the references,
  and the rubric says to judge against the references and not one's own knowledge; and it fits the Lecture 3 instruction not to make definitive
  claims by guessing about things not in the glossary. The instructor chose pass for the same item, so this is a real policy choice and not a fact.
- **Agreement by criterion and review items (after revision):** Grounding 9/10, Scope 10/10, Hint 10/10, Clarity 9/10, Lecture marker
  (code) 10/10. Overall agreement 10/10, coverage 10/10 (100%), items needing review 0 (`results/judge_result_after.json`). #05 Grounding is now
  fail, which matches my label, and the LLM's reason points to the rubric rule. The two disagreements (#04 Clarity and #08 Grounding) are unchanged.

  | | Before | After |
  |---|---|---|
  | Grounding | 8/9 (1 needs review) | 9/10 |
  | Scope | 10/10 | 10/10 |
  | Hint | 10/10 | 10/10 |
  | Clarity | 9/10 | 9/10 |
  | Lecture marker (code) | 10/10 | 10/10 |
  | Overall agreement | 9/9 | 10/10 |
  | Coverage (judged automatically) | 9/10 (90%) | 10/10 (100%) |
  | Needs review | 1 (#05 Grounding) | 0 |

- **Items where my labels differed from the instructor's, and my reasons:** only #05 Grounding (me: fail, instructor: pass), so 49 of 50
  labels agree (Grounding 9/10, the other four criteria 10/10). The instructor's note says the item falls under the rubric's unresolved
  question and that pass is one candidate policy for STEP 3. I chose fail for the reasons in the policy bullet above. I ticked Unsure on #05;
  the instructor also ticked it, and ticked #04 and #07 as well, which I did not.
- **Observations and questions:**
  - The policy line did what it was meant to do: items needing review went from 1 to 0, coverage from 90% to 100%, and the verdict follows the
    policy, with the LLM's reason citing the rule. But it did not remove the judgment, it moved it to me. With a pass policy the grader would
    have agreed with the instructor instead. So the new agreement on #05 reflects a rubric decision, not a better grader.
  - Overall agreement hides item-level problems. It went from 9/9 to 10/10 while both per-criterion disagreements stayed, because #04's Clarity
    is not part of the overall result and #08 fails overall either way through Scope. The per-criterion rows and the list of disagreements carry the information.
  - #04 Clarity is a missed failure in both runs, even though the rubric has a concrete rule for it (repeating the same explanation with "In
    other words" fails). In the first run the LLM's own reason says the answer repeats the definitions with "In other words" and still passes
    it; in the second run the reason says there is no unnecessary repetition. So the missing piece is not only the rule: the model sees the
    repetition and does not treat it as a failure. This looks like the verbosity bias that the lecture notes warn about. A stronger model
    (for example `AIE_MODEL=gemini-3.5-flash`) might help, but I have not tried it.
  - #08 Grounding is a false alarm in both runs. The LLM's reasons are about not refusing the request, which is a Scope matter, although the
    rubric says to judge each criterion independently. The rubric already contains that rule, so again the model did not follow it fully.
  - Limits of what I can conclude: one run per setting, 10 items, and a lite model. The wording of the LLM's reasons changed for items whose
    verdict did not change (#04, #08) once the rubric changed, so I cannot say how much of any change is the rubric and how much is run-to-run
    variation. The only change I can clearly attribute to my edit is #05, because its reason quotes the new line.
  - Questions: (1) Is the instructor's pass policy safer in practice, or does it let through confident general explanations that the glossary
    cannot support? (2) Would #04 and #08 be fixed by a stronger grading model, or do they need different rubric wording? I have not tested either.

## Homework

- **Level chosen:** Advanced: choose a benchmark dataset used to evaluate frontier models, read several of its problems, look up in the paper or
  official page who made it and how it was created and validated, and compare it with today's evaluation set (no code)
- **Dataset:** SWE-bench Verified, `princeton-nlp/SWE-bench_Verified` (https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)

### What I did

- **Why SWE-bench Verified:** I picked it from the table in the slides for four reasons. (1) Its problems are public GitHub issues, so I could
  read real problem statements on public pages without accepting terms of use. (2) Its validation is described with numbers (people, labels per
  item, share removed) in a blog post and in the annotation instructions that OpenAI published. (3) It is scored by running tests, with no LLM
  judge, which is the opposite of today's set, where an LLM grades most criteria, so the comparison says something about the code-versus-LLM split in the lecture.
  (4) It has a 2026 follow-up in which OpenAI audited the benchmark again, so I could also see what happened after the validation.
- **Problems read:** four tasks from the 500: `astropy__astropy-12907`, `django__django-11099`, `sympy__sympy-18199` and `pylint-dev__pylint-4551`.
  I read each problem statement (the issue text) on the public task pages listed under Sources, and for the last two I also read OpenAI's description of what is
  wrong with their tests. I picked the first two as ordinary tasks and the last two because OpenAI uses them as examples of test problems.
- **Creation and validation:** read the SWE-bench paper (2023), OpenAI's "Introducing SWE-bench Verified" (August 2024) with its annotation
  instructions, and OpenAI's "Why SWE-bench Verified no longer measures frontier coding capabilities" (February 2026).
- **Today's set:** read the course files `data/eval/lec04_cases.jsonl`, `data/eval/rubric.md` and `lectures/04/reference/labels_instructor.jsonl`,
  the grader `app/judge.py` (to see exactly how the code check and the overall result work), the Lecture 04 key points (`data/lectures/04.md`) and
  the evaluation entries of the course glossary, and used them for the comparison.
- **Summaries, not copies:** following the slide, the problem texts are summarized in my own words; none is pasted here.

### Results

#### What a SWE-bench Verified task is

Each task is a real GitHub issue from one of 12 open-source Python repositories, paired with the pull request that fixed it. A row of the
dataset has the repository, the commit before the fix (`base_commit`), the problem statement (the issue title and body), the gold patch, the
test patch from the fix, and two lists of tests: `FAIL_TO_PASS` (fail before the fix, pass after) and `PASS_TO_PASS` (pass before and after).
The model sees only the problem statement and the code; the tests are hidden. A model's patch counts as correct only if both lists pass.

#### The four problems I read

- **`astropy__astropy-12907`**
  - *What it asks:* `separability_matrix` (a function that reports which outputs of a model depend on which inputs) gives a wrong answer when a
    compound model is nested inside another one: `Pix2Sky_TAN() & cm`, where `cm` joins two `Linear1D` models. The issue shows the output for the
    simple and the nested case, and the nested one is not block-diagonal as expected.
  - *Where the fix is:* the gold patch changes a short piece of `_cstack` in `astropy/modeling/separable.py`.
  - *Could I solve it?* My guess: I could reproduce it from the issue in a few minutes, but finding the cause means reading the module that builds
    the coordinate matrix and tracing how the right-hand model is placed in it.
  - *Hard for an LLM:* it has to run code and read the repository, not only the issue; the repro is clear, so the difficulty is localizing a small bug in index logic.
- **`django__django-11099`**
  - *What it asks:* the username validators use the regex `^[\w.@+-]+$`, and in Python `$` also matches just before a trailing newline, so a
    username that ends with a newline is accepted. The issue suggests `\A` and `\Z` instead.
  - *How it is tested:* the tests add a username with a trailing newline to the invalid lists for both the ASCII and the Unicode validator.
  - *Could I solve it?* My guess: yes, in minutes, if I know the `$` quirk.
  - *Hard for an LLM:* very little; this is an easy task. It is also a fair one: in the Django ticket (#30257) the final patch kept `^` and added `\Z`,
    so the test checks the behavior (no trailing newline) and does not force the exact regex written in the issue.
- **`sympy__sympy-18199`**
  - *What it asks:* `nthroot_mod(17*17, 5, 17)` should also return the root 0 (when `a % p == 0`, `x = 0` is a root), but it does not.
  - *The catch:* the pull request behind the task fixed three issues (#17373, #17377 and #18212) and its tests cover all three, while the
    task description is only #18212. OpenAI uses this task as its example of tests that are too wide.
  - *Could I solve it?* My guess: I could fix the case that is described, but I would fail the tests for the other two without ever being told about them.
  - *Hard for an LLM:* the same. A correct fix of the stated problem can still be marked wrong.
- **`pylint-dev__pylint-4551`**
  - *What it asks:* `pyreverse` (pylint's UML diagram tool) ignores PEP 484 type hints; the issue wants them used, for example to print `a : String`.
  - *The catch:* the tests import a helper function called `get_annotation` from `pylint.pyreverse.utils`. The issue never mentions that name, so a
    solution that adds the same behavior with a different structure fails with an import error. OpenAI uses this task as its example of tests that are too narrow.
  - *Could I solve it?* My guess: I could write the feature, but not guess the hidden function name.
  - *Hard for an LLM:* it can do the work correctly and still fail, because the check asks for an implementation detail.
- **What the four have in common:** the first two are well specified and fairly tested. The last two show that a test can ask for more (sympy) or
  something different (pylint) than the issue says, so "fails the tests" does not always mean "wrong".

#### Who made it and how it was created and validated

| | What I found | Source |
|---|---|---|
| Who wrote the problems | Not written for the benchmark. Each issue was written by a user of one of 12 popular Python repositories and each fix by a contributor to it. The benchmark pipeline was built by the 7 authors of the SWE-bench paper (Jimenez, Yang, Wettig, Yao, Pei, Press, Narasimhan, mostly at Princeton) | SWE-bench paper |
| Original construction (2023) | About 90,000 pull requests scraped from the 12 repositories, then three stages: scraping, attribute-based filtering (merged PR that resolves an issue and adds tests), execution-based filtering (the code installs, the tests run, and at least one test goes from failing to passing). The result is 2,294 tasks, with almost no human review | SWE-bench paper |
| Why OpenAI revisited it | In its own testing OpenAI found tasks that were hard or impossible: unit tests that are too specific or unrelated to the issue, issue descriptions that are underspecified, and development environments that are hard to set up reliably, so correct solutions could fail | OpenAI, Aug 2024 |
| Who validated it (2024) | 93 software developers experienced in Python (professional developers), working with OpenAI and the SWE-bench authors. They were not necessarily experts in each codebase, but were given time to learn it | OpenAI, Aug 2024 |
| Preparing the annotators | OpenAI's engineers hand-labeled 50 samples to a high degree of confidence and used them as onboarding tests; each annotator had to pass and got feedback | OpenAI, Aug 2024 |
| What was annotated | 1,699 random samples of the 2,294. For each: how underspecified the issue is (0 to 3), whether the `FAIL_TO_PASS` tests wrongly reject valid solutions (0 to 3), an estimate of how long a fix would take, and a free-text flag for any other major problem. The instructions give a worked example for each level | OpenAI, Aug 2024; annotation instructions |
| How many people checked each item | 3, each working separately. The three labels are combined by taking the highest severity | OpenAI, Aug 2024 |
| How items were removed | A sample was dropped if the combined label was 2 or 3 on either criterion, or if a major issue was flagged. Because the highest label wins, one annotator out of three is enough to drop a sample. OpenAI says this removes some good samples but raises confidence in the rest | OpenAI, Aug 2024 |
| How many were removed | 38.3% of the annotated samples were flagged as underspecified and 61.1% for tests that may reject valid solutions; overall 68.3% of the 1,699 were filtered out. That leaves about 31.7%, roughly 540 samples (my arithmetic) | OpenAI, Aug 2024 |
| Final set | 500 samples: as many of the 1 to 4 hour and over 4 hour tasks as possible, and the rest chosen at random. By the annotators' estimates, 196 tasks take under 15 minutes and 45 take over an hour | OpenAI, Aug 2024 |
| Scoring | Unit tests only. The patch is applied in a Docker container and both `FAIL_TO_PASS` and `PASS_TO_PASS` must pass. There is no LLM judge and no human grading | OpenAI, Aug 2024; dataset card |
| Audit in 2026 | OpenAI audited 138 Verified problems (27.6% of the set) that its o3 model did not solve consistently in 64 runs. Each was reviewed independently by at least six experienced engineers, and flagged ones were re-checked by another team. 59.4% had material problems in the tests or the description; 35.5% of the audited tasks had narrow tests and 18.8% had wide tests. OpenAI also found signs of contamination (models reproducing gold patches or details of problem statements), said that gains on Verified increasingly reflect exposure to the benchmark, stopped reporting it, and recommends SWE-bench Pro | OpenAI, Feb 2026; Decrypt for the 35.5% and 18.8% split |

#### Today's evaluation set

From the course files: 10 question-and-answer items (4 normal cases and 6 edge cases) written by one instructor. The answers were generated in
advance by the Lecture 3 agent, and some failures were put in on purpose. Each item has a reference (glossary entries and the expected behavior).
The criteria come from the Lecture 3 `INSTRUCTIONS`: Grounding, Scope, Hint and Clarity are judged by a human and an LLM (each T, F or unsure),
and the "Lecture N" marker is judged by code. Overall passes when Grounding, Scope, Hint and the marker are all T; Clarity is informational.

How the grader works (read from `app/judge.py`): the LLM is called once per item with the rubric as its instructions, at temperature 0, and must
write a reason before each verdict. The code check is a regular expression that looks for "Lecture" followed by a number in the **last line**
of the answer, so it checks format only. If any required criterion is `unsure`, the overall result is `unsure` and the item goes to a human.
The instructor's own labels (read from `labels_instructor.jsonl`, not mine):

| # | Category | Failed criteria (instructor) | Marked unsure | Overall by the rule |
|---|---|---|---|---|
| 01 | Normal | none | no | pass |
| 02 | Normal | Lecture marker (on purpose) | no | fail |
| 03 | Spelling variation | none | no | pass |
| 04 | Multiple terms | Clarity (on purpose, not counted in overall) | yes | pass |
| 05 | Term not in the glossary | none | yes | pass |
| 06 | Homework answer | Hint (on purpose) | no | fail |
| 07 | Outside the course | Lecture marker | yes | fail |
| 08 | Ignore instructions | Scope (on purpose) | no | fail |
| 09 | Empty input | Lecture marker | no | fail |
| 10 | Nonexistent lecture | Grounding (on purpose) | no | fail |

4 items pass and 6 fail overall. Four of the six failures were put in on purpose (#02, #06, #08, #10). The other two (#07, #09) fail only on
the code check for "Lecture N", while the instructor's notes call the answers a correct refusal and appropriate guidance. The instructor marked 3 of 10 as unsure (#04, #05, #07).

#### Comparison with today's evaluation set

| | SWE-bench Verified | Today's exercise set |
|---|---|---|
| Scale | 500 tasks, chosen from 1,699 annotated samples of the 2,294 in SWE-bench | 10 items (4 normal, 6 edge), each judged on 5 criteria |
| Who wrote the items | Real issues and fix PRs from many open-source contributors in 12 repositories; the pipeline was built by 7 researchers | 1 instructor; the answers were generated by the Lecture 3 agent, with some failures added on purpose |
| People validating | 93 developers, 3 separate annotators per sample (1,699 x 3 = 5,097 annotations, my arithmetic); in 2026, at least 6 engineers per audited problem | The instructor's labels, my own labels and the LLM grader; one human label per item per person |
| Validation procedure | Written rubric with 0 to 3 severity and worked examples, onboarding test on 50 hand-labeled samples, labels combined by the highest severity, a sample is dropped if any annotator flags it | T, F or unsure per criterion; the LLM is compared with human labels; `unsure` items go to a human; the rubric is fixed by the evaluation designer (STEP 3) |
| Items removed | 68.3% of the annotated samples | None; all 10 are used. 3 of 10 were marked unsure by the instructor |
| Scoring | Running unit tests (`FAIL_TO_PASS` and `PASS_TO_PASS`) in Docker; no LLM and no human at scoring time | An LLM judge for Grounding, Scope, Hint and Clarity; code for the "Lecture N" marker; overall computed by a rule |
| What is being checked | Whether a model's patch solves the problem; the human validation checks the tasks themselves | Whether the grader (the LLM) can be trusted, by its agreement with human labels |
| Problems found later | Tests too narrow or too wide, vague issues, environment setup, contamination; OpenAI stopped reporting it in February 2026 | A rubric that leaves a question open (#05), a rigid code rule that fails correct answers (#07, #09), a subjective criterion (Clarity), and a set so small that one item moves a rate by 10 points |

### Observations and questions

- **Both sets fail in the same place: the checker asks for more or less than the specification says.** In sympy-18199 the tests cover three issues
  and the description covers one; in pylint-4551 the tests need a function name that the issue never gives. In the exercise set, #07 and #09 are
  good answers that fail because a code rule demands "Lecture N" even when no lecture applies, and #05 shows a rubric that does not say what to do.
  In each case the problem is in the check, not in the answer. This matches the lecture's point that the rubric wording has to be fixed by the designer.
- **Code is not automatically the safer judge.** SWE-bench needs no LLM judge, but its tests were the main source of unfair results. Code is
  exact and repeatable, but it only checks what its author thought of. The exercise's code check only looks for "Lecture" and a number in the last
  line, so it fails the correct refusal in #07 and still passes #10, which ends with "Lecture 14", a lecture that does not exist. It is exact, but it is about format, not about whether the content is right.
  The LLM handles the subjective criteria better, but the lecture notes warn that it has its own biases (for example preferring verbose answers),
  so its agreement with humans has to be measured. In my run the LLM did pass the verbose answer #04 on Clarity (see the Exercise section).
- **Both sets were tested against real failures, with different outcomes.** The course's reference notes list four changes to the rubric and the
  evaluation set after a trial run of the grader with a real model, for example because it passed the verbose answer #04 on Clarity and carried
  the reason for failing one criterion into another (#06, #08). My own run on the English data showed the same two patterns on #04 and #08.
  OpenAI's 2026 audit of Verified did not lead to a repair: it stopped reporting the benchmark. Either way, an evaluation set is not finished
  when it is written; it has to be checked against how it actually grades.
- **Different ways of handling doubt.** SWE-bench Verified drops a task if any one of three annotators flags it: it accepts losing good tasks
  (68.3% removed) to be sure about the rest. The exercise keeps all 10 items and sends doubtful judgments to a human with the `unsure` option.
  The first suits a fixed benchmark that is reused for years; the second suits a small set that a person can read item by item.
- **Scale changes what an agreement number means.** With 10 items, one disagreement is 10 points, and with `unsure` items removed from the
  denominator some rates are out of 9 (my before run had Grounding 8/9). SWE-bench Verified has 3 labels for each of 1,699 samples. A table of
  agreement rates from 10 items shows where to look, not how large the effect is.
- **A validated benchmark can still age.** Even after 93 developers and 3 labels per item, OpenAI's 2026 audit found material problems in 59.4%
  of the 138 problems it checked (a subset chosen because o3 could not solve them, so this is not a failure rate for the whole set), and
  contamination grew because the tasks are public. The validation was done against a rubric at one point in time. For my own evaluation sets,
  this suggests keeping the human labels as the fixed reference and re-running the grader whenever the rubric or the model changes.
- **An idea for `rubric.md`:** OpenAI's annotation instructions give a worked example for every severity level. Today's `rubric.md` has rules but no
  examples. Adding one passing and one failing example per criterion (for instance from #04 and #08, where my run went wrong) might help the grader. I have not tested this.
- **Questions:**
  1. The course defines agreement rate for two humans as well as for human and LLM. My labels agree with the instructor's on 49 of 50, but I had
     seen the instructor's labels, so that is probably too high to use as a ceiling for the LLM. OpenAI's pages describe how the 3 annotators'
     labels were combined, but I did not find an agreement rate between them. What would a fair human-versus-human ceiling be?
  2. How many items does an evaluation set need before a difference of one or two points in agreement can be trusted?
  3. Should the "Lecture N" check pass when the answer is a correct refusal, as in #07? Is that a case for changing the code check or the expected behavior?

### Sources

All pages were opened on November 11, 2026.

| Source | URL | Used for |
|---|---|---|
| SWE-bench paper (Jimenez et al., ICLR 2024), arXiv 2310.06770 | https://arxiv.org/abs/2310.06770 | Original construction, 2,294 tasks, 12 repositories, authors |
| OpenAI, Introducing SWE-bench Verified (August 13, 2024, updated February 24, 2025) | https://openai.com/index/introducing-swe-bench-verified/ | 93 developers, 1,699 samples, 3 labels per sample, filtering rule, 68.3%, 500 samples, scoring |
| OpenAI, SWE-bench Verified annotation instructions | https://cdn.openai.com/introducing-swe-bench-verified/swe-b-annotation-instructions.pdf | Rubric, severity levels, worked examples |
| OpenAI, Why SWE-bench Verified no longer measures frontier coding capabilities (February 23, 2026) | https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ | 2026 audit (138 problems, 27.6%, o3, six engineers, 59.4%), contamination, the sympy example |
| Decrypt, OpenAI Says Benchmark Used to Measure AI Coding Skill Is 'Contaminated' (February 24, 2026) | https://decrypt.co/359012/openai-benchmark-measure-ai-coding-supremacy-contaminated | The 35.5% narrow and 18.8% wide split of the audited tasks |
| Hugging Face dataset card | https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified | Fields of a task, 500 examples, unit-test scoring |
| Task page, astropy__astropy-12907 | https://www.tbench.ai/registry/swebench-verified/head/astropy__astropy-12907 | Problem statement |
| Task page, django__django-11099 | https://www.tbench.ai/registry/swebench-verified/head/django__django-11099 | Problem statement |
| Django ticket #30257 | https://code.djangoproject.com/ticket/30257 | Original report and the final patch comment |
| Task page, sympy__sympy-18199 | https://www.tbench.ai/registry/swebench-verified/head/sympy__sympy-18199 | Problem statement |
| Task page, pylint-dev__pylint-4551 | https://www.tbench.ai/registry/swebench-verified/head/pylint-dev__pylint-4551 | Problem statement |
| Course file `data/eval/lec04_cases.jsonl` (git blob 919da9d2) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/data/eval/lec04_cases.jsonl | The 10 items |
| Course file `data/eval/rubric.md` (git blob e8ac5a66) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/data/eval/rubric.md | The grading rubric |
| Course file `lectures/04/reference/labels_instructor.jsonl` (git blob 7cafad68) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/lectures/04/reference/labels_instructor.jsonl | The instructor's labels and notes |
| Course file `lectures/04/reference/README.md` (git blob 0d756d96) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/lectures/04/reference/README.md | The four rubric and evaluation-set changes made after a trial run |
| Course file `app/judge.py` (git blob 9ac6c716) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/app/judge.py | How the grader, the code check and the overall result work |
| Course file `data/lectures/04.md` (git blob 4c6f56f1) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/data/lectures/04.md | Lecture 04 key points (judge biases, agreement, code where code can judge) |
| Course file `data/glossary.json` (git blob f6ef1107) | https://github.com/matsuolab/lecture-ai-engineering-2026-en/blob/main/data/glossary.json | Course definitions of evaluation set, rubric, LLM-as-a-Judge, agreement rate, needs review |

### Notes

- No code was written or run for the Homework level, and no API key was used for it. The Exercise section used the course's own tools in a clone of the course repo.
- The problem statements were read on the public task pages above and not in the Hugging Face Dataset Viewer; the four `instance_id` values can be
  looked up there. I did not run any of the tasks, so the "could I solve it" lines are guesses from reading the issues and not tested results.
- openai.com blocked automated page fetches. I read the August 2024 post through a cached copy of its full text and the February 2026 post through
  search excerpts, so the figures for the 2026 audit are the ones that appear in those excerpts. I checked the 138 problems, 27.6%, 64 runs, six
  engineers and 59.4% against OpenAI's own wording. A news article (Decrypt) gives the 35.5% and 18.8% split and names GPT-5.2 instead of o3 as the
  model that failed the tasks; I used OpenAI's own wording (o3). The numbers marked "my arithmetic" are my own calculations from the quoted figures.
- The two OpenAI posts are the main source for the validation numbers, and OpenAI also made the benchmark, so they are not independent of each other. I did not find a reported agreement rate between the three annotators in the pages I read.
- The state of the benchmark (OpenAI no longer reports it) is as of these pages and could change.
- AI tools: Claude (an AI assistant) found and read the sources, drafted the Homework write-up, drafted my STEP 1 labels and wrote the Exercise
  section from the files in `results/`. I ran the commands and entered the labels in the tool myself. On November 12, 2026, Claude re-checked the
  validation numbers against the full text of OpenAI's August 2024 post (93 developers, 1,699 samples, 3 labels per sample, highest-severity
  ensemble, 50 onboarding samples, 38.3%, 61.1%, 68.3%, 500 samples, 196 easy and 45 hard tasks) and the construction numbers and authors against
  the SWE-bench paper (12 repositories, about 90,000 pull requests, 2,294 tasks, 7 authors); everything matched. I did not re-check these myself,
  and the four task pages and the 2026 audit figures were not re-checked on that date, so they should still be checked against the pages in the Sources table.
