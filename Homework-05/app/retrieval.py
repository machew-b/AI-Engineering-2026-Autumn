"""Lecture 05: page-level vector search, Tree, Graph and full context (course code), plus Graph v2 (Homework 5, Advanced).

Everything above the \"Graph v2\" banner is the course code from the Lecture 05 preparation branch. Graph v2 is added below it.
"""

import argparse
import json
import math
import re
import sqlite3
from contextlib import contextmanager
from collections import defaultdict, deque
from pathlib import Path

from google import genai
from google.genai import types
from pydantic_ai.exceptions import ModelHTTPError
import sqlite_vec

from app.config import (
    EMBEDDING_DIMENSIONS, EMBEDDING_MAX_TOKENS, EMBEDDING_MODEL,
    RAG_DB, RAG_DOCUMENT_IDS, RAG_SOURCE, RAG_TOP_K, RAG_TREE, get_api_key,
    RAG_GRAPH, GRAPH_START_K, GRAPH_HOPS, GRAPH_MAX_RESULTS,
    GRAPH2_START_K, GRAPH2_HOPS, GRAPH2_FULL, GRAPH2_PREVIEWS,
)


def get_all_materials() -> str:
    """Combine all materials into one string with lecture, section, and page metadata."""
    documents = json.loads(RAG_SOURCE.read_text(encoding="utf-8"))
    return "\n\n".join(
        f"Document: {document['id']} / {document['title']}\n"
        f"Section: {section['section']}\n"
        f"Page: PDF p.{page['page']} / {page['title']}\n{page['content']}"
        for document in documents
        for section in document["content"]
        for page in section["content"]
    )

def load_pages(source: Path = RAG_SOURCE) -> list[dict]:
    """Convert document → section → page JSON into a page list for the selected materials."""
    documents = json.loads(source.read_text(encoding="utf-8"))
    pages = []
    for document in documents:
        if document["id"] not in RAG_DOCUMENT_IDS:
            continue
        for section in document["content"]:
            for page in section["content"]:
                pages.append({"page_id": page["id"], "document_id": document["id"],
                              "lecture": int(document["id"][3:5]), "document_title": document["title"],
                              "section": section["section"], "title": page["title"],
                              "page": page["page"], "content": page["content"]})
    return pages


def browse_tree(node_id: str | None = None) -> dict:
    """Return the first sentence for child pages and the full text for the selected page itself."""
    tree = json.loads(RAG_TREE.read_text(encoding="utf-8"))
    tree["children"] = [node for node in tree["children"] if node["id"] in RAG_DOCUMENT_IDS]
    node_id = node_id or tree["id"]
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}

    def describe(node, full=False):
        info = {key: node[key] for key in ("id", "kind", "title")}
        if node["kind"] == "page":
            info.update({key: value for key, value in pages[node["id"]].items() if key != "page_id"})
            if not full:
                info["content"] = re.split(r"(?<=[。！？])|\n", info["content"].strip(), maxsplit=1)[0]
        return info

    remaining = [tree]
    while remaining:
        node = remaining.pop()
        if node["id"] == node_id:
            return {
                "node": describe(node, full=True),
                "children": [describe(child) for child in node.get("children", [])],
            }
        remaining.extend(node.get("children", []))
    raise ValueError("The requested table-of-contents node was not found.")


def read_page(page_id: str) -> dict:
    """Return text and citation metadata for one specified page from the main materials for Lectures 01–03."""
    for page in load_pages(RAG_SOURCE):
        if page["page_id"] == page_id:
            return page
    raise ValueError("The requested page was not found.")


def normalized_vector(values: list[float]) -> list[float]:
    """Normalize the vector to unit length."""
    norm = math.hypot(*values)
    if norm == 0:
        raise ValueError("The embedding is a zero vector.")
    return [value / norm for value in values]


def embed_text(text: str, task_type: str) -> list[float]:
    """Embed text with Gemini. Stop instead of truncating if the input limit is exceeded."""
    with genai.Client(api_key=get_api_key()) as client:
        count = client.models.count_tokens(model=EMBEDDING_MODEL, contents=text).total_tokens
        if count is None or count > EMBEDDING_MAX_TOKENS:
            raise ValueError(f"Embedding input exceeds the limit or could not be measured: {count} tokens.")
        response = client.models.embed_content(
            model=EMBEDDING_MODEL, contents=text,
            config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=EMBEDDING_DIMENSIONS),
        )
    embedding = response.embeddings[0]
    if embedding.statistics and embedding.statistics.truncated:
        raise ValueError("The embedding API truncated the text.")
    return normalized_vector(embedding.values)


