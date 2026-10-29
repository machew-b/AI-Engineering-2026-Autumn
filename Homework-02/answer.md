# Lecture 2 Answer

Course: AI Engineering Practice Course 2026 (Matsuo-Iwasawa Lab, UTokyo)
Submission: this repository (`machew-b/AI-Engineering-2026-Autumn`), folder `Homework-02`

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
(`uv run pytest -q`, 37 tests, no GPU or key needed).

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
  examples for 52 definitions, so 8 passes shows each definition about 24 times. This number was my own judgment call and I did not tune it. On the Colab T4 run A
  took 604 s (160 steps) and run B 768 s (208 steps).
- **Run A** trains on the glossary only. **Run B** adds 48 examples of unknown terms answered with "not in the glossary", to test whether
  the judgment about unknowns can be taught, and whether it carries over to different unknown terms.
- **Glossary search** (`app/retrieval.py`): the comparison system. It finds the longest term name or alias inside the question and
  returns that definition, otherwise "not in the glossary". The rule was fixed before any result was looked at and not tuned.

### Results

Training runs:

<!-- AUTO:training -->
| Run | Training examples | Epochs | Steps | Final loss | Seconds | Trainable parameters |
|---|---|---|---|---|---|---|
| A: glossary only | 156 | 8 | 160 | 0.051 | 604 | 6,389,760 of 758,782,784 (0.84%) |
| B: + abstain examples | 204 | 8 | 208 | 0.053 | 768 | 6,389,760 of 758,782,784 (0.84%) |
<!-- /AUTO:training -->

All 58 questions (share correct; for "not in glossary" a correct answer is saying so):

<!-- AUTO:comparison -->
| Question type | n | Base model | Run A (glossary only) | Run B (+ abstain examples) | Glossary search |
|---|---|---|---|---|---|
| Seen wording | 16 | 0% | 100% | 100% | 100% |
| New wording | 16 | 0% | 100% | 100% | 100% |
| Alias | 8 | 0% | 38% | 50% | 100% |
| Left out of training | 6 | 0% | 0% | 0% | 100% |
| Not in glossary (abstain = correct) | 12 | 0% | 0% | 67% | 75% |
| Taught terms answered with "not in glossary" | 40 | 2% | 0% | 0% | 0% |
| All questions | 58 | 0% | 60% | 76% | 95% |
<!-- /AUTO:comparison -->

Answers to the held-out and unknown questions in run A (base model, then after training):

