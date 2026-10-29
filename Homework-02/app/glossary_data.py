"""Build the Homework 2 (Advanced) data from the course glossary.

Standard library only, so the same file runs in Codespaces, in the offline tests and in Colab.

Design in one paragraph: every glossary term except HELDOUT_IDS is turned into question/answer pairs
(the course script's two wordings, plus one alias wording). The test set then asks five kinds of
questions: the exact wording seen in training ("seen"), a new wording of the same term ("reworded"),
an alias not used in training ("alias"), glossary terms that were left out of training ("heldout"),
and terms that are not in the glossary at all ("unknown"). Gold answers are key phrases taken from
the glossary definition, kept apart from the questions and never shown to the model.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY_PATH = ROOT / "data" / "glossary.json"

ABSTAIN_ANSWER = "用語集に記載がありません。確認が必要です。"
SYSTEM = (
    "あなたは AIE2026 講座の用語集の回答係です。質問された用語の定義を、用語集の定義どおりに日本語で答えてください。"
    "用語集に載っていない用語は、定義を作らずに『" + ABSTAIN_ANSWER + "』と答えてください。"
)

# Wordings. The first two are the course script's own templates (scripts/make_sft_dataset.py in the course repo).
TRAIN_TEMPLATES = ["「{term}」とは何ですか？", "{term}について簡単に説明してください。"]
ALIAS_TRAIN_TEMPLATE = "{alias}とは何ですか？"          # used with aliases[0] only
VALID_TEMPLATE = "{term}を説明してください。"            # validation wording, never trained on
REWORD_TEMPLATES = ["{term}の意味を教えてください。", "{term}って何ですか？", "{term}とはどのようなものか教えてください。"]
ALIAS_TEST_TEMPLATE = "{alias}の意味を教えてください。"  # used with aliases[-1], which is not the trained alias

# Test terms (all are trained on, except HELDOUT_IDS). Chosen by hand to cover lectures 1, 2, 3 and 5.
SEEN_IDS = ["llm", "token", "hallucination", "api-key", "rate-limit", "pull-request", "lora", "qlora",
            "overfitting", "quantization", "peft", "ai-agent", "tool", "guardrail", "pydantic-ai", "mcp"]
ALIAS_IDS = ["llm", "hallucination", "rate-limit", "pull-request", "overfitting", "ai-agent", "tool", "mcp"]
HELDOUT_IDS = ["pi", "adk", "tool-namespace", "fetch-server", "test-model", "default-model"]

# Terms that are NOT in the glossary. UNKNOWN_TEST is only for evaluation. UNKNOWN_TRAIN is only used by
# the optional run B, which adds "answer: not in the glossary" examples (the two lists never overlap).
UNKNOWN_TEST = ["Transformer", "強化学習", "ベクトルデータベース", "プロンプトインジェクション", "RLHF", "蒸留",
                "Docker", "REST API", "ONNX", "Kubernetes", "LLM-as-a-judge", "エンベディング"]
UNKNOWN_TRAIN = ["BERT", "GPT-4", "畳み込みニューラルネットワーク", "勾配降下法", "バックプロパゲーション", "ドロップアウト",
                 "活性化関数", "自己注意機構", "ベクトル検索", "プロンプトチェーン", "rebase", "GitHub Actions",
                 "CI/CD", "Terraform", "AWS Lambda", "PostgreSQL", "pandas", "NumPy", "Jupyter Notebook",
                 "Streamlit", "FastAPI", "OAuth", "WebSocket", "正規化"]

# Gold: short key phrases that a correct answer should contain (both required). They come from the
# glossary definition text. For the held-out terms, tests/test_glossary_data.py checks that the phrases
# do not appear anywhere in the training definitions, so they cannot be learned from other terms.
GOLD_PHRASES = {
    "llm": ["大量のテキスト", "予測"],
    "token": ["最小単位", "断片"],
    "hallucination": ["事実と異なる", "もっともらしく"],
    "api-key": ["秘密", "識別"],
    "rate-limit": ["一定時間", "上限"],
    "pull-request": ["別のブランチ", "依頼"],
    "lora": ["低ランク", "アダプタ"],
    "qlora": ["4ビット", "量子化"],
    "overfitting": ["学習データ", "未知の入力"],
    "quantization": ["少ないビット数", "メモリ"],
    "peft": ["総称", "GPUメモリ"],
    "ai-agent": ["ツールを呼び出し", "ループ"],
    "tool": ["用意した関数", "引数"],
    "guardrail": ["望ましくない", "制約"],
    "pydantic-ai": ["エージェントを作る", "フレームワーク"],
    "mcp": ["標準プロトコル", "つなぐ"],
    "pi": ["MITライセンス", "ターミナル"],
    "adk": ["Googleが公開", "adk web"],
    "tool-namespace": ["接頭辞", "区別"],
    "fetch-server": ["Markdown", "uvx"],
    "test-model": ["偽モデル", "ダミー"],
    "default-model": ["gemini-3.5-flash-lite", "安定性"],
}


def load_terms(path: Path | str = GLOSSARY_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["terms"]


def build_messages(question: str) -> list[dict]:
    """The prompt (system + user). Training and evaluation both use this, so only the adapter differs."""
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]


def _record(question: str, answer: str) -> dict:
    # Same "messages" layout as the notebook's to_chat, so Dataset.from_list accepts it directly.
    return {"messages": build_messages(question) + [{"role": "assistant", "content": answer}]}


def build_dataset(terms: list[dict] | None = None, include_abstain: bool = False) -> dict:
    """Return train / valid (lists of {"messages": [...]}), test (id, category, question), gold and meta."""
    terms = terms if terms is not None else load_terms()
    by_id = {t["id"]: t for t in terms}
    for needed in SEEN_IDS + ALIAS_IDS + HELDOUT_IDS:
        if needed not in by_id:
            raise KeyError(f"glossary has no term with id {needed!r}")

    train, valid = [], []
    for t in terms:
        if t["id"] in HELDOUT_IDS:
            continue
        for tpl in TRAIN_TEMPLATES:
            train.append(_record(tpl.format(term=t["term"]), t["definition"]))
        if t["aliases"]:
            train.append(_record(ALIAS_TRAIN_TEMPLATE.format(alias=t["aliases"][0]), t["definition"]))
        valid.append(_record(VALID_TEMPLATE.format(term=t["term"]), t["definition"]))
    if include_abstain:
        for name in UNKNOWN_TRAIN:
            for tpl in TRAIN_TEMPLATES:
                train.append(_record(tpl.format(term=name), ABSTAIN_ANSWER))

    test, gold = [], {}

    def add(qid: str, category: str, question: str, term_id: str | None, kind: str, phrases: list[str] | None):
        test.append({"id": qid, "category": category, "question": question})
        gold[qid] = {"kind": kind, "term_id": term_id, "must_include": phrases or []}

    for i, tid in enumerate(SEEN_IDS):
        term = by_id[tid]["term"]
        add(f"seen-{tid}", "seen", TRAIN_TEMPLATES[0].format(term=term), tid, "definition", GOLD_PHRASES[tid])
        add(f"reworded-{tid}", "reworded", REWORD_TEMPLATES[i % len(REWORD_TEMPLATES)].format(term=term), tid,
            "definition", GOLD_PHRASES[tid])
    for tid in ALIAS_IDS:
        alias = by_id[tid]["aliases"][-1]
        add(f"alias-{tid}", "alias", ALIAS_TEST_TEMPLATE.format(alias=alias), tid, "definition", GOLD_PHRASES[tid])
    for tid in HELDOUT_IDS:
        add(f"heldout-{tid}", "heldout", TRAIN_TEMPLATES[0].format(term=by_id[tid]["term"]), tid, "definition",
            GOLD_PHRASES[tid])
    for j, name in enumerate(UNKNOWN_TEST):
        add(f"unknown-{j + 1:02d}", "unknown", REWORD_TEMPLATES[j % len(REWORD_TEMPLATES)].format(term=name), None,
            "abstain", None)

    seen_in_training = {r["messages"][1]["content"] for r in train + valid}
    for item in test:
        if item["category"] != "seen" and item["question"] in seen_in_training:
            raise ValueError(f"test question also appears in training or validation: {item['question']}")
    if len({item["id"] for item in test}) != len(test):
        raise ValueError("duplicate test ids")

    counts = {c: sum(1 for x in test if x["category"] == c) for c in ("seen", "reworded", "alias", "heldout", "unknown")}
    meta = {"glossary_terms": len(terms), "trained_terms": len(terms) - len(HELDOUT_IDS), "train": len(train),
            "valid": len(valid), "test": len(test), "test_by_category": counts, "include_abstain": include_abstain}
    return {"train": train, "valid": valid, "test": test, "gold": gold, "meta": meta}


def write_jsonl(records: list[dict], path: Path | str) -> None:
    Path(path).write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
