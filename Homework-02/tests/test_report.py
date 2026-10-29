import json

import pytest

from app import report as rp


def summary(label, **kw):
    base = {"label": label, "n": 58, "seen_n": 16, "reworded_n": 16, "alias_n": 8, "heldout_n": 6, "unknown_n": 12,
            "seen_rate": 1.0, "reworded_rate": 0.5, "alias_rate": 0.25, "heldout_rate": 0.0, "unknown_rate": 0.0,
            "known_rate": 0.7, "over_abstain_rate": 0.0, "unknown_asserted_rate": 1.0, "overall_rate": 0.6}
    return {**base, **kw}


def rows(ok):
    return [{"id": "heldout-pi", "category": "heldout", "question": "「Pi」とは何ですか？", "answer": "Piは | 何か", "ok": ok, "abstained": False},
            {"id": "seen-llm", "category": "seen", "question": "x", "answer": "y", "ok": True, "abstained": False}]


def write_run(root, name, after_unknown):
    d = root / name
    d.mkdir(parents=True)
    result = {"run": name, "config": {"num_train_epochs": 8}, "data": {"train": 156},
              "training": {"seconds": 600.4, "steps": 160, "final_loss": 0.0123, "trainable": "1 of 2 (50%)"},
              "before": summary("before", unknown_rate=0.1, over_abstain_rate=0.4), "after": summary("after", unknown_rate=after_unknown)}
    (d / "result.json").write_text(json.dumps(result), encoding="utf-8")
    (d / "eval_before.json").write_text(json.dumps({"rows": rows(False)}), encoding="utf-8")
    (d / "eval_after.json").write_text(json.dumps({"rows": rows(True)}), encoding="utf-8")


@pytest.fixture
def results(tmp_path):
    write_run(tmp_path, "run_a", 0.0)
    write_run(tmp_path, "run_b", 0.9)
    (tmp_path / "retrieval_baseline.json").write_text(json.dumps({"summary": summary("retrieval", unknown_rate=0.75)}), encoding="utf-8")
    ex = {"config": {"base_model": "m", "lr": 0.0002, "lora_r": 16, "lora_alpha": 32, "num_train_epochs": 20, "seed": 42},
          "method": "LoRA", "executed_training_myself": True, "regressed": [],
          "before": {"format_rate": 0.1, "content_rate": 0.0, "both_rate": 0.0}, "after": {"format_rate": 1.0, "content_rate": 0.9, "both_rate": 0.9},
          "knowledge": [{"質問": "q1", "FAQ にある": False, "学習前の分類": "format_error", "学習後の分類": "asserted"}]}
    (tmp_path / "exercise").mkdir()
    (tmp_path / "exercise" / "result.json").write_text(json.dumps(ex, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def test_tables_with_all_results(results):
    table = rp.comparison_table(results)
    assert "Run B" in table and "75%" in table and "90%" in table and "| All questions | 58 |" in table
    assert "600" in rp.training_table(results) and "0.012" in rp.training_table(results)
    ex = rp.examples_table(results)
    assert "Piは / 何か" in ex and "| no |" not in ex.split("\n")[2]      # the pipe inside an answer must not break the table
    assert "90%" in rp.exercise_table(results) and "asserted" in rp.exercise_table(results)


def test_missing_results_say_not_run_yet(tmp_path):
    assert rp.comparison_table(tmp_path) == rp.training_table(tmp_path) == rp.exercise_table(tmp_path) == rp.NOT_RUN


def test_run_b_is_optional(results):
    (results / "run_b" / "result.json").unlink()
    table = rp.comparison_table(results)
    assert "n/a" in table and "Run A" in table


def test_replace_block_and_check():
    text = "a\n<!-- AUTO:exercise -->\nold\n<!-- /AUTO:exercise -->\nb"
    new = rp.replace_block(text, "exercise", "NEW")
    assert new == "a\n<!-- AUTO:exercise -->\nNEW\n<!-- /AUTO:exercise -->\nb"
    with pytest.raises(KeyError):
        rp.replace_block(text, "missing", "x")
    assert rp.unresolved(text) == []
    open_text = f"<!-- AUTO:comparison -->\n{rp.NOT_RUN}\n<!-- /AUTO:comparison -->\nTODO(findings): write this"
    assert len(rp.unresolved(open_text)) == 2


def test_answer_md_has_every_block():
    text = rp.ANSWER.read_text(encoding="utf-8")
    for name in rp.blocks(rp.RESULTS):
        assert f"<!-- AUTO:{name} -->" in text and f"<!-- /AUTO:{name} -->" in text