@contextmanager
def open_index(path: Path):
    """Open an existing search database read-only and close it on exit."""
    if not path.is_file():
        raise FileNotFoundError("Search database not found.")
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        db.row_factory = sqlite3.Row
        db.enable_load_extension(True)
        sqlite_vec.load(db)
        db.enable_load_extension(False)
        yield db
    finally:
        db.close()


def search(query: str) -> list[dict]:
    """Embed the query and return up to RAG_TOP_K similar pages."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("""
            SELECT page_id, document_id, lecture, document_title, section, title, page, content,
                   vec_distance_cosine(embedding, ?) AS distance
            FROM chunks ORDER BY distance, page_id LIMIT ?
        """, (sqlite_vec.serialize_float32(vector), RAG_TOP_K))
        return [dict(row) for row in rows]


def search_graph(query: str) -> dict:
    """Start with vector search, then expand candidates through adjacent pages and shared terms."""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in graph["nodes"]
             if node["kind"] == "term" or node["id"] in pages}
    adjacent = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            adjacent[a].add(b)
            adjacent[b].add(a)

    seeds = [hit for hit in search(query) if hit["page_id"] in pages][:min(GRAPH_START_K, GRAPH_MAX_RESULTS)]
    seed_ids = {seed["page_id"] for seed in seeds}
    results, candidates = [], {}
    for rank, seed in enumerate(seeds):
        root = seed["page_id"]
        results.append({**pages[root], "distance": seed["distance"], "hops": 0,
                        "path": [{"id": root, "title": pages[root]["title"]}]})
        queue = deque([(root, [root])])
        visited = {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= GRAPH_HOPS:
                continue
            # At the same depth, follow terms with fewer connections first.
            neighbors = sorted(adjacent[current], key=lambda n: (len(adjacent[n]), n))
            for neighbor in neighbors:
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seed_ids:
                    continue
                frequency = max((len(adjacent[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                priority = (len(route) - 1, frequency, rank, neighbor)
                candidate = {**pages[neighbor], "hops": len(route) - 1,
                             "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
                if neighbor not in candidates or priority < candidates[neighbor][0]:
                    candidates[neighbor] = (priority, candidate)
    expanded = [candidate for _, candidate in sorted(candidates.values())]
    return {"seeds": results, "expanded": expanded[:max(0, GRAPH_MAX_RESULTS - len(results))],
            "max_hops": GRAPH_HOPS}



# ---------------------------------------------------------------------------
# Graph v2 (Homework 5, Advanced)
#
# The course Graph returns up to 10 pages of full text. It ranks the pages it adds by (hops, term frequency,
# seed rank, page id), so the query plays no part after the first search, and ties are broken by page id.
# Graph v2 keeps the same entry points, the same edges and the same hop limit, and changes three things:
#   1. the graph only decides which pages are eligible; the query decides their order
#      (one embedding call, cosine distance to every page, the same call the course search makes);
#   2. only the best GRAPH2_FULL eligible pages come back as full text; the next GRAPH2_PREVIEWS come back as
#      title + one line, and the model reads one with read_page when it needs it (Tree's fetch-when-needed idea);
#   3. the one-line preview skips slide headers, so it says something about the page (see preview_line).
# ---------------------------------------------------------------------------

HEADER_LINE = re.compile(r"^(\d+\s*/\s*\d+\s|Part\s*\d+\s|第\s*\d+\s*回)")
SOURCE_PREFIXES = ("出典", "©", "Source", "Sources")


def preview_line(page: dict, limit: int = 90) -> str:
    """Return one informative line of a page: not the title, not a slide section header ("4/4 ...", "Part 6 ..."),
    not a source note and not the copyright line. The course Tree returns the first line, which is often a section header."""
    title = page["title"].strip()
    for line in page["content"].splitlines():
        line = line.strip()
        if not line or line == title or HEADER_LINE.match(line) or line.startswith(SOURCE_PREFIXES):
            continue
        return line if len(line) <= limit else line[:limit] + "…"
    return ""


def page_distances(query: str) -> dict[str, float]:
    """Embed the query once and return the cosine distance from it to every page in the search database."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("The search query is empty.")
    with open_index(RAG_DB) as db:
        vector = embed_text(query.strip(), "RETRIEVAL_QUERY")
        rows = db.execute("SELECT page_id, vec_distance_cosine(embedding, ?) AS distance FROM chunks",
                          (sqlite_vec.serialize_float32(vector),))
        return {row["page_id"]: row["distance"] for row in rows}


def graph_neighbors(pages: dict[str, dict], graph: dict) -> tuple[dict, dict]:
    """Return (neighbors, nodes) for the two edge types the course Graph follows: next_page and mentions."""
    nodes = {node["id"]: node for node in graph["nodes"] if node["kind"] == "term" or node["id"] in pages}
    neighbors = defaultdict(set)
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if edge["relation"] in ("next_page", "mentions") and a in nodes and b in nodes:
            neighbors[a].add(b)
            neighbors[b].add(a)
    return neighbors, nodes


