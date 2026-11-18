"""Graph v2 tests. Offline: no API key, no network, no course data needed (except the one marked test)."""
import json
import sqlite3
from pathlib import Path

import pytest
import sqlite_vec

from app import retrieval as r

PAGES = {
    f"lec01-main-p{n:03d}": {"page_id": f"lec01-main-p{n:03d}", "document_id": "lec01-main", "lecture": 1,
                              "document_title": "Lecture 1", "section": "S", "title": f"Title {n}", "page": n,
                              "content": f"4/4 Header\nTitle {n}\nBody line {n}. More text.\n© Lab"}
    for n in range(1, 7)
}
P = list(PAGES)  # p001 .. p006


def make_graph() -> dict:
    nodes = [{"id": p, "kind": "page", "title": PAGES[p]["title"]} for p in P]
    nodes += [{"id": "term:x", "kind": "term", "title": "X"}, {"id": "term:big", "kind": "term", "title": "BIG"}]
    edges = [{"source": a, "target": b, "relation": "next_page"} for a, b in zip(P, P[1:])]
    edges += [{"source": p, "target": "term:x", "relation": "mentions"} for p in (P[0], P[4], P[5])]
    edges += [{"source": p, "target": "term:big", "relation": "mentions"} for p in P]
    edges += [{"source": "term:x", "target": "term:big", "relation": "related_term"}]  # not followed, as in the course Graph
    return {"nodes": nodes, "edges": edges}


DIST = {P[0]: 0.0, P[1]: 0.5, P[2]: 0.6, P[3]: 0.9, P[4]: 0.2, P[5]: 0.1}


def test_expand_candidates_hops_and_seed_exclusion():
    found = r.expand_candidates([P[0]], PAGES, make_graph(), hops=2)
    assert P[0] not in found
    assert found[P[1]]["hops"] == 1                     # adjacent page
    assert found[P[4]]["hops"] == 2 and found[P[5]]["hops"] == 2   # shared term
    assert found[P[2]]["hops"] == 2                     # next page of the next page
    assert set(found) == set(P[1:])
    assert [n["id"] for n in found[P[5]]["path"]] == [P[0], "term:x", P[5]]  # the rarer term is kept as the route
    assert r.expand_candidates([P[0]], PAGES, make_graph(), hops=1).keys() == {P[1]}


def test_graph_v2_ranks_by_query_distance_not_by_hops_or_id():
    out = r.graph_v2([P[0]], DIST, PAGES, make_graph(), full=2, previews=2)
    assert [x["page_id"] for x in out["seeds"]] == [P[0]]
    assert [x["page_id"] for x in out["expanded"]] == [P[5], P[4]]      # the 2-hop pages win: they are closest to the query
    assert [x["page_id"] for x in out["more"]] == [P[1], P[2]]
    returned = [x["page_id"] for key in ("seeds", "expanded", "more") for x in out[key]]
    assert len(returned) == len(set(returned))                           # no duplicates
    assert P[3] not in returned                                          # the farthest page is cut by the budget


def test_more_has_preview_but_no_body_text():
    out = r.graph_v2([P[0]], DIST, PAGES, make_graph(), full=1, previews=3)
    assert out["more"]
    for item in out["more"]:
        assert "content" not in item and item["preview"].startswith("Body line")
        assert {"page_id", "title", "page", "lecture", "hops", "path", "distance"} <= item.keys()
    assert all("content" in x for x in out["seeds"] + out["expanded"])
    json.dumps(out, ensure_ascii=False)  # must be serialisable for the tool result


def test_ties_are_broken_by_hops_then_page_id():
    tied = {**DIST, P[1]: 0.3, P[2]: 0.3}
    out = r.graph_v2([P[0]], tied, PAGES, make_graph(), full=4, previews=0)
    order = [x["page_id"] for x in out["expanded"]]
    assert order.index(P[1]) < order.index(P[2])   # same distance: 1 hop before 2 hops


def test_preview_line_skips_title_headers_sources_and_copyright():
    page = {"title": "メモリ", "content": "メモリ\n4/4 　選んだモデル\nPart 6 メモリ\n出典）何か\n© Lab\n\nコンテキストは有限である。続き"}
    assert r.preview_line(page) == "コンテキストは有限である。続き"
    assert r.preview_line({"title": "T", "content": "T\n4/4 H"}) == ""
    long = {"title": "T", "content": "x" * 200}
    assert r.preview_line(long, limit=10) == "x" * 10 + "…"


