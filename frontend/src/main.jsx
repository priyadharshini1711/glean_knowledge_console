import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const TABS = [
  { id: "chat", label: "Chat", icon: "message" },
  { id: "search", label: "Search", icon: "search" },
  { id: "index", label: "Index", icon: "file" },
];

const STARTER_QUESTIONS = [
  "What are the main Git workflow rules?",
  "What should a new employee complete during week one?",
  "What are the FY2026 product milestones?",
  "What is the main contribution of the PDF paper?",
];

function Icon({ name, size = 18 }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round",
    strokeLinejoin: "round",
    "aria-hidden": "true",
  };

  const paths = {
    message: (
      <>
        <path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4z" />
      </>
    ),
    search: (
      <>
        <circle cx="11" cy="11" r="7" />
        <path d="m20 20-3.5-3.5" />
      </>
    ),
    file: (
      <>
        <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7z" />
        <path d="M14 2v5h5" />
      </>
    ),
    send: (
      <>
        <path d="m22 2-7 20-4-9-9-4z" />
        <path d="M22 2 11 13" />
      </>
    ),
    refresh: (
      <>
        <path d="M21 12a9 9 0 0 1-15.4 6.4L3 16" />
        <path d="M3 21v-5h5" />
        <path d="M3 12A9 9 0 0 1 18.4 5.6L21 8" />
        <path d="M21 3v5h-5" />
      </>
    ),
    database: (
      <>
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
        <path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
      </>
    ),
    link: (
      <>
        <path d="M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1" />
        <path d="M14 11a5 5 0 0 0-7.1 0l-2 2A5 5 0 0 0 12 20.1l1.1-1.1" />
      </>
    ),
    x: (
      <>
        <path d="M18 6 6 18" />
        <path d="m6 6 12 12" />
      </>
    ),
  };

  return <svg {...common}>{paths[name]}</svg>;
}