<!-- AUTO:examples -->
| Question | Base model | After training | After: correct? |
|---|---|---|---|
| 「Pi」とは何ですか？ | 「Pi」は、数学の恒等式 $e = 2.71828182845904523536...$ の小数点後の第 1 位小数で… | MCPのクライアントとして使うループの速度を上げるための超高レベルのツールとして存在的に存在するサーバー。サーバーがク… | no |
| 「ADK（Agent Development Kit）」とは何ですか？ | 「ADK（Agent Development Kit）」とは、AIE2026 講座の用語集に載っていない用語です。 確… | LLMの周りを、学習支援・ツール呼び出し・評価と、エージェントの構築から評価までを包みえたプログラム。Claude C… | no |
| 「ツールの名前空間」とは何ですか？ | 「ツールの名前空間」とは、ソフトウェア開発において、特定のツール（例：Python の `requests`、Java… | ツールの用途や引数の意味を定義する場所。Pydantic AIでは package name などで指定できる。本講座… | no |
| 「fetchサーバー」とは何ですか？ | 「fetchサーバー」は、HTTP 通信のループを停止させるために使用されるサーバーです。 このサーバーは、クライアン… | APIを別のプログラムの関数として呼び出すためのサービス。AIE2026ではGemini APIをPythonから呼び… | no |
| 「TestModel」とは何ですか？ | TestModel は、AIE2026 講座の用語集に載っていない用語です。 確認が必要です。 | LLMの周りを、学習ではなくテストするために使う環境とツール。TestModelでは huggingfaceのモデルを… | no |
| 「既定モデル」とは何ですか？ | 「既定モデル」とは、学習プロセスにおいて**学習対象となるデータセットやモデルの構造、パラメータ、トレーニング手順など… | 学習データに固定したモデル。学習するパラメータは少ないので学習も速い。TILEではLoRAで学習する。 | no |
| Transformerの意味を教えてください。 | Transformer は、**「入力と出力の間に直接接続するネットワーク」**という概念を指します。 具体的には、*… | 入力と出力の2段階で学習するモデル。トークンごとのテキストをデータで表し、次に単語や文字で入力し、モデルが次のトークン… | no |
| 強化学習って何ですか？ | 強化学習（Deep Reinforcement Learning）とは、**「人間が直接操作する行動（例えば、車を運転… | 学習データに固定された入力と出力のペア（例：画像とその時のテキスト表示）で学習する手法。次の入力に続くデータも同じよう… | no |
| ベクトルデータベースとはどのようなものか教えてください。 | ベクトルデータベースとは、**ベクトル（数値の列）をデータとして扱うデータベース**です。 ベクトルデータベースは、デ… | NLPの単語や文を長めのトークンに分割し、そのトークンを列挙してメモリを消費する。単語のレベルでデータを表すため、距離… | no |
| プロンプトインジェクションの意味を教えてください。 | プロンプトインジェクションとは、AI に対して特定の文脈やタスクを提示し、その出力を「プロンプトインジェクション」とし… | LLMが人間の質問ではなく、ツールの名前・説明・引数の書き方から、ツールの実体を認識させる方法。Pydantic AI… | no |
| RLHFって何ですか？ | RLHF（Reinforcement Learning from Human Feedback）とは、人間の意見や指示… | LLMの振る舞い（プロンプト・出力・評価）を人の確認と入力で改善する手法。Claude Code・Copilotのエー… | no |
| 蒸留とはどのようなものか教えてください。 | 蒸留とは、液体を溶かす溶媒（水など）を溶媒に溶かすことで、溶媒を抽出し、溶媒を抽出した液体を抽出液として回収するプロセ… | アルコールを溶ける溶剂（通常是水）を添加し、沸点を高くして純度の高いアルコールを製造する技術。純度の高いアルコールを扱… | no |
| Dockerの意味を教えてください。 | Docker は、開発者やエンジニアが、複数の異なる環境（例：開発環境、テスト環境、デプロイ環境など）を統一して管理す… | 開発環境をコンテナとして定義する仕組み。.dockerfileに指定したブランチからイメージを起動して、容器として使う。 | no |
| REST APIって何ですか？ | REST API は、Web 技術において「Web 標準化されたアプリケーションプログラミング接口（インターフェース）… | Webページの読み書きやツールとして使う関数でデータを交換するプログラム。HTTPを媒介として、クライアントからサーバ… | no |
| ONNXとはどのようなものか教えてください。 | ONNX（Open Neural Network Exchange）とは、AI 分野における**データ形式の標準化**… | PyTorchのモデルを2つのファイルから選ぶこと（モデルと出力ファイル）や、TensorFlowのCPU/GPUをモ… | no |
| Kubernetesの意味を教えてください。 | Kubernetes は、Google が開発した、クラウドコンピューティングの「容器化」技術です。 この技術は、アプ… | エージェントのプログラム（ツールの説明文）と、そのプログラムの起動を separate する環境。起動を簡単にするよう… | no |
| LLM-as-a-judgeって何ですか？ | LLM-as-a-judge（大規模言語モデルによる判断）とは、大規模言語モデル（LLM）が、特定の問題や文脈において… | LLMが事実と異なる内容や新しい情報に気づく、評価する、評価する結果をツールとして使う、というロルをモデルとして使い、… | no |
| エンベディングとはどのようなものか教えてください。 | エンベディングとは、植物の葉が光を吸収してエネルギーに変換し、そのエネルギーを細胞内で消費して成長や繁殖を行う過程を指… | LLMの周りを、ループ・ツール・画面（UI）などで包み、実際に作業できるようにするプログラム。Claude Codeや… | no |
<!-- /AUTO:examples -->

**Glossary search, measured offline** (`results/retrieval_baseline.json`): seen 16/16, reworded 16/16, alias 8/8, held-out 6/6,
unknown 9/12, so 55 of 58 (95%). The three misses are all false matches on an unknown term that contains a glossary word:
プロンプトインジェクション returned the definition of プロンプト, "REST API" returned API, and "LLM-as-a-judge" returned LLM. The search
never missed a real term, but it cannot tell "contains a known word" from "is a known word", and it would answer confidently
with the wrong entry. A real search tool would add a similarity score with a threshold or let the model judge relevance.

What the runs showed (all numbers are from the tables above; the 58-question test set is small, so one question is about 2 to 17 percentage points):

- **Wording versus memorizing.** The base model got 0 of 16 on "seen" and 0 of 16 on "reworded". After training both runs got 16 of 16 on both, so
  a new sentence around the same term name made no difference: the model keys on the term name. The gap is aliases, 3 of 8 in run A and 4 of 8 in
  run B. The aliases I tested were never trained on, and for several the model returned another term's definition (in run A, `Model Context Protocol`
  got a Human-in-the-loop-style definition and `ツール` got a guardrail-style one). It learned "this name goes with this text", not what the term means.
  The base model's 0% needs a caveat: the scoring looks for the glossary's own phrases, and the base answers were fluent but generic (for example
  LLM and トークン), so 0% means it does not reproduce the glossary, not that it knows nothing.
