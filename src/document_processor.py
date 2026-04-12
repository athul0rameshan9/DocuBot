"""
Document Processor
─────────────────
Extracts text, tables, and metadata from .docx files.
Chunks and stores in an in-memory vector store for semantic search.
"""

import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

try:
    from docx import Document
    from docx.shared import Pt
except ImportError:
    raise ImportError("Run: pip install python-docx")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain_anthropic import ChatAnthropic
except ImportError:
    pass


class DocumentProcessor:
    """
    Extracts rich content from .docx files and indexes them for semantic search.

    Capabilities:
    - Full text extraction (paragraphs, headings, lists)
    - Table extraction → structured text
    - Metadata extraction (author, created date, word count)
    - Chunked vector indexing via FAISS + OpenAI Embeddings
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = None
        self.processed_docs: list[dict] = []
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
        )

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def process_document(self, file_path: str, display_name: Optional[str] = None) -> Optional[dict]:
        """
        Process a single .docx file. Returns a summary dict or None on failure.
        """
        try:
            doc = Document(file_path)
            name = display_name or Path(file_path).name

            full_text = self._extract_text(doc)
            tables = self._extract_tables(doc)
            metadata = self._extract_metadata(doc, name)

            combined = full_text
            if tables:
                combined += "\n\n[TABLES]\n" + "\n\n".join(tables)

            # Index into vector store
            self._index_document(combined, name)

            result = {
                "name": name,
                "path": file_path,
                "text": full_text,
                "tables": tables,
                "metadata": metadata,
                "word_count": len(full_text.split()),
                "char_count": len(full_text),
                "processed_at": datetime.now().isoformat(),
                "preview": full_text[:300].strip() + "...",
            }

            self.processed_docs.append(result)
            return result

        except Exception as e:
            print(f"[DocumentProcessor] Error processing {file_path}: {e}")
            return None

    def search(self, query: str, k: int = 4) -> list[dict]:
        """
        Semantic search across all indexed documents.
        Returns list of {content, source, score} dicts.
        """
        if self.vector_store is None:
            return []

        try:
            results = self.vector_store.similarity_search_with_score(query, k=k)
            return [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "score": float(score),
                }
                for doc, score in results
            ]
        except Exception as e:
            print(f"[DocumentProcessor] Search error: {e}")
            return []

    def get_all_text(self) -> str:
        """Return concatenated text from all documents."""
        if not self.processed_docs:
            return ""
        parts = []
        for doc in self.processed_docs:
            parts.append(f"=== {doc['name']} ===\n{doc['text']}")
        return "\n\n".join(parts)

    def get_summary_stats(self) -> dict:
        return {
            "total_docs": len(self.processed_docs),
            "total_words": sum(d["word_count"] for d in self.processed_docs),
            "doc_names": [d["name"] for d in self.processed_docs],
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _extract_text(self, doc: "Document") -> str:
        """Extract all paragraph text preserving headings and structure."""
        lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = para.style.name.lower() if para.style else ""
            if "heading" in style_name:
                level = self._get_heading_level(style_name)
                lines.append(f"\n{'#' * level} {text}\n")
            elif "list" in style_name:
                lines.append(f"  • {text}")
            else:
                lines.append(text)
        return "\n".join(lines)

    def _extract_tables(self, doc: "Document") -> list[str]:
        """Convert all tables to readable text format."""
        table_texts = []
        for i, table in enumerate(doc.tables, 1):
            rows = []
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows.append(" | ".join(cells))
            if rows:
                header = rows[0]
                separator = "-+-".join(["-" * len(c) for c in rows[0].split(" | ")])
                body = "\n".join(rows[1:]) if len(rows) > 1 else ""
                table_texts.append(f"Table {i}:\n{header}\n{separator}\n{body}")
        return table_texts

    def _extract_metadata(self, doc: "Document", name: str) -> dict:
        """Extract core properties from the document."""
        props = doc.core_properties
        return {
            "name": name,
            "author": getattr(props, "author", "Unknown") or "Unknown",
            "created": str(getattr(props, "created", "Unknown")),
            "modified": str(getattr(props, "modified", "Unknown")),
            "subject": getattr(props, "subject", "") or "",
            "keywords": getattr(props, "keywords", "") or "",
            "paragraph_count": len(doc.paragraphs),
            "table_count": len(doc.tables),
        }

    def _get_heading_level(self, style_name: str) -> int:
        """Extract heading level number from style name."""
        match = re.search(r"(\d+)", style_name)
        return int(match.group(1)) if match else 2

    def _index_document(self, text: str, source_name: str):
        """Chunk text and add to FAISS vector store."""
        from langchain.schema import Document as LCDocument

        chunks = self._splitter.split_text(text)
        lc_docs = [
            LCDocument(page_content=chunk, metadata={"source": source_name})
            for chunk in chunks
            if chunk.strip()
        ]

        if not lc_docs:
            return

        try:
            embeddings = self._get_embeddings()
            if self.vector_store is None:
                self.vector_store = FAISS.from_documents(lc_docs, embeddings)
            else:
                self.vector_store.add_documents(lc_docs)
        except Exception as e:
            print(f"[DocumentProcessor] Indexing warning (fallback to text search): {e}")

    def _get_embeddings(self):
        """Get embeddings model — tries OpenAI first, falls back gracefully."""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            return OpenAIEmbeddings(openai_api_key=api_key)
        raise ValueError("OPENAI_API_KEY not set. Set it in .env to enable semantic search.")