async function apiGet(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorBody.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function Shell() {
  const [activeTab, setActiveTab] = useState("chat");
  const [health, setHealth] = useState("checking");

  useEffect(() => {
    let cancelled = false;
    apiGet("/api/health")
      .then(() => !cancelled && setHealth("online"))
      .catch(() => !cancelled && setHealth("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">G</div>
          <div>
            <div className="brand-name">Glean Console</div>
            <div className="brand-sub">Sandbox knowledge</div>
          </div>
        </div>

        <nav className="nav" aria-label="Primary">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              className={`nav-item ${activeTab === tab.id ? "active" : ""}`}
              onClick={() => setActiveTab(tab.id)}
              type="button"
            >
              <Icon name={tab.icon} />
              <span>{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <span className={`status-light ${health}`} />
          <span>{health === "online" ? "API online" : health === "offline" ? "API offline" : "Checking API"}</span>
        </div>
      </aside>

      <main className="workspace">
        {activeTab === "chat" && <ChatView />}
        {activeTab === "search" && <SearchView />}
        {activeTab === "index" && <IndexView />}
      </main>
    </div>
  );
}

function ViewHeader({ eyebrow, title, action }) {
  return (
    <header className="view-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
      </div>
      {action}
    </header>
  );
}

function ChatView() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Ask me about indexed policies, onboarding, engineering practices, roadmap details, or the PDF paper.",
      citations: [],
    },
  ]);
  const [history, setHistory] = useState([]);
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function sendChat(text = question) {
    const clean = text.trim();
    if (!clean || loading) return;

    setQuestion("");
    setLoading(true);
    setMessages((current) => [...current, { role: "user", content: clean }, { role: "assistant", loading: true }]);

    try {
      const data = await apiPost("/api/chat", { question: clean, chat_history: history });
      const answer = data.answer || "No answer returned.";
      setMessages((current) => [
        ...current.slice(0, -1),
        { role: "assistant", content: answer, citations: data.citations || [] },
      ]);
      setHistory((current) => [
        ...current,
        { role: "USER", content: clean },
        { role: "ASSISTANT", content: answer },
      ]);
    } catch (error) {
      setMessages((current) => [...current.slice(0, -1), { role: "assistant", content: `Error: ${error.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  function clearChat() {
    setHistory([]);
    setMessages([{ role: "assistant", content: "Conversation cleared. Ask a fresh question.", citations: [] }]);
  }

  return (
    <section className="view chat-view">
      <ViewHeader
        eyebrow="Glean Chat"
        title="Knowledge assistant"
        action={
          <button className="ghost-button" onClick={clearChat} type="button">
            <Icon name="x" size={16} />
            Clear
          </button>
        }
      />

      <div className="chat-layout">
        <div className="conversation" ref={scrollRef}>
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
        </div>

        <div className="question-strip">
          {STARTER_QUESTIONS.map((item) => (
            <button key={item} type="button" onClick={() => sendChat(item)} disabled={loading}>
              {item}
            </button>
          ))}
        </div>

        <form
          className="composer"
          onSubmit={(event) => {
            event.preventDefault();
            sendChat();
          }}
        >
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                sendChat();
              }
            }}
            placeholder="Ask a question"
            maxLength={2000}
            rows={1}
          />
          <button className="icon-button primary" disabled={!question.trim() || loading} type="submit" title="Send">
            <Icon name="send" />
          </button>
        </form>
      </div>
    </section>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <article className={`message-row ${isUser ? "from-user" : "from-assistant"}`}>
      <div className="avatar">{isUser ? "U" : "G"}</div>
      <div className="message-card">
        {message.loading ? <LoadingDots /> : <p>{message.content}</p>}
        {!message.loading && message.citations?.length > 0 && (
          <div className="sources">
            {message.citations.map((citation, index) => (
              <a key={`${citation.url}-${index}`} href={citation.url || "#"} target="_blank" rel="noreferrer">
                <span>{index + 1}</span>
                {citation.title || "Source"}
              </a>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}

function LoadingDots() {
  return (
    <div className="loading-dots" aria-label="Loading">
      <span />
      <span />
      <span />
    </div>
  );
}

function SearchView() {
  const [query, setQuery] = useState("");
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  async function runSearch(event) {
    event?.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await apiPost("/api/search", { query, page_size: Number(pageSize) }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="view">
      <ViewHeader eyebrow="Glean Search" title="Document search" />

      <form className="search-bar" onSubmit={runSearch}>
        <div className="search-input-wrap">
          <Icon name="search" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search indexed documents" />
        </div>
        <select value={pageSize} onChange={(event) => setPageSize(event.target.value)}>
          <option value="5">5 results</option>
          <option value="10">10 results</option>
          <option value="20">20 results</option>
        </select>
        <button className="solid-button" disabled={!query.trim() || loading} type="submit">
          {loading ? "Searching" : "Search"}
        </button>
      </form>

      <div className="content-scroll">
        {error && <Notice tone="error" title="Search failed" body={error} />}
        {loading && <RowsLoading label="Searching Glean" />}
        {result && <SearchResults data={result} />}
        {!result && !loading && !error && <EmptyState title="No search yet" body="Run a query to inspect matching documents and metadata." />}
      </div>
    </section>
  );
}

function SearchResults({ data }) {
  const results = data.results || [];
  if (results.length === 0) {
    return <EmptyState title="No results" body={`No matches for "${data.query}".`} />;
  }

  return (
    <div className="results-list">
      <div className="result-count">
        {results.length} result{results.length === 1 ? "" : "s"} for "{data.query}"
      </div>
      {results.map((item, index) => (
        <article className="result-item" key={`${item.doc_id}-${index}`}>
          <div className="result-main">
            <a href={item.url || "#"} target="_blank" rel="noreferrer">
              {item.title || "Untitled"}
            </a>
            {item.snippet && <p>{item.snippet}</p>}
          </div>
          <div className="metadata-row">
            {item.datasource && <span>{item.datasource}</span>}
            {item.author && <span>{item.author}</span>}
            {item.doc_id && <code>{item.doc_id}</code>}
          </div>
        </article>
      ))}
    </div>
  );
}

function IndexView() {
  const [documents, setDocuments] = useState([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [indexing, setIndexing] = useState(false);
  const [checking, setChecking] = useState(false);
  const [notice, setNotice] = useState(null);
  const [statusMap, setStatusMap] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    setLoadingDocs(true);
    setNotice(null);
    try {
      const data = await apiGet("/api/documents");
      setDocuments(data.documents || []);
    } catch (error) {
      setNotice({ tone: "error", title: "Document load failed", body: error.message });
    } finally {
      setLoadingDocs(false);
    }
  }

  async function indexAll() {
    setIndexing(true);
    setNotice(null);
    setStatusMap(null);
    try {
      const data = await apiPost("/api/index", { force: false });
      setNotice({
        tone: "success",
        title: "Index request accepted",
        body: `${data.indexed} document(s) submitted to Glean.`,
      });
    } catch (error) {
      setNotice({ tone: "error", title: "Indexing failed", body: error.message });
    } finally {
      setIndexing(false);
    }
  }

  async function checkStatus() {
    if (documents.length === 0) return;
    setChecking(true);
    setNotice(null);
    try {
      const ids = documents.map((doc) => doc.id);
      setStatusMap(await apiPost("/api/index/status", ids));
    } catch (error) {
      setNotice({ tone: "error", title: "Status check failed", body: error.message });
    } finally {
      setChecking(false);
    }
  }

  const counts = useMemo(() => {
    const pdf = documents.filter((doc) => doc.type === "pdf").length;
    const txt = documents.filter((doc) => doc.type === "txt").length;
    return { pdf, txt, total: documents.length };
  }, [documents]);

  return (
    <section className="view">
      <ViewHeader
        eyebrow="Indexing API"
        title="Document indexing"
        action={
          <div className="header-actions">
            <button className="ghost-button" onClick={loadDocuments} disabled={loadingDocs} type="button">
              <Icon name="refresh" size={16} />
              Refresh
            </button>
            <button className="solid-button" onClick={indexAll} disabled={indexing || documents.length === 0} type="button">
              {indexing ? "Indexing" : "Index all"}
            </button>
          </div>
        }
      />

      <div className="index-grid">
        <section className="inventory">
          <div className="stats-row">
            <Stat label="Documents" value={counts.total} />
            <Stat label="Text" value={counts.txt} />
            <Stat label="PDF" value={counts.pdf} />
          </div>

          {notice && <Notice tone={notice.tone} title={notice.title} body={notice.body} />}

          <div className="section-title">Local documents</div>
          {loadingDocs ? (
            <RowsLoading label="Loading documents" />
          ) : documents.length === 0 ? (
            <EmptyState title="No documents" body="No supported files were found in the documents folder." />
          ) : (
            <div className="document-list">
              {documents.map((doc) => (
                <DocumentRow key={doc.id} doc={doc} status={statusMap?.[doc.id]} />
              ))}
            </div>
          )}
        </section>

        <aside className="status-panel">
          <div className="section-title">Index status</div>
          <button className="wide-button" onClick={checkStatus} disabled={checking || documents.length === 0} type="button">
            <Icon name="database" size={16} />
            {checking ? "Checking" : "Check indexed docs"}
          </button>
          <div className="status-note">
            Submitted documents can take a short time to become searchable.
          </div>
        </aside>
      </div>
    </section>
  );
}

function DocumentRow({ doc, status }) {
  return (
    <article className="document-row">
      <div className={`file-type ${doc.type || "doc"}`}>{(doc.type || "doc").toUpperCase()}</div>
      <div className="document-info">
        <a href={doc.url} target="_blank" rel="noreferrer">
          {doc.title}
        </a>
        <code>{doc.id}</code>
        {status && (
          <pre className={status.status === "error" ? "status-json error" : "status-json"}>
            {JSON.stringify(status, null, 2)}
          </pre>
        )}
      </div>
    </article>
  );
}

function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Notice({ tone, title, body }) {
  return (
    <div className={`notice ${tone}`}>
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  );
}

function EmptyState({ title, body }) {
  return (
    <div className="empty-state">
      <div className="empty-icon">
        <Icon name="file" />
      </div>
      <strong>{title}</strong>
      <span>{body}</span>
    </div>
  );
}

function RowsLoading({ label }) {
  return (
    <div className="rows-loading">
      <LoadingDots />
      <span>{label}</span>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<Shell />);
