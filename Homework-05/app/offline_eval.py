"""Offline mechanism check for Graph v2. No API key, no network: it only reads data/rag_data/.

Question: when vector search found ONE of the pages a question needs (among its top 3), which of the other
needed pages does each method add, and how much text does it return?

There is no question embedding offline, so the "query" is a stand-in and the result is NOT a measurement of
live behaviour (see answer.md):
  - entry points: the needed page and its 2 nearest pages by the stored page embeddings;
  - query distance: cosine distance to the mean of those 3 vectors.
The live comparison (app/compare.py) is what tests the real system.

    uv run python -m app.offline_eval           # prints the tables and writes results/offline/
"""
import json
import math
import re
import sqlite3
from pathlib import Path

from app import retrieval as r
from app.config import GRAPH2_FULL, GRAPH2_PREVIEWS, GRAPH_MAX_RESULTS, RAG_DB, RAG_SOURCE

OUT = Path(__file__).resolve().parents[1] / "results" / "offline"

# Evidence pages (document id + PDF page) fixed BEFORE any method was run. Q1 to Q3 are the course's examples
# (Lecture 05 problem page); Q4 is my own cross-lecture question. Q3 has no evidence page.
CASES = [
    {"id": "q1-single", "gold": ["lec02-main-p052"]},
    {"id": "q2-multi", "gold": ["lec03-main-p013", "lec03-main-p039", "lec03-main-p040"]},
    {"id": "q4-cross-lecture", "gold": ["lec01-main-p049", "lec02-main-p046", "lec02-main-p047"]},
]


def load_vectors(path: Path = RAG_DB) -> dict[str, list[float]]:
    """Read the stored page embeddings (float32, unit length) without the sqlite-vec extension."""
    import struct
    db = sqlite3.connect(path)
    try:
        rows = db.execute("SELECT page_id, embedding FROM chunks ORDER BY page_id").fetchall()
    finally:
        db.close()
    return {pid: list(struct.unpack(f"{len(blob) // 4}f", blob)) for pid, blob in rows}


def unit(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values))
    return [v / norm for v in values]


def distance(a: list[float], b: list[float]) -> float:
    return 1.0 - sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def stand_in(start: str, vectors: dict[str, list[float]]) -> tuple[list[str], dict[str, float]]:
    """Entry points (start + its 2 nearest pages) and the distance of every page to their mean vector."""
    near = sorted((p for p in vectors if p != start), key=lambda p: (distance(vectors[start], vectors[p]), p))[:2]
    seeds = [start] + near
    mean = unit([sum(vectors[p][i] for p in seeds) / len(seeds) for i in range(len(vectors[start]))])
    return seeds, {pid: distance(mean, vec) for pid, vec in vectors.items()}


def run_methods(seeds: list[str], dist: dict[str, float], pages: dict, graph: dict) -> dict[str, dict]:
    """Pages returned with full text ("full") and as previews ("more") by each method."""
    by_dist = sorted(dist, key=lambda p: (dist[p], p))
    out = {
        "vector-5": {"full": by_dist[:5], "more": []},
        "knn-7": {"full": by_dist[:7], "more": []},
        "knn-10": {"full": by_dist[:10], "more": []},
    }
    original = r.search
    r.search = lambda query: [{**pages[p], "distance": dist[p]} for p in seeds]
    try:
        v1 = r.search_graph("stand-in")
    finally:
        r.search = original
    out["graph-v1"] = {"full": [x["page_id"] for x in v1["seeds"] + v1["expanded"]], "more": []}
    v2 = r.graph_v2(seeds, dist, pages, graph)
    out["graph-v2"] = {"full": [x["page_id"] for x in v2["seeds"] + v2["expanded"]], "more": [x["page_id"] for x in v2["more"]]}
    return out


def score(result: dict, gold: list[str], start: str, seeds: list[str], pages: dict) -> dict:
    full, more = set(result["full"]), set(result["more"])
    others = [g for g in gold if g != start]
    return {
        "others_total": len(others),
        "others_in_full": sum(g in full for g in others),
        "others_in_previews": sum(g in more for g in others),
        "full_pages": len(result["full"]),
        "full_chars": sum(len(pages[p]["content"]) for p in result["full"]),
        "off_topic_full": sum(p not in gold and p not in seeds for p in result["full"]),
    }


