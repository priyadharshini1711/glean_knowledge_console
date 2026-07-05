"""
Glean Search API - query the Glean index and return structured results.
"""

from typing import Any, Dict, List, Optional

from src.glean_client import get_client_api_client, DATASOURCE


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _format_result(result: Any) -> Dict[str, Any]:
    """Normalize a Glean SearchResult JSON object into a clean dict."""
    result_dict = _as_dict(result)
    doc = _as_dict(result_dict.get("document"))
    snippets = result_dict.get("snippets") or []

    title = doc.get("title") or result_dict.get("title") or "Untitled"
    url = doc.get("url") or result_dict.get("url") or ""
    datasource = doc.get("datasource", "")
    doc_id = doc.get("id", "")

    snippet = ""
    if snippets:
        first = snippets[0] if isinstance(snippets[0], dict) else {}
        snippet = first.get("text", "") or first.get("snippet", "")

    metadata = _as_dict(doc.get("metadata"))
    author_obj = _as_dict(metadata.get("author"))
    author = author_obj.get("name") or author_obj.get("email") or ""

    return {
        "title": title,
        "url": url,
        "datasource": datasource,
        "doc_id": doc_id,
        "snippet": snippet,
        "author": author,
    }


def _error_response(exc: Exception) -> Dict[str, Any]:
    response = getattr(exc, "response", None)
    return {
        "status": "error",
        "message": response.text if response is not None else str(exc),
        "http_status": getattr(response, "status_code", None),
        "results": [],
    }


async def search(query: str, page_size: int = 10, datasource_filter: Optional[str] = None) -> Dict:
    """
    Search Glean for the given query using the REST API.

    Args:
        query: Natural language or keyword search query.
        page_size: Max number of results to return (1-20).
        datasource_filter: Optionally restrict results to a specific datasource.
    """
    page_size = max(1, min(page_size, 20))
    payload: Dict[str, Any] = {
        "query": query,
        "pageSize": page_size,
        "requestOptions": {
            "datasourceFilter": datasource_filter or DATASOURCE,
        },
    }

    try:
        async with get_client_api_client() as client:
            response = await client.post("search", json=payload)
            response.raise_for_status()
            data = response.json()

        raw_results = data.get("results", []) or []
        formatted: List[Dict] = [_format_result(r) for r in raw_results]

        return {
            "status": "success",
            "query": query,
            "total_results": len(formatted),
            "results": formatted,
        }
    except Exception as exc:
        return _error_response(exc)