def expand_candidates(seed_ids: list[str], pages: dict[str, dict], graph: dict, hops: int = GRAPH2_HOPS) -> dict[str, dict]:
    """Every page reachable from a seed within `hops` steps (a seed is excluded), with the shortest route found.

    A page next to a seed is 1 hop. A page that shares a term with a seed is 2 hops (page, term, page).
    On a tie the route through the term with fewer connected pages is kept, as in the course Graph."""
    neighbors, nodes = graph_neighbors(pages, graph)
    seeds = set(seed_ids)
    found: dict[str, dict] = {}
    for rank, root in enumerate(seed_ids):
        queue, visited = deque([(root, [root])]), {root}
        while queue:
            current, path = queue.popleft()
            if len(path) - 1 >= hops:
                continue
            for neighbor in sorted(neighbors[current], key=lambda n: (len(neighbors[n]), n)):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                route = path + [neighbor]
                queue.append((neighbor, route))
                if neighbor not in pages or neighbor in seeds:
                    continue
                weight = max((len(neighbors[n]) for n in route if nodes[n]["kind"] == "term"), default=0)
                key = (len(route) - 1, weight, rank)
                if neighbor not in found or key < found[neighbor]["key"]:
                    found[neighbor] = {"key": key, "hops": len(route) - 1,
                                       "path": [{"id": n, "title": nodes[n]["title"]} for n in route]}
    return found


def graph_v2(seed_ids: list[str], distances: dict[str, float], pages: dict[str, dict], graph: dict,
             full: int = GRAPH2_FULL, previews: int = GRAPH2_PREVIEWS, hops: int = GRAPH2_HOPS) -> dict:
    """Graph v2 on given entry points. `distances` maps page id to the distance from the query (smaller is closer).

    Pure function (no files, no API): the tests and the offline evaluation call it directly."""
    found = expand_candidates(seed_ids, pages, graph, hops)
    ranked = sorted(found, key=lambda pid: (distances[pid], found[pid]["hops"], pid))

    def entry(pid: str, hop_count: int, path: list[dict]) -> dict:
        return {"distance": distances[pid], "hops": hop_count, "path": path}

    seeds = [{**pages[pid], **entry(pid, 0, [{"id": pid, "title": pages[pid]["title"]}])} for pid in seed_ids]
    expanded = [{**pages[pid], **entry(pid, found[pid]["hops"], found[pid]["path"])} for pid in ranked[:full]]
    more = []
    for pid in ranked[full:full + previews]:
        page = pages[pid]
        more.append({"page_id": pid, "document_id": page["document_id"], "lecture": page["lecture"],
                     "title": page["title"], "page": page["page"], "preview": preview_line(page),
                     **entry(pid, found[pid]["hops"], found[pid]["path"])})
    return {"seeds": seeds, "expanded": expanded, "more": more, "max_hops": hops,
            "note": "Pages in `more` have no body text. Call read_page(page_id) to read one of them."}


def search_graph_v2(query: str) -> dict:
    """Graph v2 from a query: the top GRAPH2_START_K pages are the entry points (as in the course Graph)."""
    pages = {page["page_id"]: page for page in load_pages(RAG_SOURCE)}
    graph = json.loads(RAG_GRAPH.read_text(encoding="utf-8"))
    distances = {pid: d for pid, d in page_distances(query).items() if pid in pages}
    seeds = sorted(distances, key=lambda pid: (distances[pid], pid))[:GRAPH2_START_K]
    return graph_v2(seeds, distances, pages, graph)



def run_full_context(agent, question: str, model, instructions: str, prompt_template: str):
    """Pass all materials at once and answer without retrieval tools."""
    prompt = prompt_template.format(materials=get_all_materials(), question=question)
    print(f"[full-context] Input: {len(prompt):,} characters")
    try:
        with agent.override(tools=[], instructions=instructions):
            return agent.run_sync(prompt, model=model)
    except ModelHTTPError as e:
        print(f"[full-context] API error HTTP {e.status_code}: {e.body}")
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search the lecture materials without using an agent")
    parser.add_argument("query", help="What to look up")
    args = parser.parse_args()
    for i, result in enumerate(search(args.query), 1):
        print(f"\n{'=' * 60}\nSearch result {i}\n{'=' * 60}")
        print(f"Lecture: {result['document_title']}")
        print(f"Section: {result['section']}")
        print(f"Title: {result['title']}")
        print(f"Page: {result['page']}")
        print(f"\n{result['content']}")
