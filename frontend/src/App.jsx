import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API = "http://localhost:8000";

function Message({ msg }) {
  return (
    <div className={`message ${msg.role}`}>
      <div className="avatar">{msg.role === "user" ? "U" : "F"}</div>
      <div className="bubble">
        <p>{msg.content}</p>
        {msg.sources && msg.sources.length > 0 && (
          <div className="sources">
            <p className="sources-label">Sources</p>
            {[...new Map(msg.sources.map(s => [s.source, s])).values()].map((s, i) => (
              <div key={i} className="source-item">
                <span className="source-icon">📄</span>
                <span>{s.source.split("\\").pop()} {s.page !== "N/A" ? `· page ${s.page}` : ""}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi, I'm FinSight. Upload a financial document and ask me anything about it." }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ ready: false, docs: [] });
  const [uploading, setUploading] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const bottomRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    try {
      const [health, docs] = await Promise.all([
        axios.get(`${API}/health`),
        axios.get(`${API}/documents`),
      ]);
      setStatus({ ready: health.data.retriever_ready, docs: docs.data.documents });
    } catch {}
  }

  async function handleUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      await axios.post(`${API}/upload`, form);
      await fetchStatus();
      addSystem(`"${file.name}" uploaded. Click Ingest to process it.`);
    } catch (err) {
      addSystem("Upload failed: " + (err.response?.data?.detail || err.message));
    }
    setUploading(false);
    fileRef.current.value = "";
  }

  async function handleIngest() {
    setIngesting(true);
    addSystem("Ingesting documents...");
    try {
      const res = await axios.post(`${API}/ingest`);
      await fetchStatus();
      addSystem(`Ready. ${res.data.documents_processed} document(s) processed.`);
    } catch (err) {
      addSystem("Ingestion failed: " + (err.response?.data?.detail || err.message));
    }
    setIngesting(false);
  }

  function addSystem(text) {
    setMessages(m => [...m, { role: "system", content: text }]);
  }

  async function handleSend() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", content: q }]);
    setLoading(true);
    try {
      const res = await axios.post(`${API}/query`, { question: q });
      setMessages(m => [...m, { role: "assistant", content: res.data.answer, sources: res.data.sources }]);
    } catch (err) {
      setMessages(m => [...m, { role: "assistant", content: "Error: " + (err.response?.data?.detail || err.message) }]);
    }
    setLoading(false);
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="logo">FinSight</div>
          <p className="logo-sub">Financial Document Intelligence</p>
        </div>

        <div className="sidebar-section">
          <p className="section-label">Documents</p>
          {status.docs.length === 0
            ? <p className="empty-docs">No documents yet</p>
            : status.docs.map((d, i) => (
              <div key={i} className="doc-item">
                <span className="doc-icon">📄</span>
                <span className="doc-name">{d}</span>
              </div>
            ))
          }
        </div>

        <div className="sidebar-actions">
          <input ref={fileRef} type="file" accept=".pdf,.txt" onChange={handleUpload} style={{ display: "none" }} />
          <button className="btn-upload" onClick={() => fileRef.current.click()} disabled={uploading}>
            {uploading ? "Uploading..." : "Upload Document"}
          </button>
          <button className="btn-ingest" onClick={handleIngest} disabled={ingesting || status.docs.length === 0}>
            {ingesting ? "Processing..." : "Ingest"}
          </button>
        </div>

        <div className="sidebar-bottom">
          <div className={`status-dot ${status.ready ? "ready" : "not-ready"}`} />
          <span>{status.ready ? "Ready to query" : "Not ready"}</span>
        </div>
      </aside>

      <main className="chat">
        <div className="messages">
          {messages.map((m, i) => <Message key={i} msg={m} />)}
          {loading && (
            <div className="message assistant">
              <div className="avatar">F</div>
              <div className="bubble typing"><span /><span /><span /></div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="input-bar">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about your financial documents..."
            rows={1}
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </main>
    </div>
  );
}
