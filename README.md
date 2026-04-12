# 🤖 DocuBot — AI Document Intelligence Chatbot

A production-ready AI chatbot that extracts and analyzes Word documents, queries databases, and fetches live API data — all through a clean conversational interface.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                   DocuBot Agent                     │
│  (LangChain + Claude Sonnet / GPT-4)                │
└──────────┬────────────────┬───────────────┬─────────┘
           │                │               │
    ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼────────┐
    │  Documents  │  │  Database   │  │  Live APIs  │
    │  .docx      │  │  SQLite     │  │  Weather    │
    │  FAISS      │  │  Employees  │  │  Countries  │
    │  Semantic   │  │  Products   │  │  FX Rates   │
    │  Search     │  │  Projects   │  │             │
    └─────────────┘  └─────────────┘  └─────────────┘
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 📄 **Word Doc Extraction** | Paragraphs, headings, lists, tables, metadata |
| 🔍 **Semantic Search** | FAISS + OpenAI embeddings for intelligent retrieval |
| 🗄️ **Database Queries** | LLM-driven SQL on employees, products, projects, contracts |
| 🌐 **Live APIs** | Real-time weather, country info, currency rates |
| 🔄 **Multi-turn Chat** | Full conversation history with source attribution |
| 🎨 **Beautiful UI** | Dark-mode Streamlit with custom styling |
| ⚙️ **Source Toggles** | Enable/disable Documents, DB, or API per-query |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/docubot
cd docubot
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and add your API key:
# ANTHROPIC_API_KEY=sk-ant-...   ← Claude (recommended)
# OPENAI_API_KEY=sk-...          ← GPT-4 (fallback)
```

> **Minimum requirement:** One LLM key (Anthropic or OpenAI).  
> OpenAI key also enables semantic search embeddings.

### 3. Generate Sample Documents (optional)

```bash
python generate_sample_docs.py
```

Creates three realistic .docx files in `./sample_docs/` for immediate testing.

### 4. Launch

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) 🎉

---

## 💬 Example Queries

Once running, try these:

```
"Summarize all uploaded documents"
"List all employees in the Engineering department"
"What's the weather in Mumbai today?"
"Compare the products in the document vs the database"
"Which projects are over budget?"
"Convert USD to INR exchange rate"
"Find any employees mentioned in the uploaded documents"
"What are the key risks in the project report?"
```

---

## 📁 Project Structure

```
docubot/
├── app.py                    # Streamlit UI & orchestration
├── src/
│   ├── chatbot.py            # LangChain agent (main intelligence)
│   ├── document_processor.py # .docx extraction + FAISS indexing
│   ├── database.py           # SQLite integration + sample data
│   └── api_client.py         # External API integrations
├── sample_docs/              # Auto-generated test documents
├── generate_sample_docs.py   # Sample document generator
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔌 Adding New Data Sources

### New API

In `src/api_client.py`, add a method:
```python
def get_stock_price(self, ticker: str) -> dict:
    r = httpx.get(f"https://api.example.com/stock/{ticker}")
    return r.json()
```

Then register it in `dispatch()` and update `_get_api_context()` in `chatbot.py`.

### New Database Table

In `src/database.py`, add to `_create_tables()`:
```sql
CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY,
    client TEXT,
    amount REAL,
    due_date TEXT
);
```

Seed data in `seed_sample_data()` and add detection keywords in `chatbot.py`'s `_get_database_context()`.

---

## 🧠 LLM Support

| Provider | Model | Setup |
|---|---|---|
| **Anthropic** (recommended) | claude-sonnet-4-20250514 | `ANTHROPIC_API_KEY` |
| **OpenAI** | gpt-4o | `OPENAI_API_KEY` |

---

## 📦 Dependencies

- **Streamlit** — UI framework
- **python-docx** — Word document parsing
- **LangChain** — LLM orchestration & chains
- **FAISS** — Vector similarity search
- **httpx** — Async HTTP for API calls
- **SQLite** (built-in) — Local database

---

## 🛣️ Roadmap

- [ ] PDF support (pdfplumber)
- [ ] PostgreSQL / MySQL connector
- [ ] LangChain Tools + ReAct agent
- [ ] User authentication
- [ ] Export chat as PDF report
- [ ] Slack/Teams integration

---

## 📄 License

MIT © 2024 — Built with ❤️ using LangChain + Anthropic Claude
