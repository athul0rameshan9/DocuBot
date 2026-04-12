"""
DocuBot Agent
─────────────
LangChain-powered conversational agent that intelligently routes
queries to documents, database, or external APIs.

Architecture:
  User Query
      │
      ▼
  DocuBotAgent.chat()
      │
      ├─► Document Search (FAISS semantic search)
      ├─► Database Query (LLM → SQL → results)
      └─► API Calls (weather, country, rates)
      │
      ▼
  LLM Synthesis → Final Answer
"""

import os
import json
import re
from typing import Optional

from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, AIMessage, SystemMessage


class DocuBotAgent:
    """
    Multi-source conversational AI agent.
    
    Supports:
    - Anthropic Claude (claude-sonnet-4-20250514)
    - OpenAI GPT-4 (fallback)
    """

    SYSTEM_PROMPT = """You are DocuBot, an expert AI assistant that answers questions by intelligently combining information from:

1. **Uploaded Documents** — Word files the user has provided
2. **Internal Database** — SQLite records (employees, products, projects, contracts)  
3. **External APIs** — Live weather, country info, currency rates

## Your Behavior:
- Always cite which source you used (Document / Database / API / Knowledge)
- When asked to compare, clearly show similarities and differences
- Generate SQL mentally when querying the database context provided
- Be concise but thorough
- If information is missing from provided context, say so clearly

## Response Format:
- Use markdown for structure
- Bold key findings
- Use tables when comparing data
- End complex answers with a brief **Summary** section

{doc_context}
{db_context}
{api_capabilities}"""

    def __init__(self, doc_processor, database, api_client):
        self.doc_processor = doc_processor
        self.database = database
        self.api_client = api_client
        self._llm = None

    # ──────────────────────────────────────────────────────────────────────────
    # Public
    # ──────────────────────────────────────────────────────────────────────────

    def chat(
        self,
        query: str,
        sources_enabled: dict = None,
        chat_history: list = None,
    ) -> dict:
        """
        Process a user query across all enabled sources.
        Returns {answer: str, sources: list[str]}
        """
        sources_enabled = sources_enabled or {"documents": True, "database": True, "api": True}
        chat_history = chat_history or []

        context_parts = []
        sources_used = []

        # 1. Document context
        if sources_enabled.get("documents") and self.doc_processor.processed_docs:
            doc_results = self.doc_processor.search(query, k=3)
            if doc_results:
                context_parts.append(self._format_doc_context(doc_results))
                sources_used.append("📄 Documents")
            else:
                # Fall back to full text if no vector store
                all_text = self.doc_processor.get_all_text()
                if all_text:
                    context_parts.append(f"DOCUMENT CONTENT:\n{all_text[:3000]}")
                    sources_used.append("📄 Documents")

        # 2. Database context
        if sources_enabled.get("database"):
            db_context = self._get_database_context(query)
            if db_context:
                context_parts.append(db_context)
                sources_used.append("🗄️ Database")

        # 3. API context
        if sources_enabled.get("api"):
            api_context = self._get_api_context(query)
            if api_context:
                context_parts.append(api_context)
                sources_used.append("🌐 Live API")

        # Build system message
        system_content = self._build_system_prompt(context_parts)

        # Get LLM response
        llm = self._get_llm()
        messages = self._build_messages(system_content, chat_history, query)
        response = llm.invoke(messages)

        return {
            "answer": response.content,
            "sources": sources_used,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Context Builders
    # ──────────────────────────────────────────────────────────────────────────

    def _format_doc_context(self, doc_results: list) -> str:
        parts = ["RELEVANT DOCUMENT EXCERPTS:"]
        for i, r in enumerate(doc_results, 1):
            parts.append(f"\n[Excerpt {i} from '{r['source']}']:\n{r['content']}")
        return "\n".join(parts)

    def _get_database_context(self, query: str) -> str:
        """
        Smart DB context: run relevant queries based on keywords in the query.
        """
        query_lower = query.lower()
        parts = ["DATABASE RECORDS:"]
        found = False

        keyword_queries = {
            ("employee", "staff", "team", "person", "hire", "salary", "department", "role"): (
                "SELECT name, department, role, salary, hire_date, status FROM employees ORDER BY department",
                "employees"
            ),
            ("product", "item", "catalog", "sku", "price", "stock", "inventory"): (
                "SELECT name, category, price, stock, description FROM products WHERE active=1",
                "products"
            ),
            ("project", "initiative", "budget", "deadline"): (
                "SELECT p.title, p.status, p.start_date, p.end_date, p.budget, e.name as lead "
                "FROM projects p LEFT JOIN employees e ON p.lead_id = e.id",
                "projects"
            ),
            ("contract", "client", "deal", "agreement", "revenue"): (
                "SELECT client_name, value, start_date, end_date, status FROM contracts",
                "contracts"
            ),
        }

        for keywords, (sql, label) in keyword_queries.items():
            if any(kw in query_lower for kw in keywords):
                rows = self.database.query(sql)
                if rows and "error" not in rows[0]:
                    parts.append(f"\n{label.upper()}:\n{self._rows_to_text(rows)}")
                    found = True

        # Always include schema + summary for context
        parts.append(f"\nDB SCHEMA:\n{self.database.get_schema()}")
        parts.append(f"\nDB SUMMARY: {self.database.get_context_summary()}")

        return "\n".join(parts) if found else "\n".join(parts[-2:])  # just schema if no specific match

    def _get_api_context(self, query: str) -> str:
        """Call appropriate APIs based on query content."""
        query_lower = query.lower()
        parts = []

        # Weather
        city_match = re.search(
            r"weather (?:in |for |at )?([A-Za-z\s]+?)(?:\?|$|,| today| now| currently)",
            query,
            re.IGNORECASE,
        )
        if city_match or any(w in query_lower for w in ["weather", "temperature", "climate", "rain", "forecast"]):
            city = city_match.group(1).strip() if city_match else "London"
            data = self.api_client.get_weather(city)
            if "error" not in data:
                parts.append(f"LIVE WEATHER ({city}):\n{json.dumps(data, indent=2)}")

        # Country info
        country_match = re.search(
            r"(?:about|info on|tell me about|details on) ([A-Za-z\s]+?)(?:\?|$|,)",
            query,
            re.IGNORECASE,
        )
        if country_match and any(w in query_lower for w in ["country", "nation", "capital", "population"]):
            country = country_match.group(1).strip()
            data = self.api_client.get_country_info(country)
            if "error" not in data:
                parts.append(f"COUNTRY INFO ({country}):\n{json.dumps(data, indent=2)}")

        # Exchange rates
        fx_match = re.search(
            r"(\b[A-Z]{3}\b).*?(?:to|in|vs).*?(\b[A-Z]{3}\b)",
            query,
        )
        if fx_match or any(w in query_lower for w in ["exchange rate", "currency", "convert", "forex"]):
            base = fx_match.group(1) if fx_match else "USD"
            target = fx_match.group(2) if fx_match else "EUR"
            data = self.api_client.get_exchange_rate(base, target)
            if "error" not in data:
                parts.append(f"EXCHANGE RATE ({base}→{target}):\n{json.dumps(data, indent=2)}")

        return "\n\n".join(parts) if parts else ""

    # ──────────────────────────────────────────────────────────────────────────
    # LLM Setup
    # ──────────────────────────────────────────────────────────────────────────

    def _get_llm(self):
        if self._llm:
            return self._llm

        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if anthropic_key:
            from langchain_anthropic import ChatAnthropic
            self._llm = ChatAnthropic(
                model="claude-sonnet-4-20250514",
                anthropic_api_key=anthropic_key,
                max_tokens=2048,
            )
        elif openai_key:
            from langchain_openai import ChatOpenAI
            self._llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=openai_key,
                max_tokens=2048,
            )
        else:
            raise ValueError(
                "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file."
            )

        return self._llm

    def _build_system_prompt(self, context_parts: list) -> str:
        """Inject all context into system prompt."""
        context_block = "\n\n".join(context_parts) if context_parts else "No specific data context provided."
        return (
            "You are DocuBot, an AI assistant that answers questions using documents, databases, and live APIs.\n\n"
            "## AVAILABLE CONTEXT\n"
            f"{context_block}\n\n"
            "## INSTRUCTIONS\n"
            "- Answer the user's question using the context above.\n"
            "- Cite sources: (Document), (Database), (API), or (General Knowledge).\n"
            "- Use markdown formatting with headers, bold, and tables where helpful.\n"
            "- If asked to compare, show a clear comparison table.\n"
            "- If data is missing, state what's unavailable and why.\n"
            "- Be concise but complete."
        )

    def _build_messages(self, system: str, history: list, query: str) -> list:
        messages = [SystemMessage(content=system)]
        for h in history[-6:]:  # last 6 turns for context window management
            if h["role"] == "user":
                messages.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                messages.append(AIMessage(content=h["content"]))
        messages.append(HumanMessage(content=query))
        return messages

    def _rows_to_text(self, rows: list[dict]) -> str:
        if not rows:
            return "(empty)"
        headers = list(rows[0].keys())
        lines = [" | ".join(headers)]
        lines.append("-" * len(lines[0]))
        for row in rows[:20]:  # cap at 20 rows
            lines.append(" | ".join(str(v or "") for v in row.values()))
        if len(rows) > 20:
            lines.append(f"... and {len(rows) - 20} more rows")
        return "\n".join(lines)
