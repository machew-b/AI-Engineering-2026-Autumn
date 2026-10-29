from app import glossary_data as gd
from app import scoring as sc

DATA = gd.build_dataset()
DEFS = {t["id"]: t["definition"] for t in gd.load_terms()}


def oracle(question):
    """Always right: the definition for glossary terms, 'not in glossary' for the rest."""
    item = next(i for i in DATA["test"] if i["question"] == question)
    g = DATA["gold"][item["id"]]
    return DEFS[g["term_id"]] if g["kind"] == "definition" else gd.ABSTAIN_ANSWER


def test_normalize_and_think_block():
    assert sc.normalize("ADK　Web") == sc.normalize("adk web") == "adkweb"
    assert sc.clean_answer("<think>x\ny</think>\n答え") == "答え"


def test_abstain_markers():
    assert sc.is_abstain("用語集に記載がありません。確認が必要です。")
    assert sc.is_abstain("すみません、わかりません")
    assert not sc.is_abstain("LoRAは低ランク行列だけを学習する手法です。")


def test_score_definition_needs_every_phrase():
    gold = {"kind": "definition", "must_include": ["低ランク", "アダプタ"]}
    assert sc.score_answer("低ランク行列を学習し、アダプタとして保存する", gold)["ok"]
    assert not sc.score_answer("低ランク行列を学習する", gold)["ok"]
    assert not sc.score_answer("", {"kind": "definition", "must_include": []})["ok"]   # no phrases is never a pass


def test_score_abstain():
    gold = {"kind": "abstain", "must_include": []}
    assert sc.score_answer("用語集に記載がありません。", gold)["ok"]
    assert not sc.score_answer("Dockerはコンテナを動かす仕組みです。", gold)["ok"]


def test_oracle_gets_everything_right():
    summary, rows = sc.evaluate(oracle, DATA["test"], DATA["gold"], "oracle")
    assert summary["overall_rate"] == 1.0 and summary["over_abstain_rate"] == 0.0
    assert all(summary[f"{c}_rate"] == 1.0 for c in sc.CATEGORIES)
    assert len(rows) == 58


def test_always_abstain_is_caught_as_dodging():
    summary, _ = sc.evaluate(lambda q: gd.ABSTAIN_ANSWER, DATA["test"], DATA["gold"])
    assert summary["unknown_rate"] == 1.0 and summary["seen_rate"] == 0.0
    assert summary["over_abstain_rate"] == 1.0 and summary["unknown_asserted_rate"] == 0.0


def test_always_inventing_is_caught_as_asserting():
    summary, _ = sc.evaluate(lambda q: "それは大量のテキストで学習するモデルです。", DATA["test"], DATA["gold"])
    assert summary["unknown_rate"] == 0.0 and summary["unknown_asserted_rate"] == 1.0
    assert summary["over_abstain_rate"] == 0.0


def test_summarize_handles_a_missing_category():
    rows = [{"category": "seen", "ok": True, "abstained": False}]
    s = sc.summarize(rows, "x")
    assert s["seen_rate"] == 1.0 and s["unknown_rate"] is None and s["unknown_asserted_rate"] is None
