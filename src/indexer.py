"""
Glean Indexing API - bulk-indexes documents from the /documents directory.
"""

import time
import base64
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.glean_client import get_indexing_client, DATASOURCE, DOCUMENT_BASE_URL

DOCUMENTS_DIR = Path(__file__).parent.parent / "documents"
SUPPORTED_DOCUMENT_SUFFIXES = {".txt", ".pdf"}


def _document_id(filepath: Path) -> str:
    return filepath.stem


def _document_title(filepath: Path) -> str:
    return filepath.stem.replace("_", " ").replace("-", " ").title()


def _base_document_payload(filepath: Path, doc_id: str, title: str) -> Dict[str, Any]:
    return {
        "id": doc_id,
        "datasource": DATASOURCE,
        "title": title,
        "objectType": "Document",
        "viewURL": f"{DOCUMENT_BASE_URL.rstrip('/')}/{doc_id}",
        "author": {
            "name": "Glean Software Architecture Team",
            "email": "internal@company.internal",
        },
        "updatedAt": int(time.time()),
        "permissions": {
            "allowAnonymousAccess": True,
            "allowAllDatasourceUsersAccess": True,
        },
    }


def _parse_text_file(filepath: Path) -> Dict[str, Any]:
    """Read a .txt file and return a Glean document definition payload."""
    text = filepath.read_text(encoding="utf-8")

    title = _document_title(filepath)
    doc_id = _document_id(filepath)

    for line in text.splitlines()[:5]:
        if line.startswith("TITLE:"):
            title = line.replace("TITLE:", "").strip()
        if line.startswith("DOCUMENT ID:"):
            doc_id = line.replace("DOCUMENT ID:", "").strip()

    payload = _base_document_payload(filepath, doc_id, title)
    payload["body"] = {
        "mimeType": "text/plain",
        "textContent": text,
    }
    return payload


def _parse_pdf_file(filepath: Path) -> Dict[str, Any]:
    """Read a .pdf file and return a Glean document definition payload."""
    doc_id = _document_id(filepath)
    title = _document_title(filepath)

    payload = _base_document_payload(filepath, doc_id, title)
    payload["body"] = {
        "mimeType": "application/pdf",
        "binaryContent": base64.b64encode(filepath.read_bytes()).decode("ascii"),
    }
    return payload


def _parse_document_file(filepath: Path) -> Dict[str, Any]:
    suffix = filepath.suffix.lower()
    if suffix == ".txt":
        return _parse_text_file(filepath)
    if suffix == ".pdf":
        return _parse_pdf_file(filepath)
    raise ValueError(f"Unsupported document type: {filepath.name}")


def _local_document_files() -> List[Path]:
    return sorted(
        (
            path
            for path in DOCUMENTS_DIR.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_DOCUMENT_SUFFIXES
        ),
        key=lambda path: path.name.lower(),
    )


def _raw_document_info(filepath: Path) -> Dict[str, Any]:
    title = _document_title(filepath)
    doc_id = _document_id(filepath)

    if filepath.suffix.lower() == ".txt":
        for line in filepath.read_text(encoding="utf-8").splitlines()[:5]:
            if line.startswith("TITLE:"):
                title = line.replace("TITLE:", "").strip()
            if line.startswith("DOCUMENT ID:"):
                doc_id = line.replace("DOCUMENT ID:", "").strip()

    return {
        "id": doc_id,
        "title": title,
        "url": f"{DOCUMENT_BASE_URL.rstrip('/')}/{doc_id}",
        "type": filepath.suffix.lower().lstrip("."),
    }




def load_all_documents() -> List[Dict[str, Any]]:
    """Load all TXT and PDF files from /documents and return document payloads."""
    return [_parse_document_file(f) for f in _local_document_files()]



def load_all_documents_raw() -> List[Dict[str, Any]]:
    """Return lightweight dicts for the /api/documents listing endpoint."""
    return [_raw_document_info(f) for f in _local_document_files()]


def _document_value(document: Any, *names: str, default: Any = "") -> Any:
    for name in names:
        if isinstance(document, dict) and name in document:
            return document[name]
        if hasattr(document, name):
            return getattr(document, name)
    return default


def _document_payload(document: Any) -> Dict[str, Any]:
    """Normalize dict or SDK-like document objects into API JSON."""
    if isinstance(document, dict):
        return document
    if hasattr(document, "model_dump"):
        return document.model_dump(by_alias=True, exclude_none=True)
    if hasattr(document, "dict"):
        return document.dict(by_alias=True, exclude_none=True)
    return {
        "id": _document_value(document, "id"),
        "datasource": _document_value(document, "datasource", default=DATASOURCE),
        "title": _document_value(document, "title"),
    }


def _error_response(exc: Exception, attempted: Optional[int] = None) -> Dict[str, Any]:
    response = getattr(exc, "response", None)
    message = str(exc)
    if response is not None:
        message = response.text or message
    if "connect" in exc.__class__.__name__.lower():
        message = f"Connection error while calling Glean: {message}"

    result: Dict[str, Any] = {
        "status": "error",
        "message": message,
        "http_status": getattr(response, "status_code", None),
    }
    if attempted is not None:
        result["attempted"] = attempted
    return result


async def index_documents(documents: Optional[List[Dict[str, Any]]] = None) -> Dict:
    """
    Push documents to Glean via the Indexing API.
    Returns a summary dict with success/failure details.
    """
    if documents is None:
        documents = load_all_documents()

    if not documents:
        return {"status": "error", "message": "No documents found to index."}

    payload_documents = [_document_payload(d) for d in documents]

    try:
        async with get_indexing_client() as client:
            response = await client.post(
                "indexdocuments",
                json={
                    "datasource": DATASOURCE,
                    "documents": payload_documents,
                },
            )
            response.raise_for_status()
        return {
            "status": "success",
            "indexed": len(payload_documents),
            "document_ids": [_document_value(d, "id") for d in payload_documents],
            "titles": [_document_value(d, "title") for d in payload_documents],
        }
    except Exception as exc:
        return _error_response(exc, attempted=len(payload_documents))


async def get_index_status(doc_ids: List[str]) -> Dict:
    """Check the indexing status of specific documents."""
    results = {}
    try:
        async with get_indexing_client() as client:
            for doc_id in doc_ids:
                try:
                    resp = await client.post(
                        "getdocumentstatus",
                        json={
                            "datasource": DATASOURCE,
                            "objectType": "Document",
                            "docId": doc_id,
                        },
                    )
                    resp.raise_for_status()
                    results[doc_id] = resp.json()
                except Exception as exc:
                    results[doc_id] = _error_response(exc)
    except Exception as exc:
        return {"error": str(exc)}
    return results
