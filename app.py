"""
DocuBot — AI-powered document chatbot
Extracts Word docs, queries databases & APIs via LangChain
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.document_processor import DocumentProcessor
from src.database import Database
from src.api_client import APIClient
from src.chatbot import DocuBotAgent

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DocuBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

  :root {
    --bg: #0d0f14;
    --surface: #161921;
    --surface2: #1e2330;
    --accent: #4fffb0;
    --accent2: #7c6dfa;
    --text: #e8eaf0;
    --muted: #6b7280;
    --border: #2a2f3e;
  }

  html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
  }

  .stApp { background: var(--bg) !important; }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border);
  }

  /* Chat messages */
  .chat-user {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 12px 12px 2px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-left: 20%;
    font-size: 14px;
  }

  .chat-bot {
    background: linear-gradient(135deg, #1a2040 0%, #1e1a40 100%);
    border: 1px solid var(--accent2);
    border-radius: 2px 12px 12px 12px;
    padding: 12px 16px;
    margin: 8px 0;
    margin-right: 20%;
    font-size: 14px;
  }

  .chat-bot .source-badge {
    display: inline-block;
    background: rgba(76, 255, 176, 0.1);
    border: 1px solid var(--accent);
    color: var(--accent);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-family: 'Space Mono', monospace;
    margin: 2px;
  }

  /* Buttons */
  .stButton button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 8px 20px !important;
    transition: all 0.2s !important;
  }

  .stButton button:hover {
    background: #2de098 !important;
    transform: translateY(-1px) !important;
  }

  /* File uploader */
  [data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1px dashed var(--border) !important;
    border-radius: 8px !important;
  }

  /* Header */
  .logo-header {
    font-family: 'Space Mono', monospace;
    font-size: 28px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: -1px;
  }

  .logo-header span { color: var(--accent2); }

  .subtitle {
    font-size: 13px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
  }

  /* Doc chips */
  .doc-chip {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 12px;
    color: var(--accent);
    margin: 4px 0;
    font-family: 'Space Mono', monospace;
  }

  /* Status indicator */
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    display: inline-block;
    background: var(--accent);
    box-shadow: 0 0 8px var(--accent);
    margin-right: 6px;
  }

  /* Metrics */
  .metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
  }
  .metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 24px;
    color: var(--accent);
    font-weight: 700;
  }
  .metric-lbl {
    font-size: 11px;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
  }

  /* Chat input */
  .stTextInput input, [data-testid="stChatInput"] textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif !important;
  }

  div[data-testid="stChatInput"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
  }

  .stSelectbox select, [data-testid="stSelectbox"] {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--text) !important;
  }

  /* Source tags in sidebar */
  .source-active {
    color: var(--accent);
    font-size: 12px;
    font-family: 'Space Mono', monospace;
  }
  .source-inactive { color: var(--muted); font-size: 12px; }

  hr { border-color: var(--border) !important; opacity: 0.5; }
  
  .stMarkdown h3 { color: var(--accent) !important; font-family: 'Space Mono', monospace; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "messages": [],
        "documents": [],
        "doc_processor": None,
        "db": None,
        "agent": None,
        "sources_enabled": {"documents": True, "database": True, "api": True},
        "db_initialized": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


init_state()


# ─── Initialize Services ───────────────────────────────────────────────────────
@st.cache_resource
def get_database():
    db = Database()
    db.seed_sample_data()
    return db


@st.cache_resource
def get_api_client():
    return APIClient()


def get_or_create_agent():
    if st.session_state.agent is None:
        db = get_database()
        api_client = get_api_client()
        doc_processor = st.session_state.doc_processor or DocumentProcessor()
        st.session_state.agent = DocuBotAgent(
            doc_processor=doc_processor,
            database=db,
            api_client=api_client,
        )
    return st.session_state.agent


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="logo-header">Docu<span>Bot</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">// AI Document Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Stats
    db = get_database()
    doc_count = len(st.session_state.documents)
    record_count = db.get_record_count()

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{doc_count}</div><div class="metric-lbl">Docs Loaded</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-val">{record_count}</div><div class="metric-lbl">DB Records</div></div>', unsafe_allow_html=True)

    st.markdown("---")

    # Document Upload
    st.markdown("### 📄 Upload Documents")
    uploaded_files = st.file_uploader(
        "Drop .docx files here",
        type=["docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        if st.button("⚡ Process Documents", use_container_width=True):
            with st.spinner("Extracting & indexing..."):
                if st.session_state.doc_processor is None:
                    st.session_state.doc_processor = DocumentProcessor()

                processor = st.session_state.doc_processor
                new_docs = []

                for f in uploaded_files:
                    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
                        tmp.write(f.read())
                        tmp_path = tmp.name

                    result = processor.process_document(tmp_path, f.name)
                    if result:
                        new_docs.append(result)
                    os.unlink(tmp_path)

                st.session_state.documents.extend(new_docs)
                st.session_state.agent = None  # Reset agent to pick up new docs
                st.success(f"✅ Processed {len(new_docs)} document(s)")
                st.rerun()

    # Show loaded docs
    if st.session_state.documents:
        st.markdown("**Indexed Documents:**")
        for doc in st.session_state.documents:
            st.markdown(f'<div class="doc-chip">📄 {doc["name"][:25]}...</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Data Sources Toggle
    st.markdown("### 🔌 Data Sources")
    sources = st.session_state.sources_enabled

    s1 = st.toggle("📄 Documents", value=sources["documents"], key="tog_doc")
    s2 = st.toggle("🗄️  Database", value=sources["database"], key="tog_db")
    s3 = st.toggle("🌐 External APIs", value=sources["api"], key="tog_api")

    st.session_state.sources_enabled = {"documents": s1, "database": s2, "api": s3}

    st.markdown("---")

    # Sample Queries
    st.markdown("### 💡 Try These")
    sample_qs = [
        "Summarize all uploaded documents",
        "List all employees in the database",
        "Compare document content with DB records",
        "What products are available?",
        "Find any discrepancies between docs and DB",
    ]

    for q in sample_qs:
        if st.button(q, key=f"sq_{q[:20]}", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# ─── Main Chat UI ──────────────────────────────────────────────────────────────
header_col, status_col = st.columns([3, 1])
with header_col:
    st.markdown("## 🤖 DocuBot — Document Intelligence")
    st.markdown("Ask me anything about your documents, database records, or live data.")
with status_col:
    api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")
    if api_key:
        st.markdown('<br><span class="status-dot"></span><span style="font-size:12px;color:#4fffb0">LLM Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<br><span style="font-size:12px;color:#f87171">⚠️ Set API Key in .env</span>', unsafe_allow_html=True)

st.markdown("---")

# Chat history
chat_container = st.container()
with chat_container:
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center; padding: 60px 0; color: #6b7280;">
            <div style="font-size: 48px; margin-bottom: 16px;">🗂️</div>
            <div style="font-family: 'Space Mono', monospace; font-size: 16px; color: #4fffb0;">Upload documents & start chatting</div>
            <div style="font-size: 13px; margin-top: 8px;">Or try a sample query from the sidebar →</div>
        </div>
        """, unsafe_allow_html=True)

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
        else:
            content = msg["content"]
            sources_html = ""
            if "sources" in msg:
                for src in msg["sources"]:
                    sources_html += f'<span class="source-badge">{src}</span> '
            st.markdown(
                f'<div class="chat-bot">🤖 {content}'
                + (f'<br><br>{sources_html}' if sources_html else "")
                + "</div>",
                unsafe_allow_html=True,
            )

# Chat Input
if prompt := st.chat_input("Ask about your documents, data, or anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            agent = get_or_create_agent()
            response = agent.chat(
                prompt,
                sources_enabled=st.session_state.sources_enabled,
                chat_history=st.session_state.messages[:-1],
            )
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response.get("sources", []),
            })
        except Exception as e:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Error: {str(e)}\n\nMake sure your API key is set in `.env`",
                "sources": [],
            })

    st.rerun()
