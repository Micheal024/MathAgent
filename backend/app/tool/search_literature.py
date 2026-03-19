"""T4: SearchLiterature — Academic paper search.

Searches Semantic Scholar API and returns relevant papers.
In production, this would also integrate with a local Vector DB.

PRD §2.7: Input: `query, filters` → Output: `papers[{title, url, score}]`
"""

from __future__ import annotations

import json
from typing import Optional

from loguru import logger


def search_literature(
    query: str,
    max_results: int = 10,
    year_from: int = 0,
    fields_of_study: str = "",
) -> str:
    """Search for academic papers relevant to a math modeling topic.

    Searches Semantic Scholar for papers matching the query.
    Useful for finding references, prior work, and validation data
    for your mathematical models.

    Args:
        query: Search query describing the topic or research question.
        max_results: Maximum number of papers to return (default: 10).
        year_from: Only return papers published after this year (0 for no filter).
        fields_of_study: Comma-separated fields to filter by (e.g., "Mathematics,Computer Science").

    Returns:
        A JSON-formatted list of papers with title, authors, year, citations, and URL.
    """
    logger.info(f"🔍 Searching literature: '{query}' (max={max_results})")

    try:
        import httpx

        params = {
            "query": query,
            "limit": min(max_results, 20),
            "fields": "title,authors,year,citationCount,url,abstract",
        }

        if year_from > 0:
            params["year"] = f"{year_from}-"
        if fields_of_study:
            params["fieldsOfStudy"] = fields_of_study

        with httpx.Client(timeout=15) as client:
            response = client.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        papers = []
        for paper in data.get("data", []):
            authors = ", ".join(
                a.get("name", "") for a in (paper.get("authors") or [])[:3]
            )
            papers.append({
                "title": paper.get("title", ""),
                "authors": authors,
                "year": paper.get("year"),
                "citations": paper.get("citationCount", 0),
                "url": paper.get("url", ""),
                "abstract": (paper.get("abstract") or "")[:200],
            })

        if not papers:
            return f"No papers found for query: '{query}'"

        return json.dumps(papers, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"Literature search error: {e}")
        return f"[error] Search failed: {e}"
