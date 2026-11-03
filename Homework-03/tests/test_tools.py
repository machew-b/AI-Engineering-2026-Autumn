"""Tool tests (no LLM or API key used). The first tests are the course's own; the make_quiz ones are for the exercise tool."""

import json

from app import tools


def test_glossary_ids_are_unique_and_related_links_exist():
    terms = tools.load_glossary()
    ids = [t["id"] for t in terms]
    assert len(ids) == len(set(ids))
    for t in terms:
        for r in t["related"]:
            assert r in ids, f"{t['id']} has a nonexistent id in related: {r}"


def test_search_finds_term_by_name_and_alias():
    for query in ["LoRA", "lora", "Low-Rank Adaptation"]:
        hits = json.loads(tools.search_glossary(query))
        assert hits[0]["term"] == "LoRA", query


def test_search_finds_course_specific_term():
    hits = json.loads(tools.search_glossary("lecNN-start"))
    assert hits[0]["term"] == "lecNN-start tag"


def test_search_limits_number_of_results():
    hits = json.loads(tools.search_glossary("agent"))
    assert 1 <= len(hits) <= tools.MAX_RESULTS


def test_search_reports_not_found():
    assert "was not found" in tools.search_glossary("nonexistent-term-xyz")


def test_lecture_summary():
    assert "agent" in tools.get_lecture_summary(3)
    assert "not available yet" in tools.get_lecture_summary(99)


def test_default_question_of_lecture1_is_answerable_from_glossary():
    """The Lecture 03 agent can correctly answer the Lecture 01 default question (app.ask) using the glossary."""
    from app.ask import DEFAULT_QUESTION

    assert "3 homework levels" in DEFAULT_QUESTION
    hits = json.loads(tools.search_glossary("3 homework levels"))
    assert hits[0]["term"] == "3 homework levels"


# ---- make_quiz (exercise step 4)

def test_make_quiz_returns_a_question_and_the_definition_of_a_term_from_that_lecture():
    for lecture in (1, 2, 3, 5):
        quiz = json.loads(tools.make_quiz(lecture))
        assert set(quiz) == {"lecture", "question", "answer"} and quiz["lecture"] == lecture
        matches = [t for t in tools.load_glossary() if t["lecture"] == lecture and f'"{t["term"]}"' in quiz["question"]]
        assert len(matches) == 1 and quiz["answer"] == matches[0]["definition"]


def test_make_quiz_matches_the_example_in_the_exercise(monkeypatch):
    peft = next(t for t in tools.load_glossary() if t["id"] == "peft")
    monkeypatch.setattr(tools.random, "choice", lambda items: peft)
    quiz = json.loads(tools.make_quiz(2))
    assert quiz["question"] == 'What does "PEFT" mean?' and quiz["answer"].startswith("An umbrella term")


def test_make_quiz_picks_among_the_terms_of_the_lecture():
    seen = {json.loads(tools.make_quiz(2))["question"] for _ in range(200)}
    lecture2 = [t for t in tools.load_glossary() if t["lecture"] == 2]
    assert len(seen) > 1 and len(seen) <= len(lecture2)


def test_make_quiz_handles_a_lecture_without_terms():
    """The course's pytest calls every tool with dummy arguments such as lecture=0, so this must not raise."""
    for lecture in (0, 4, 99, -1):
        message = tools.make_quiz(lecture)
        assert "No glossary terms were found" in message and "01, 02, 03, 05" in message
        assert not message.lstrip().startswith("{")


def test_make_quiz_docstring_says_when_to_use_it():
    doc = tools.make_quiz.__doc__
    assert "review question" in doc and "Give me a review question for Lecture 2" in doc and "integer" in doc
