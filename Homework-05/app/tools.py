"""Lecture 05 tools for the agent, plus the two tools Graph v2 needs (Homework 5, Advanced).

Function docstrings and type hints here become the "tool descriptions" presented to the model.
search_materials, browse_tree and search_graph are the course versions. search_graph_v2 and read_page are new.
The glossary tools of Lecture 03 and the MCP code are not copied: this lecture's agent does not register them.
"""

import json
import sqlite3

from app.config import api_error_message


def search_materials(query: str) -> str:
    """Search the main materials for Lectures 01–03 and return relevant page text, titles, and page numbers.

    Use query to specify what you want to look up.
    """
    from google.genai.errors import APIError
    from app.retrieval import search

    try:
        return json.dumps({"results": search(query)}, ensure_ascii=False)
    except (ValueError, FileNotFoundError, sqlite3.Error) as e:
        return json.dumps({"error": str(e), "results": []}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code), "results": []}, ensure_ascii=False)


def browse_tree(node_id: str | None = None) -> str:
    """Return the table of contents and the first sentence of each page. Specify a page ID to get its full text.

    Omit node_id on the first call. Then follow the table of contents using the returned IDs.
    """
    from app.retrieval import browse_tree as browse

    try:
        return json.dumps(browse(node_id), ensure_ascii=False)
    except (ValueError, OSError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


def search_graph(query: str) -> str:
    """Search the materials, then follow adjacent pages and shared terms to return related page text and citation metadata.

    Use query to specify what you want to look up.
    """
    from google.genai.errors import APIError
    from app.retrieval import search_graph as search

    try:
        return json.dumps(search(query), ensure_ascii=False)
    except (ValueError, OSError, sqlite3.Error) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code)}, ensure_ascii=False)


def search_graph_v2(query: str) -> str:
    """Search the materials, then add related pages found through adjacent pages and shared terms, best match first.

    Returns seeds and expanded (full page text with citation metadata) and more (page_id, title and one line only).
    Use query to specify what you want to look up. To read a page listed in more, call read_page with its page_id.
    """
    from google.genai.errors import APIError
    from app.retrieval import search_graph_v2 as search

    try:
        return json.dumps(search(query), ensure_ascii=False)
    except (ValueError, OSError, sqlite3.Error) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except APIError as e:
        return json.dumps({"error": api_error_message(e.code)}, ensure_ascii=False)


def read_page(page_id: str) -> str:
    """Return the full text and citation metadata of one page, for example read_page("lec02-main-p052").

    Use it for a page_id that search_graph_v2 listed in more and that you need to read.
    """
    from app.retrieval import read_page as read

    try:
        return json.dumps(read(page_id), ensure_ascii=False)
    except (ValueError, OSError) as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
