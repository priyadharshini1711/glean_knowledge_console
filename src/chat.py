"""
Glean Chat API - generate grounded answers with source citations.
"""

from typing import Any, Dict, List, Optional

from src.glean_client import get_client_api_client
from src.searcher import search


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _build_message(role: str, text: str) -> Dict[str, Any]:
    """Construct a ChatMessage API payload."""
    normalized_role = (role or "USER").upper()
    author = "GLEAN_AI" if normalized_role in ("ASSISTANT", "GLEAN_AI") else "USER"
    return {
        "author": author,
        "messageType": "CONTENT",
        "fragments": [{"text": text}],
    }


def _extract_answer(response: Dict[str, Any]) -> str:
    """Pull plain text from the last assistant message in the response."""
    messages = response.get("messages", []) or []
    for msg in reversed(messages):
        msg_dict = _as_dict(msg)
        author = (msg_dict.get("author") or msg_dict.get("role") or "").upper()
        if author in ("ASSISTANT", "GLEAN_AI"):
            text = msg_dict.get("text")
            if text:
                return text

            parts = []
            for fragment in msg_dict.get("fragments", []) or []:
                fragment_dict = _as_dict(fragment)
                if fragment_dict.get("text"):
                    parts.append(fragment_dict["text"])
            if parts:
                return " ".join(parts)
    return ""


def _citation_document(citation: Dict[str, Any]) -> Dict[str, Any]:
    source_doc = _as_dict(citation.get("sourceDocument"))
    if source_doc:
        return source_doc
    source_file = _as_dict(citation.get("sourceFile"))
    if source_file:
        return source_file
    return _as_dict(citation.get("document"))


def _extract_citations(response: Dict[str, Any]) -> List[Dict]:
    """Pull unique source citations from the assistant response fragments."""
    messages = response.get("messages", []) or []
    citations: List[Dict] = []
    seen: set = set()

    for msg in reversed(messages):
        msg_dict = _as_dict(msg)
        author = (msg_dict.get("author") or msg_dict.get("role") or "").upper()
        if author not in ("ASSISTANT", "GLEAN_AI"):
            continue

        for fragment in msg_dict.get("fragments", []) or []:
            fragment_dict = _as_dict(fragment)
            citation = _as_dict(fragment_dict.get("citation"))

            if not citation and (fragment_dict.get("type") or "").upper() == "DOCUMENT_CITATION":
                citation = {"document": fragment_dict.get("document")}

            doc = _citation_document(citation)
            if not doc:
                continue

            doc_id = doc.get("id") or doc.get("url") or doc.get("name") or doc.get("title")
            if not doc_id or doc_id in seen:
                continue
            seen.add(doc_id)
            citations.append({
                "title": doc.get("title") or doc.get("name") or "Unknown",
                "url": doc.get("url") or doc.get("webUrl") or "",
                "doc_id": doc.get("id") or "",
                "datasource": doc.get("datasource") or "",
            })
        break

    return citations


def _error_response(exc: Exception) -> Dict[str, Any]:
    response = getattr(exc, "response", None)
    return {
        "status": "error",
        "message": response.text if response is not None else str(exc),
        "http_status": getattr(response, "status_code", None),
        "answer": "",
        "citations": [],
    }


async def chat(
    question: str,
    chat_history: Optional[List[Dict]] = None,
    save_chat: bool = False,
) -> Dict:
    """
    Send a question to the Glean Chat API and return a grounded answer.

    Args:
        question: The natural-language user question.
        chat_history: Optional prior messages for multi-turn conversation.
                      Each item: {"role": "USER"|"ASSISTANT", "content": "..."}
        save_chat: Whether to persist the chat session in Glean.
    """

    #search the document before taking up the chat API, if the search result is not empty, then we can use the chat API to get the answer
    search_result = await search(query=question, page_size=5)

    if search_result["status"] == "error":
        return {
            "status": "error",
            "message": f"Search failed (HTTP {search_result.get('http_status', '?')}): {search_result.get('message', 'Unknown error')}",
            "http_status": search_result.get("http_status", None),
            "answer": "",
            "citations": [],
        }
    else:
        if search_result["total_results"] == 0:
            return {
                "status": "error",
                "message": "No relevant documents found for the question.",
                "http_status": None,
                "answer": "",
                "citations": [],
            }
        
    
    messages: List[Dict[str, Any]] = []

    if chat_history:
        for turn in chat_history:
            messages.append(_build_message(turn.get("role", "USER"), turn.get("content", "")))

    messages.append(_build_message("USER", question))

    try:
        async with get_client_api_client() as client:
            response = await client.post(
                "chat",
                json={
                    "messages": messages,
                    "saveChat": save_chat,
                },
            )
            response.raise_for_status()
            data = response.json()

        return {
            "status": "success",
            "question": question,
            "answer": _extract_answer(data),
            "citations": _extract_citations(data),
            "chat_id": data.get("chatId", ""),
        }
    except Exception as exc:
        return _error_response(exc)