def evaluate(full: int = GRAPH2_FULL, previews: int = GRAPH2_PREVIEWS) -> dict:
    pages = {p["page_id"]: p for p in r.load_pages(RAG_SOURCE)}
    graph = json.loads(r.RAG_GRAPH.read_text(encoding="utf-8"))
    vectors = load_vectors()
    runs = []
    for case in CASES:
        for start in case["gold"]:
            seeds, dist = stand_in(start, vectors)
            if (full, previews) == (GRAPH2_FULL, GRAPH2_PREVIEWS):
                methods = run_methods(seeds, dist, pages, graph)
            else:  # sensitivity runs: only Graph v2 changes
                v2 = r.graph_v2(seeds, dist, pages, graph, full=full, previews=previews)
                methods = {"graph-v2": {"full": [x["page_id"] for x in v2["seeds"] + v2["expanded"]],
                                        "more": [x["page_id"] for x in v2["more"]]}}
            runs.append({"case": case["id"], "start": start, "seeds": seeds,
                         "returned": methods,
                         "scores": {m: score(res, case["gold"], start, seeds, pages) for m, res in methods.items()}})
    return {"settings": {"full": full, "previews": previews, "v1_max_results": GRAPH_MAX_RESULTS}, "runs": runs}


def summarize(runs: list[dict], methods: list[str]) -> list[dict]:
    """Add up the multi-evidence cases (the ones where there is something left to recover)."""
    rows = []
    multi = [x for x in runs if x["scores"][methods[0]]["others_total"] > 0]
    for m in methods:
        s = [x["scores"][m] for x in multi]
        rows.append({
            "method": m, "starts": len(multi),
            "others_total": sum(x["others_total"] for x in s),
            "others_in_full": sum(x["others_in_full"] for x in s),
            "others_in_previews": sum(x["others_in_previews"] for x in s),
            "mean_full_pages": round(sum(x["full_pages"] for x in s) / len(s), 1),
            "mean_full_chars": round(sum(x["full_chars"] for x in s) / len(s)),
            "mean_off_topic_full": round(sum(x["off_topic_full"] for x in s) / len(s), 1),
        })
    return rows


def tree_preview_stats() -> dict:
    """How informative is the course Tree's page preview (the first sentence or line), and the one-line preview of Graph v2?"""
    pages = r.load_pages(RAG_SOURCE)
    first = lambda p: re.split(r"(?<=[。！？])|\n", p["content"].strip(), maxsplit=1)[0]
    course = {p["page_id"]: first(p) for p in pages}
    header = sum(bool(r.HEADER_LINE.match(v)) for v in course.values())
    same_title = sum(course[p["page_id"]].strip() == p["title"].strip() for p in pages)
    seen: dict[tuple, int] = {}
    for p in pages:
        seen[(p["document_id"], p["section"], course[p["page_id"]])] = seen.get((p["document_id"], p["section"], course[p["page_id"]]), 0) + 1
    repeated = sum(n for n in seen.values() if n > 1)
    v2 = {p["page_id"]: r.preview_line(p) for p in pages}
    return {
        "pages": len(pages),
        "course_preview_is_slide_header": header,
        "course_preview_equals_title": same_title,
        "course_preview_repeated_in_section": repeated,
        "v2_preview_empty": sum(not v for v in v2.values()),
        "v2_preview_is_slide_header": sum(bool(r.HEADER_LINE.match(v)) for v in v2.values()),
    }


def markdown(summary: list[dict]) -> str:
    lines = ["| Method | Other evidence pages (of) | In full text | In previews | Mean full-text pages | Mean full-text characters | Mean off-topic full-text pages |",
             "|---|---|---|---|---|---|---|"]
    for s in summary:
        lines.append(f"| {s['method']} | {s['others_total']} | {s['others_in_full']} | {s['others_in_previews']} | "
                     f"{s['mean_full_pages']} | {s['mean_full_chars']:,} | {s['mean_off_topic_full']} |")
    return "\n".join(lines)


def main() -> None:
    result = evaluate()
    methods = ["vector-5", "knn-7", "knn-10", "graph-v1", "graph-v2"]
    result["summary"] = summarize(result["runs"], methods)
    result["tree_previews"] = tree_preview_stats()
    result["sensitivity"] = {f"full={f}": summarize(evaluate(full=f)["runs"], ["graph-v2"])[0] for f in (2, 4, 6)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "offline_eval.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    (OUT / "offline_summary.md").write_text(markdown(result["summary"]) + "\n", encoding="utf-8")
    print(markdown(result["summary"]))
    print(json.dumps(result["tree_previews"], indent=1))
    print(json.dumps(result["sensitivity"], indent=1))


if __name__ == "__main__":
    main()
