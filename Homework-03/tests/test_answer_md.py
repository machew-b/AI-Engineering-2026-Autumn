"""answer.md keeps the structure of Homeworks 1 and 2 and the course template, and the generated blocks can be filled in."""
import re

from app import report as rp

TEXT = rp.ANSWER.read_text(encoding="utf-8")


def test_has_the_sections_of_the_course_template():
    assert TEXT.startswith("# Lecture 3 Answer")
    assert "\n## Exercise\n" in TEXT and "\n## Homework\n" in TEXT
    for label in ("Differences between the Lecture 1", "Tool calls shown by `--trace`", "Number of LLM calls for one question",
                  "Tool added and the description in its docstring", "**Level chosen:** Advanced"):
        assert label in TEXT, label


def test_every_generated_block_exists_and_is_closed():
    for name in rp.blocks([]):
        assert f"<!-- AUTO:{name} -->\n" in TEXT and f"\n<!-- /AUTO:{name} -->" in TEXT


def test_the_docstring_quoted_in_answer_md_is_the_one_in_tools_py():
    from app import tools

    first, rest = tools.make_quiz.__doc__.strip().split("\n\n", 1)
    quoted = re.sub(r"\s+", " ", TEXT)
    assert first in TEXT
    assert re.sub(r"\s+", " ", rest.strip()) in quoted.replace("> ", "")


def test_the_unfinished_parts_are_exactly_the_ones_that_need_the_live_runs():
    todos = {m.group(1) for m in re.finditer(r"TODO\(([^)]*)\)", TEXT)}
    assert todos == {"exercise-1", "exercise-2", "exercise-3", "adk-tools", "adk-answers", "adk-cost", "adk-run", "adk-variation", "adk-choice", "notes-live"}


def test_no_em_dashes():
    assert "\u2014" not in TEXT
