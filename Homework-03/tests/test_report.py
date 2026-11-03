import json

import pytest

from app import report as rp
from app.compare import QUESTIONS


def run(system, qid, n, calls=(), requests=1, answer="An answer | with a pipe", seconds=2.0, error=None):
    base = {"key": f"{system}:{qid}:{n}", "system": system, "question_id": qid, "run": n, "error": error}
    if error:
        return base
    return {**base, "answer": answer, "tool_calls": [{"tool": t, "args": a} for t, a in calls], "requests": requests,
            "input_tokens": 100, "output_tokens": 10, "seconds": seconds}


@pytest.fixture
def runs():
    out = []
    for n in (1, 2):
        out += [run("bare", "levels", n, answer="I do not know the course."),
                run("pydantic", "levels", n, [("search_glossary", {"query": "3 homework levels"})], 2, "Basic, Implementation, Advanced (Lecture 01)"),
                run("adk", "levels", n, [("search_glossary", {"query": "3 homework levels"})], 2, "Three levels (Lecture 01)", 3.0),
                run("pydantic", "lora-qlora", n, [("search_glossary", {"query": "LoRA"}), ("search_glossary", {"query": "QLoRA"})], 2),
                run("adk", "lora-qlora", n, [("search_glossary", {"query": "LoRA and QLoRA"})], 2),
                run("pydantic", "quiz", n, [("make_quiz", {"lecture": 2})], 2),
                run("adk", "quiz", n, [("make_quiz", {"lecture": 2})], 2)]
    out.append(run("adk", "summary", 1, error="ModelHTTPError: 503"))
    return out


def test_exercise_table_shows_bare_against_agent(runs):
    table = rp.exercise_table(runs)
    assert "Bare model (Lecture 1) | none | 1/1 |" in table
    assert "`search_glossary('3 homework levels')`" in table and "`make_quiz(2)`" in table
    assert "An answer / with a pipe" in table                    # a pipe in an answer must not break the table
    assert "ADK" not in table                                     # the exercise table is about the Pydantic AI agent only


def test_comparison_table_flags_different_tool_order_and_skips_failed_runs(runs):
    rows = {line.split("|")[1].strip(): line for line in rp.comparison_table(runs).splitlines()[2:]}
    assert set(rows) == {"levels", "lora-qlora", "quiz"}         # `summary` had no successful ADK run
    assert "| yes |" in rows["levels"] and "| yes |" in rows["quiz"]
    assert "| no |" in rows["lora-qlora"]                         # two searches against one search with both terms
    assert "100 / 10" in rows["levels"] and "2.0" in rows["levels"] and "3.0" in rows["levels"]


def test_answers_table(runs):
    table = rp.answers_table(runs)
    assert "Three levels (Lecture 01)" in table and "| summary |" not in table


def test_no_runs_say_not_run_yet():
    assert rp.exercise_table([]) == rp.comparison_table([]) == rp.answers_table([]) == rp.NOT_RUN


def test_failed_runs_are_not_used(runs):
    only_failed = [r for r in runs if r.get("error")]
    assert rp.comparison_table(only_failed) == rp.NOT_RUN


def test_replace_block_and_check():
    text = "a\n<!-- AUTO:exercise -->\nold\n<!-- /AUTO:exercise -->\nb"
    assert rp.replace_block(text, "exercise", "NEW") == "a\n<!-- AUTO:exercise -->\nNEW\n<!-- /AUTO:exercise -->\nb"
    with pytest.raises(KeyError):
        rp.replace_block(text, "missing", "x")
    assert rp.unresolved(text) == []
    open_text = f"<!-- AUTO:comparison -->\n{rp.NOT_RUN}\n<!-- /AUTO:comparison -->\nTODO(findings): write this"
    assert len(rp.unresolved(open_text)) == 2


def test_load_runs_reads_the_file_the_runner_writes(tmp_path):
    path = tmp_path / "runs.json"
    assert rp.load_runs(path) == []
    path.write_text(json.dumps([{"key": "a"}]), encoding="utf-8")
    assert rp.load_runs(path) == [{"key": "a"}]


def test_question_ids_used_by_the_report_exist():
    assert [q[0] for q in QUESTIONS[:3]] == ["levels", "lora-qlora", "quiz"]
