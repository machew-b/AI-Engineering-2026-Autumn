import json
import re

import pytest

from app import glossary_data as gd
from app.scoring import is_abstain, normalize

TERMS = gd.load_terms()
BY_ID = {t["id"]: t for t in TERMS}


def test_glossary_snapshot_is_the_course_draft():
    raw = json.loads(gd.GLOSSARY_PATH.read_text(encoding="utf-8"))
    assert raw["version"] == "2026-draft-1"
    assert len(TERMS) == 58 and len(BY_ID) == 58


def test_sizes_and_categories():
    run_a, run_b = gd.build_dataset(), gd.build_dataset(include_abstain=True)
    assert run_a["meta"]["test_by_category"] == {"seen": 16, "reworded": 16, "alias": 8, "heldout": 6, "unknown": 12}
    assert len(run_a["test"]) == 58 == len(run_a["gold"])
    assert len(run_a["train"]) == 52 * 2 + 52          # 2 wordings + 1 alias wording for each of the 52 trained terms
    assert len(run_a["valid"]) == 52
    assert len(run_b["train"]) == len(run_a["train"]) + 24 * 2
    assert run_a["test"] == run_b["test"]              # the test set does not depend on the run


def test_records_use_the_notebook_messages_format():
    for rec in gd.build_dataset()["train"]:
        assert list(rec) == ["messages"]
        assert [m["role"] for m in rec["messages"]] == ["system", "user", "assistant"]
        assert rec["messages"][0]["content"] == gd.SYSTEM


def test_heldout_terms_are_not_trained_on():
    data = gd.build_dataset(include_abstain=True)
    answers = {r["messages"][2]["content"] for r in data["train"] + data["valid"]}
    for tid in gd.HELDOUT_IDS:
        assert BY_ID[tid]["definition"] not in answers
        for text in [BY_ID[tid]["term"], *BY_ID[tid]["aliases"]]:
            assert not any(text in r["messages"][1]["content"] for r in data["train"] + data["valid"])


def test_only_the_seen_questions_overlap_with_training():
    data = gd.build_dataset(include_abstain=True)
    trained = {r["messages"][1]["content"] for r in data["train"] + data["valid"]}
    for item in data["test"]:
        assert (item["question"] in trained) == (item["category"] == "seen"), item


def test_alias_questions_use_an_alias_that_was_not_trained():
    data = gd.build_dataset()
    trained = {r["messages"][1]["content"] for r in data["train"]}
    for tid in gd.ALIAS_IDS:
        aliases = BY_ID[tid]["aliases"]
        assert len(aliases) >= 2 and aliases[0] != aliases[-1]
        assert gd.ALIAS_TRAIN_TEMPLATE.format(alias=aliases[0]) in trained
        assert gd.ALIAS_TRAIN_TEMPLATE.format(alias=aliases[-1]) not in trained


def test_gold_phrases_come_from_the_definition_and_pick_the_right_term():
    for tid, phrases in gd.GOLD_PHRASES.items():
        assert len(phrases) == 2
        for p in phrases:
            assert normalize(p) in normalize(BY_ID[tid]["definition"]), (tid, p)


def test_heldout_gold_phrases_cannot_be_learned_from_other_terms():
    trained = [t for t in TERMS if t["id"] not in gd.HELDOUT_IDS]
    blob = normalize(" ".join(t["definition"] + t["term"] + " ".join(t["aliases"]) for t in trained) + gd.SYSTEM + gd.ABSTAIN_ANSWER)
    for tid in gd.HELDOUT_IDS:
        for p in gd.GOLD_PHRASES[tid]:
            assert normalize(p) not in blob, f"{p!r} (held-out {tid}) appears in trained text"


def test_real_definitions_never_look_like_an_abstention():
    # otherwise a correct answer could be counted as "said not in the glossary"
    assert [t["id"] for t in TERMS if is_abstain(t["definition"])] == []


def _contains_word(text: str, name: str) -> bool:
    n, t = normalize(name), normalize(text)
    if n.isascii():
        return re.search(rf"(?<![a-z0-9]){re.escape(n)}(?![a-z0-9])", t) is not None
    return n in t


def test_unknown_terms_are_really_not_in_the_glossary():
    assert not set(gd.UNKNOWN_TEST) & set(gd.UNKNOWN_TRAIN)
    assert len(set(gd.UNKNOWN_TEST)) == 12 and len(set(gd.UNKNOWN_TRAIN)) == 24
    names = {normalize(x) for t in TERMS for x in [t["term"], *t["aliases"]]}
    all_definitions = " ".join(t["definition"] for t in TERMS)
    for name in gd.UNKNOWN_TEST + gd.UNKNOWN_TRAIN:
        assert normalize(name) not in names, name
        assert not _contains_word(all_definitions, name), f"{name} is mentioned in a definition"


def test_unknown_test_questions_are_new_wordings():
    data = gd.build_dataset(include_abstain=True)
    train_questions = {r["messages"][1]["content"] for r in data["train"]}
    for item in data["test"]:
        if item["category"] == "unknown":
            assert item["question"] not in train_questions
            assert data["gold"][item["id"]]["kind"] == "abstain"


def test_missing_term_is_reported():
    with pytest.raises(KeyError):
        gd.build_dataset([t for t in TERMS if t["id"] != "llm"])


def test_cli_writes_the_files(tmp_path, capsys):
    import runpy, sys
    script = gd.ROOT / "scripts" / "make_sft_dataset.py"
    sys.argv = [str(script), "--out-dir", str(tmp_path)]
    runpy.run_path(str(script), run_name="__main__")
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl", "gold.json", "manifest.json"):
        assert (tmp_path / name).exists()
    first = json.loads((tmp_path / "train.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert first["messages"][2]["role"] == "assistant"
    assert json.loads(capsys.readouterr().out)["train"] == 156