@pytest.fixture
def tiny_index(tmp_path, monkeypatch):
    """A real SQLite index with fixed 2-d vectors and matching lectures.json / graph.json files."""
    source, graph_file, db_file = tmp_path / "lectures.json", tmp_path / "graph.json", tmp_path / "index.sqlite3"
    source.write_text(json.dumps([{"id": "lec01-main", "title": "Lecture 1", "content": [
        {"section": "S", "content": [{"id": p["page_id"], "title": p["title"], "page": p["page"], "content": p["content"]}
                                      for p in PAGES.values()]}]}], ensure_ascii=False), encoding="utf-8")
    graph_file.write_text(json.dumps(make_graph()), encoding="utf-8")
    db = sqlite3.connect(db_file)
    db.execute("""CREATE TABLE chunks (page_id TEXT PRIMARY KEY, document_id TEXT, lecture INTEGER, document_title TEXT,
                  section TEXT, title TEXT, page INTEGER, content TEXT, embedding BLOB)""")
    angle = {P[0]: (1, 0), P[1]: (0.9, 0.1), P[2]: (0.5, 0.5), P[3]: (0, 1), P[4]: (0.95, 0.05), P[5]: (0.99, 0.01)}
    for pid, vec in angle.items():
        p = PAGES[pid]
        db.execute("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)", (pid, p["document_id"], 1, p["document_title"], "S",
                   p["title"], p["page"], p["content"], sqlite_vec.serialize_float32(list(vec))))
    db.commit()
    db.close()
    for name, value in (("RAG_SOURCE", source), ("RAG_GRAPH", graph_file), ("RAG_DB", db_file)):
        monkeypatch.setattr(r, name, value)
    monkeypatch.setattr(r, "RAG_DOCUMENT_IDS", ("lec01-main",))
    monkeypatch.setattr(r, "embed_text", lambda *_: [1.0, 0.0])
    return db_file


def test_search_graph_v2_end_to_end_with_real_sqlite(tiny_index):
    distances = r.page_distances("anything")
    assert set(distances) == set(P) and distances[P[0]] == pytest.approx(0, abs=1e-6)
    out = r.search_graph_v2("anything")
    assert [x["page_id"] for x in out["seeds"]] == [P[0], P[5], P[4]]   # the 3 closest pages, as in the course Graph
    assert out["expanded"] and "more" in out
    with pytest.raises(ValueError):
        r.page_distances("   ")


def test_tools_return_json_errors_instead_of_raising(tmp_path, monkeypatch):
    from app import tools
    monkeypatch.setattr(r, "RAG_DB", tmp_path / "missing.sqlite3")
    monkeypatch.setattr(r, "RAG_SOURCE", tmp_path / "missing.json")
    assert "error" in json.loads(tools.search_graph_v2("x"))
    assert "error" in json.loads(tools.read_page("lec02-main-p052"))


COURSE_DATA = Path(__file__).resolve().parents[1] / "data" / "rag_data" / "index.sqlite3"


@pytest.mark.skipif(not COURSE_DATA.is_file(), reason="course data not fetched (scripts/fetch_course_data.py)")
def test_v2_adds_the_memory_page_that_the_course_graph_misses():
    """The finding behind Graph v2, on the real data: from Lecture 3 p.39 the course Graph never reaches p.13 (the
    memory concept page, 2 hops through the term 'memory'); Graph v2 returns it as full text."""
    from app import offline_eval as oe
    pages = {p["page_id"]: p for p in r.load_pages()}
    graph = json.loads(r.RAG_GRAPH.read_text(encoding="utf-8"))
    seeds, dist = oe.stand_in("lec03-main-p039", oe.load_vectors())
    methods = oe.run_methods(seeds, dist, pages, graph)
    assert "lec03-main-p013" not in methods["graph-v1"]["full"]
    assert "lec03-main-p013" in methods["graph-v2"]["full"]
    assert len(methods["graph-v2"]["full"]) < len(methods["graph-v1"]["full"])
