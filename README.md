# Glean Enterprise Chatbot

An end-to-end prototype that indexes internal documents into Glean, verifies searchability, and answers employee questions through a grounded AI chat interface — exposed via both a web UI and an MCP server.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Web Browser (UI)                    │
│          Chat · Search · Index tabs                     │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────────┐
│              FastAPI Web Server (run.py)                 │
│  POST /api/index   POST /api/search   POST /api/chat    │
└────┬───────────────┬────────────────────┬───────────────┘
     │               │                    │
┌────▼────┐   ┌──────▼──────┐   ┌────────▼────────┐
│ Indexer │   │   Searcher  │   │   Chat Client   │
│indexer.py│  │ searcher.py │   │    chat.py      │
└────┬────┘   └──────┬──────┘   └────────┬────────┘
     │               │                    │
     └───────────────┼────────────────────┘
                     │ HTTPS
          ┌──────────▼──────────┐
          │   Glean APIs        │
          │  Indexing API       │
          │  Search API         │
          │  Chat API           │
          └─────────────────────┘

┌─────────────────────────────────┐
│   MCP Server (mcp_server.py)    │  ← stdio, for Cursor / Claude Desktop
│   Tools: glean_search           │
│          glean_chat             │
└─────────────────────────────────┘
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

The `.env` file is pre-filled with sandbox credentials:

```
GLEAN_COMPANY=sasandbox
GLEAN_DATASOURCE=interviewds
GLEAN_INDEXING_TOKEN=<token>
GLEAN_CLIENT_TOKEN=<token>
```

### 3. Run the web app

```bash
python run.py
```

Open **http://localhost:8000** in your browser.

---

## Usage

### Step 1 — Index documents

Go to the **Index** tab → click **Index all documents**.

This calls `POST /api/index` which pushes the four documents in `/documents` to Glean via the Indexing API (`/api/index/v1/indexdocuments`).

> Note: Glean indexes asynchronously. Allow 1–2 minutes before documents appear in search results.

### Step 2 — Verify searchability

Go to the **Search** tab → type a query like `"leave policy"` or `"onboarding checklist"`.

This calls `POST /api/search` which queries the Glean index and returns top-N results with titles, snippets, and metadata.

### Step 3 — Chat

Go to the **Chat** tab → ask a question like:

- *"How many days of annual leave do employees get?"*
- *"What is the parental leave policy?"*
- *"What are the Q3 product milestones?"*
- *"How do I set up my laptop on Day 1?"*

This calls `POST /api/chat` which invokes the Glean Chat API and returns a grounded answer with clickable source citations.

---

## MCP Server

The MCP server exposes **two tools** over stdio, compatible with Cursor, Claude Desktop, and any MCP client.

### Run the MCP server

```bash
python -m src.mcp_server
```

### Tools

| Tool | Description |
|------|-------------|
| `glean_search` | Search the Glean index. Params: `query` (required), `page_size` (optional, 1–20) |
| `glean_chat` | Ask a question and get a grounded answer with sources. Params: `question` (required), `chat_history` (optional) |

### Cursor integration

Copy `mcp_config.json` content into `~/.cursor/mcp.json` (or your MCP client config):

```json
{
  "mcpServers": {
    "glean": {
      "command": "python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/glean-app"
    }
  }
}
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/documents` | List local documents |
| POST | `/api/index` | Index all documents into Glean |
| POST | `/api/search` | Search the Glean index |
| POST | `/api/chat` | Chat with grounded answers |
| GET | `/docs` | Interactive OpenAPI docs |

---

## Documents

Four internal documents are pre-loaded in `/documents`:

| File | Content |
|------|---------|
| `hr_policy.txt` | Leave, benefits, payroll, remote work policy |
| `onboarding_guide.txt` | First-week checklist, systems, contacts |
| `product_roadmap.txt` | FY2026 roadmap with milestones and KPIs |
| `engineering_handbook.txt` | Git workflow, CI/CD, code standards, on-call |

---

## Technical Decisions

**Python + FastAPI** — async-native, clean OpenAPI docs auto-generated, minimal boilerplate.

**MCP via stdio** — the simplest transport for local MCP clients; no port management needed.

**Separate Indexing vs. Client tokens** — Glean uses distinct tokens for write (Indexing API) and read (Search/Chat APIs). The code keeps them separate and never mixes them.

**`isFirstPage: true, isLastPage: true`** in the indexing payload — tells Glean this is a complete, self-contained batch. For large doc sets you'd stream batches with checkpoint flags.

**`allowAllDatasourceUsersAccess: true`** on each document — appropriate for a sandbox demo where all users should see all docs. Production would use `allowedUsers`/`allowedGroups`.

**Chat history** is maintained client-side (in browser memory) and sent with each request. Glean's Chat API supports multi-turn via the `messages` array — no session state needed server-side.

**Failure modes:**
- Indexing is asynchronous — the API returns 202 immediately; documents become searchable after Glean's processing pipeline completes (typically seconds to minutes).
- Rate limits: back off with exponential retry for 429 responses (not implemented in the prototype for simplicity).
- If Chat returns no answer, it likely means no indexed documents match the question's context.
# glean_knowledge_console
