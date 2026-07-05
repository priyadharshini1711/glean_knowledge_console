"""
Entry point — starts the FastAPI web server.

Usage:
    python run.py

The web UI is served at http://localhost:8000
API docs are at   http://localhost:8000/docs

To run the MCP server separately:
    python -m src.mcp_server
"""

import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", 8000))

    print(f"\n  Glean Enterprise Chatbot")
    print(f"  Web UI   ->  http://localhost:{port}")
    print(f"  API docs ->  http://localhost:{port}/docs\n")

    uvicorn.run(
        "src.web_app:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
    )