- **Terms left out of training.** 0 of 6 for the base model, run A and run B; glossary search got 6 of 6. The base model said "not in the glossary" for
  2 of the 6 (ADK and TestModel) and invented definitions for the other 4. After run A it never abstained and built its answers out of pieces of
  trained definitions (its ADK answer is a blend of the Harness, Coding agent and Pydantic AI definitions). Run B abstained once (Pi) and invented the rest. A term added to the
  glossary after training is simply not there until the model is trained again.
- **Terms that are not in the glossary.** Base model 0 of 12: it explained all 12 confidently, and some answers were plainly wrong (エンベディング as
  something to do with plants and light, Transformer as a network that connects input and output directly). Run A also 0 of 12: it never said "not in the
  glossary", and answered each unknown term in the glossary's style with an invented definition. Run B, which had 48 "not in the glossary" examples, got 8 of 12
  (67%) on terms and wordings it was not trained on, so this judgment can be taught and it carried over. It did not make the model dodge: taught terms
  answered with "not in the glossary" stayed at 0% in both runs. The same lesson as the exercise, from the other side: the model learns what the examples
  show, so abstention appeared only when it was in the data. Run B missed 4 terms: プロンプトインジェクション, LLM-as-a-judge, RLHF and エンベディング.
  The first two contain a glossary word (プロンプト, LLM), and they are also two of the three that the glossary search got wrong, so a shared word in the
  question is a problem for both systems. I have no explanation for RLHF and エンベディング.
- **An odd answer I read.** In run A, the question about エンベディング (not in the glossary) was answered with the Harness definition word for word, with the name
  swapped: 「Claude CodeやPiはエンベディングの例。Piは組み込みツールをread・write・edit・bashの4つに…」. The model reused the nearest trained definition and put the
  asked term in its place. Several other answers contain garbled text mixed with Chinese or English fragments (for example 「太长」 and 「GEMINI-PROPERTIES」 in run A's answer
  for 429エラー), which I take as a sign of a 0.8B model that memorized sentences without understanding them.
- **Results against the exercise.** The exercise (FAQ, JSON format) and this homework point the same way: training changed the form and the wording very reliably
  (format 10% to 100%; seen and reworded 0% to 100%) and did not give a judgment about what the source supports unless examples of that judgment were in the data.

### Training the model versus searching the glossary

This part combines how the two systems work with the numbers measured above.

- **Updating:** the glossary is marked `2026-draft-1` and will change. For search, a changed or new entry is live immediately. A trained model
  has to be trained again for each change, and the 6 held-out terms are exactly that situation: a term added after training. Retraining cost
  10 to 13 minutes of a free T4 here (604 s and 768 s), and the test set has to be run again afterwards to catch regressions.
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
  My numbers agree with this. Glossary search was right on 55 of 58 questions with no training and no GPU, and on every held-out term. The best trained model
  (run B) was right on 44 of 58 and needed 13 minutes of training plus a GPU to answer, and still had the same weakness on unknown terms that contain a glossary word.
  What search cannot do is the one thing training did well here: answer in a set form. With only 12 unknown and 6 held-out questions this is a small test,
  so I would call it a clear direction and not a precise measurement.

### Notes

- Offline tests cover the data split (no test question in training except the intended "seen" ones, held-out phrases not learnable from
  other terms, unknown terms not in the glossary), the scoring (a perfect answerer, an always-refusing and an always-inventing answerer),
  the glossary search, the report tables and the notebook's consistency with the code. They say nothing about how the trained model
  behaves; only the Colab runs do.
- The test set is small (58 questions, 12 unknown terms, 6 held-out), so one question is 2 to 17 percentage points. Differences of one
  or two questions between runs are within the run-to-run noise of GPU training.
- The scoring is lexical (key phrases), so it can mark a correct paraphrase wrong. I read the held-out, unknown and alias answers in `eval_after.json` of both runs
  before writing the findings. The base model's answers were identical in the two runs (58 of 58), so the before side was measured under the same conditions.
- Both Colab runs were done by me on a T4 (Qwen3.5-0.8B, the same revision and library versions as the course notebook). The result files are in `results/run_a`, `results/run_b`
  and `results/exercise`. AI tools helped me write the code, the tests and the first draft of this file; the Colab runs, the reading of the answers and the conclusions are my own.
