import json

from app import glossary_data as gd
from app import retrieval as rt

TERMS = gd.load_terms()
DATA = gd.build_dataset(TERMS)


def test_name_variants_split_the_parenthesis():
    by_id = {t["id"]: t for t in TERMS}
    assert {"llm", "大規模言語モデル"} <= set(rt.name_variants(by_id["llm"]))
    assert {"ツール", "tool use", "function calling"} <= set(rt.name_variants(by_id["tool"]))
    assert "r" not in rt.name_variants(by_id["lora-rank"])      # one-character names are dropped


def test_longest_name_wins_and_english_names_need_word_boundaries():
    assert rt.search("QLoRAとは何ですか？", TERMS)[0]["id"] == "qlora"      # not "lora" inside "qlora"
    assert rt.search("LoRAとは何ですか？", TERMS)[0]["id"] == "lora"
    assert rt.search("ツールの名前空間とは", TERMS)[0]["id"] == "tool-namespace"   # longer than "ツール"
    assert rt.search("Dockerとは何ですか？", TERMS)[0] is None
    assert rt.answer("Dockerとは何ですか？", TERMS) == gd.ABSTAIN_ANSWER


def test_known_questions_are_all_found_and_collisions_are_the_documented_ones():
    summary, rows = rt.evaluate_retrieval(DATA["test"], DATA["gold"], TERMS)
    for c in ("seen", "reworded", "alias", "heldout"):
        assert summary[f"{c}_rate"] == 1.0, c
    wrong = {r["id"]: r["matched_id"] for r in rt.wrong_matches(rows, DATA["gold"])}
    # an unknown term that contains a glossary word is matched to that word's entry (a real weakness of plain search)
    assert wrong == {"unknown-04": "prompt", "unknown-08": "api", "unknown-11": "llm"}
    assert summary["unknown_rate"] == 0.75


def test_committed_baseline_file_matches_a_fresh_run():
    saved = json.loads((rt.RESULTS / "retrieval_baseline.json").read_text(encoding="utf-8"))
    summary, _ = rt.evaluate_retrieval(DATA["test"], DATA["gold"], TERMS)
    assert saved["summary"] == summary, "results/retrieval_baseline.json is stale: run `uv run python -m app.retrieval`"
