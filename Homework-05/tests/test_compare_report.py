"""Live runner and report, tested offline: citations, retrieved-page parsing, a full run with TestModel, the tables."""
import json

import pytest
from pydantic_ai.models.test import TestModel

from app import compare, report


def test_cited_pages_parses_and_deduplicates():
    text = "LoRA freezes weights (Lecture 02 / PDF p.52). Also Lecture 2 / PDF p.52 and Lecture 1 / p.49."
    assert compare.cited_pages(text) == [[2, 52], [1, 49]]
    assert compare.cited_pages("nothing here") == []


def test_retrieved_pages_separates_text_from_titles_only():
    returns = [
        ("search_graph_v2", json.dumps({"seeds": [{"page_id": "lec03-main-p039"}], "expanded": [{"page_id": "lec03-main-p013"}],
                                         "more": [{"page_id": "lec03-main-p040"}, {"page_id": "lec03-main-p039"}]})),
        ("read_page", json.dumps({"page_id": "lec03-main-p040"})),
        ("browse_tree", json.dumps({"node": {"id": "lec02-main-p052", "kind": "page"}, "children": []})),
        ("search_materials", "not json"),
    ]
    got = compare.retrieved_pages(returns)
    assert got["full"] == [[2, 52], [3, 13], [3, 39], [3, 40]]
    assert got["listed"] == []          # p.40 was listed, then read; p.39 is a seed


def test_listed_only_page_is_reported():
    got = compare.retrieved_pages([("search_graph_v2", json.dumps({"seeds": [], "expanded": [], "more": [{"page_id": "lec03-main-p040"}]}))])
    assert got == {"full": [], "listed": [[3, 40]]}


def test_plan_counts_runs():
    todo = compare.plan(compare.METHODS, compare.QUESTIONS, runs=2, full_runs=1)
    assert len(todo) == 4 * (1 + 4 * 2)
    assert todo[0][0] == "full-context:q1-single:1"


@pytest.mark.parametrize("method", ["vector", "tree", "graph", "graph2", "full-context"])
def test_run_once_records_everything_with_a_fake_model(method, monkeypatch):
    page = {"page_id": "lec02-main-p052", "lecture": 2, "page": 52, "title": "t", "content": "c", "distance": 0.1}
    monkeypatch.setattr("app.retrieval.search", lambda q: [page])
    monkeypatch.setattr("app.retrieval.search_graph", lambda q: {"seeds": [page], "expanded": [], "max_hops": 2})
    monkeypatch.setattr("app.retrieval.search_graph_v2", lambda q: {"seeds": [page], "expanded": [], "more": [], "max_hops": 2})
    monkeypatch.setattr("app.retrieval.browse_tree", lambda node_id=None: {"node": {"id": "lec02-main-p052", "kind": "page"}, "children": []})
    monkeypatch.setattr("app.retrieval.read_page", lambda page_id: page)
    monkeypatch.setattr("app.retrieval.get_all_materials", lambda: "materials")
    record = compare.run_once(method, compare.QUESTIONS[0], model_factory=lambda: TestModel(custom_output_text="LoRA freezes W (Lecture 02 / PDF p.52)."))
    assert record["error"] is None and record["cited"] == [[2, 52]]
    assert record["requests"] >= 1 and record["input_tokens"] is not None and record["seconds"] >= 0
    if method == "full-context":
        assert record["tool_calls"] == []
    else:
        assert record["tool_calls"] and record["retrieved"]["full"] == [[2, 52]]


def fake_runs():
    def run(method, qid, n, cited, full, seconds=2.0):
        return {"method": method, "question_id": qid, "error": None, "answer": "Answer text (Lecture 3 / PDF p.13).",
                "tool_calls": [{"name": "search_graph_v2", "args": {"query": "memory"}}], "cited": cited,
                "retrieved": {"full": full, "listed": []}, "seconds": seconds, "input_tokens": 3000, "output_tokens": 200,
                "requests": 2, "cost_usd": 0.001}
    gold = [[3, 13], [3, 39], [3, 40]]
    runs = {compare.run_id("graph2", "q2-multi", 1): run("graph2", "q2-multi", 1, gold, gold),
            compare.run_id("vector", "q2-multi", 1): run("vector", "q2-multi", 1, gold[:2], gold[:2], 3.0)}
    runs["vector:q3-absent:1"] = {**run("vector", "q3-absent", 1, [], []), "answer": "I cannot verify this from the materials."}
    return runs


def test_tables_show_counts_and_never_invent_missing_runs():
    runs = fake_runs()
    text = report.compare_block(runs, {"graph2:q2-multi:1": "correct"})
    assert "| Graph v2 (mine) | 1 | 3/3 | 3/3 |" in text
    assert "| Vector search | 1 | 2/3 | 2/3 |" in text
    assert "correct" in text and "not judged" in text
    assert "| Tree | 0 | Not recorded |" in text                      # a run that was not made stays blank
    assert "says it cannot verify" in text                            # q3: the absent-evidence question
    assert "Vector search 2/3; Graph v2 (mine) 3/3" in report.findings_block(runs).replace("Graph (course) 0/0; ", "")


def test_replace_blocks_and_check(tmp_path):
    text = "a\n<!-- AUTO:compare -->\nold\n<!-- /AUTO:compare -->\n<!-- AUTO:answers -->\nx\n<!-- /AUTO:answers -->\n<!-- AUTO:findings -->\ny\n<!-- /AUTO:findings -->\n"
    new = report.replace_blocks(text, {"compare": "NEW", "answers": "A", "findings": "F"})
    assert "NEW" in new and "old" not in new
    todo = report.check({}, "a\nNot recorded\n<!-- AUTO:compare -->\nNot recorded\n<!-- /AUTO:compare -->\n(fill in after the live runs)")
    assert any("not made yet" in t for t in todo)
    assert any("lines 2, 6" in t for t in todo)                      # prose outside the AUTO blocks, by line number
    assert report.unfinished_lines("<!-- AUTO:x -->\nNot recorded\n<!-- /AUTO:x -->\ndone") == []
    with pytest.raises(SystemExit):
        report.replace_blocks("no blocks", {"compare": "x"})
