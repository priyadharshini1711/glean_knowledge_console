"""
Glean MCP Server — raw JSON-RPC 2.0 over stdio, MCP 2024-11-05 spec.
Compatible with Python 3.9+. No external MCP SDK required.

Run with:
    python -m src.mcp_server

Add to Cursor (~/.cursor/mcp.json) or Claude Desktop config:
    {
      "mcpServers": {
        "glean": {
          "command": "python",
          "args": ["-m", "src.mcp_server"],
          "cwd": "/path/to/glean-app"
        }
      }
    }

Tools exposed:
    glean_search  — search the Glean index
    glean_chat    — ask a question, get a grounded answer with sources
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.searcher import search as glean_search
from src.chat import chat as glean_chat


# ── MCP protocol helpers ──────────────────────────────────────────────────────

def _ok(id_: Any, result: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": id_, "result": result})


def _err(id_: Any, code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})


def _notify(method: str, params: Any) -> str:
    return json.dumps({"jsonrpc": "2.0", "method": method, "params": params})


TOOLS = [
    {
        "name": "glean_search",
        "description": (
            "Search the Glean knowledge base for documents matching a query. "
            "Returns the top N results with titles, snippets, URLs, and metadata."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query (natural language or keywords).",
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of results to return (1–20). Default: 10.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "glean_chat",
        "description": (
            "Ask a natural-language question and get a grounded answer from Glean. "
            "The response includes the answer text and source document citations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to answer.",
                },
                "chat_history": {
                    "type": "array",
                    "description": (
                        "Optional prior conversation turns. "
                        "Each item: {\"role\": \"USER\"|\"ASSISTANT\", \"content\": \"...\"}."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["role", "content"],
                    },
                },
            },
            "required": ["question"],
        },
    },
]


# ── Tool execution ────────────────────────────────────────────────────────────

async def _call_search(args: Dict) -> str:
    query = args.get("query", "")
    page_size = int(args.get("page_size", 10))
    result = await glean_search(query=query, page_size=page_size)

    if result["status"] == "error":
        return f"Search failed (HTTP {result.get('http_status', '?')}): {result.get('message', 'Unknown error')}"

    lines = [
        f'Search results for: "{query}"',
        f"Found {result['total_results']} result(s)\n",
    ]
    for i, doc in enumerate(result["results"], 1):
        lines.append(f"{i}. {doc['title']}")
        if doc["snippet"]:
            lines.append(f"   Snippet: {doc['snippet'][:300]}")
        if doc["url"]:
            lines.append(f"   URL: {doc['url']}")
        if doc["author"]:
            lines.append(f"   Author: {doc['author']}")
        lines.append("")
    return "\n".join(lines)


async def _call_chat(args: Dict) -> str:
    question = args.get("question", "")
    chat_history = args.get("chat_history")
    result = await glean_chat(question=question, chat_history=chat_history)

    if result["status"] == "error":
        return f"Chat failed (HTTP {result.get('http_status', '?')}): {result.get('message', 'Unknown error')}"

    lines = [f"Answer:\n{result['answer']}"]
    if result["citations"]:
        lines.append("\nSources:")
        for i, c in enumerate(result["citations"], 1):
            lines.append(f"  {i}. {c['title']}")
            if c["url"]:
                lines.append(f"     {c['url']}")
    return "\n".join(lines)


# ── Request handler ───────────────────────────────────────────────────────────

async def handle(request: Dict) -> Optional[str]:
    method = request.get("method", "")
    id_ = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return _ok(id_, {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "glean-enterprise-chatbot", "version": "1.0.0"},
            "capabilities": {"tools": {}},
        })

    if method == "notifications/initialized":
        return None  # notification — no response

    if method == "tools/list":
        return _ok(id_, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            if tool_name == "glean_search":
                text = await _call_search(args)
            elif tool_name == "glean_chat":
                text = await _call_chat(args)
            else:
                return _err(id_, -32601, f"Unknown tool: {tool_name}")

            return _ok(id_, {
                "content": [{"type": "text", "text": text}],
                "isError": False,
            })
        except Exception as exc:
            return _ok(id_, {
                "content": [{"type": "text", "text": f"Error: {exc}"}],
                "isError": True,
            })

    if id_ is not None:
        return _err(id_, -32601, f"Method not found: {method}")
    return None


# ── Main stdio loop ───────────────────────────────────────────────────────────

async def main():
    while True:
        try:
            line = sys.stdin.buffer.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = await handle(request)
            if response is not None:
                print(response, flush=True)
        except json.JSONDecodeError:
            pass
        except Exception as exc:
            print(_err(None, -32603, str(exc)), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
