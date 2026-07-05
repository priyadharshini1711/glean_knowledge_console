"""
FastAPI web server — serves the UI and exposes REST endpoints for
Indexing, Search, and Chat operations.
"""

import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.indexer import index_documents, load_all_documents, load_all_documents_raw, get_index_status
from src.searcher import search as glean_search
from src.chat import chat as glean_chat

app = FastAPI(
    title="Glean Enterprise Chatbot",
    description="Internal enterprise chatbot powered by Glean APIs",
    version="1.0.0",
)

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"

if FRONTEND_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST_DIR / "assets")), name="assets")
else:
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


# ── Request / Response models ────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query string")
    page_size: int = Field(10, ge=1, le=20, description="Max results to return")


class ChatRequest(BaseModel):
    question: str = Field(..., description="Natural-language question")
    chat_history: Optional[List[dict]] = Field(None, description="Prior conversation turns")


class IndexRequest(BaseModel):
    force: bool = Field(False, description="Force re-index even if already indexed")


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_ui():
    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        index_file = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_file))


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "Glean Enterprise Chatbot"}


@app.get("/api/documents")
async def list_documents():
    """List all local documents available for indexing."""
    docs = load_all_documents_raw()
    return {"count": len(docs), "documents": docs}


@app.post("/api/index")
async def index(request: IndexRequest):
    """Index all local documents into Glean."""
    documents = load_all_documents()
    if not documents:
        raise HTTPException(status_code=400, detail="No documents found in /documents directory.")
    result = await index_documents(documents)
    if result["status"] == "error":
        raise HTTPException(
            status_code=502,
            detail=f"Glean Indexing API error ({result.get('http_status', '?')}): {result.get('message', '')}",
        )
    return result


@app.post("/api/index/status")
async def index_status(doc_ids: List[str]):
    """Check indexing status for specific document IDs."""
    if not doc_ids:
        raise HTTPException(status_code=400, detail="Provide at least one document ID.")
    return await get_index_status(doc_ids)


@app.post("/api/search")
async def search(request: SearchRequest):
    """Search the Glean index."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    result = await glean_search(query=request.query, page_size=request.page_size)
    if result["status"] == "error":
        raise HTTPException(
            status_code=502,
            detail=f"Glean Search API error ({result.get('http_status', '?')}): {result.get('message', '')}",
        )
    return result


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Ask a question and get a grounded answer from Glean Chat."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    result = await glean_chat(
        question=request.question,
        chat_history=request.chat_history,
    )
    if result["status"] == "error":
        raise HTTPException(
            status_code=502,
            detail=f"Glean Chat API error ({result.get('http_status', '?')}): {result.get('message', '')}",
        )
    return result
