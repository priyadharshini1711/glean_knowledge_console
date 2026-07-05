# Glean Knowledge Console

An end-to-end sandbox app that indexes local documents into Glean, searches the Glean index, answers grounded questions with Glean Chat, and exposes the same chatbot through a local MCP server for GitHub Copilot in VS Code.

## What It Includes

- React + Vite frontend with Chat, Search, and Index views
- FastAPI backend with REST endpoints for indexing, search, chat, and status checks
- Direct Glean API integration through `httpx`
- TXT and PDF indexing support
- Local stdio MCP server with two tools:
  - `glean_search`
  - `glean_chat`
- Workspace MCP config for GitHub Copilot: `.vscode/mcp.json`

## Architecture

```text
React UI
  Chat | Search | Index
        |
        v
FastAPI backend
  /api/index
  /api/index/status
  /api/search
  /api/chat
        |
        v
Glean APIs
  Indexing API
  Search API
  Chat API

MCP-compatible client
  GitHub Copilot in VS Code
        |
        v
src/mcp_server.py
  glean_search
  glean_chat
```

## Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

Create or update `.env` in the project root:

```env
GLEAN_COMPANY=aws-sasandbox-be
GLEAN_DATASOURCE=interviewds
GLEAN_INDEXING_TOKEN=<indexing-token>
GLEAN_CLIENT_TOKEN=<client-token>
GLEAN_DOCUMENT_BASE_URL=https://www.example.com/docs
```

`GLEAN_DOCUMENT_BASE_URL` must match the URL regex configured on the Glean datasource. For the current sandbox error pattern, `https://www.example.com/docs` is valid.

## Run The App

Build the React frontend:

```bash
cd frontend
npm run build
cd ..
```

Start the FastAPI app:

```bash
python run.py
```

Open:

```text
http://127.0.0.1:8000
```

During active frontend development, you can run Vite separately:

```bash
cd frontend
npm run dev
```

The Vite dev server proxies `/api/*` to the FastAPI backend.

## Documents

Documents are loaded from the `documents/` folder.

Supported file types:

| Type | Glean payload |
|------|---------------|
| `.txt` | `mimeType: text/plain`, `textContent` |
| `.pdf` | `mimeType: application/pdf`, base64 `binaryContent` |

Current indexed examples include:

| File | Notes |
|------|-------|
| `1706.03762v7.pdf` | PDF paper indexed as binary PDF content |
| `engineering_handbook_glean_app.txt` | Engineering practices |
| `hr_policy.txt` | HR policy and benefits |
| `onboarding_guide.txt` | New employee onboarding |
| `product_roadmap.txt` | FY2026 roadmap |

## Usage

### Index Documents

In the UI, open the Index view and click `Index all`.

This calls:

```http
POST /api/index
```

Glean indexing is asynchronous, so allow a short delay before search/chat results appear.

### Check Indexing Status

Use:

```http
POST /api/index/status
```

Example body:

```json
[
  "1706.03762v7",
  "engineering-handbook-001",
  "hr-policy-001",
  "onboarding-001",
  "product-roadmap-001"
]
```

### Search

In the UI, open the Search view and run a query, or call:

```http
POST /api/search
```

Example body:

```json
{
  "query": "engineering handbook rules",
  "page_size": 10
}
```

### Chat

In the UI, open the Chat view and ask a grounded question, or call:

```http
POST /api/chat
```

Example body:

```json
{
  "question": "What are the FY2026 product roadmap milestones?"
}
```

## Useful Chat Questions

- What are the main Git workflow rules?
- What is the expected process for code reviews?
- What does the engineering handbook say about CI/CD?
- What are the key leave and benefits policies?
- What is the remote work policy?
- What should a new employee complete during week one?
- Which systems and contacts are mentioned in onboarding?
- What are the major FY2026 product roadmap milestones?
- What KPIs are listed in the roadmap?
- What is the main topic and contribution of the PDF paper?

## MCP Server

The MCP server is implemented in:

```text
src/mcp_server.py
```

It exposes two tools over stdio:

| Tool | Description |
|------|-------------|
| `glean_search` | Accepts `query` and optional `page_size`; returns top documents with metadata |
| `glean_chat` | Accepts `question` and optional `chat_history`; returns a grounded answer and sources |

Run it manually:

```bash
python -m src.mcp_server
```

### GitHub Copilot In VS Code

This repo includes workspace MCP config:

```text
.vscode/mcp.json
```

Config:

```json
{
  "servers": {
    "glean": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

To use it:

1. Open this repository folder in VS Code.
2. Ensure GitHub Copilot Chat is enabled.
3. Open Copilot Chat in Agent mode.
4. Allow or enable the workspace MCP server if VS Code prompts you.
5. Ask Copilot to use the Glean tools.

Example prompts:

```text
Use glean_search to find engineering handbook rules.
```

```text
Use glean_chat to answer: What are the FY2026 product roadmap milestones?
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/documents` | List local documents |
| `POST` | `/api/index` | Index all local documents into Glean |
| `POST` | `/api/index/status` | Check indexing status by document ID |
| `POST` | `/api/search` | Search the Glean index |
| `POST` | `/api/chat` | Ask a grounded chat question |
| `GET` | `/docs` | FastAPI OpenAPI docs |

## Technical Notes

- The app uses direct Glean REST APIs, not the Glean Python SDK.
- Indexing uses the Glean Indexing API under `/api/index/v1`.
- Search and Chat use the Glean client REST API under `/rest/api/v1`.
- Indexing and client tokens are intentionally separate.
- The MCP server writes only JSON-RPC messages to stdout. Diagnostic output is sent to stderr so MCP clients can parse responses correctly.
- On Windows, the MCP stdio loop uses simple blocking line reads for reliable local client compatibility.

## Verification

Backend tests:

```bash
python -m pytest -q
```

Frontend production build:

```bash
cd frontend
npm run build
```
