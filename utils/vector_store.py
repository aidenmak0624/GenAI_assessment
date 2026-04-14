"""
Vector store management for PDF policy documents using ChromaDB.
"""

import os
import shutil
from bisect import bisect_right
from contextlib import suppress

from chromadb.api.client import SharedSystemClient
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

VECTORSTORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "data", "vectorstore")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
COLLECTION_NAME = "policy_docs"
_cached_vectorstore: Chroma | None = None


def _build_line_starts(text: str) -> list[int]:
    """Return character offsets for the start of each extracted line."""
    starts = [0]
    cursor = 0
    for line in text.splitlines(keepends=True):
        cursor += len(line)
        starts.append(cursor)
    return starts


def _line_number_for_offset(line_starts: list[int], offset: int) -> int:
    """Map a character offset back to an approximate 1-based line number."""
    if not line_starts:
        return 1
    clamped = max(0, offset)
    line_idx = bisect_right(line_starts, clamped) - 1
    return max(0, line_idx) + 1


def _annotate_chunk_lines(text: str, start_index: int, chunk_text: str) -> tuple[int, int]:
    """Return approximate line numbers for a chunk within a page."""
    line_starts = _build_line_starts(text)
    end_index = start_index + max(0, len(chunk_text) - 1)
    return (
        _line_number_for_offset(line_starts, start_index),
        _line_number_for_offset(line_starts, end_index),
    )


def load_and_split_pdfs(docs_dir: str = DOCS_DIR) -> list:
    """Load PDFs page-by-page, then split into line-aware chunks."""
    from langchain_core.documents import Document

    chunks: list[Document] = []
    if not os.path.exists(docs_dir):
        print(f"Docs directory not found: {docs_dir}")
        return chunks

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
        add_start_index=True,
    )

    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith(".pdf"):
            filepath = os.path.join(docs_dir, filename)
            with fitz.open(filepath) as pdf:
                total_chars = 0
                file_chunk_count = 0
                for page_number, page in enumerate(pdf, start=1):
                    page_text = page.get_text("text")
                    if not page_text.strip():
                        continue
                    total_chars += len(page_text)
                    page_chunks = splitter.create_documents(
                        [page_text],
                        metadatas=[{
                            "source": filename,
                            "type": "policy_document",
                            "page": page_number,
                        }],
                    )
                    for chunk_index, chunk in enumerate(page_chunks, start=1):
                        start_index = chunk.metadata.get("start_index", 0)
                        line_start, line_end = _annotate_chunk_lines(
                            page_text,
                            start_index,
                            chunk.page_content,
                        )
                        chunk.metadata.update({
                            "line_start": line_start,
                            "line_end": line_end,
                            "chunk_index": chunk_index,
                        })
                    file_chunk_count += len(page_chunks)
                    chunks.extend(page_chunks)
                print(
                    f"  Loaded: {filename} ({total_chars} chars, {file_chunk_count} chunks)"
                )

    print(f"  Split into {len(chunks)} chunks")
    return chunks


def _stop_vectorstore_client(vectorstore: Chroma | None) -> None:
    """Release the underlying Chroma system so the persist directory can be rebuilt."""
    if vectorstore is None:
        return
    client = getattr(vectorstore, "_client", None)
    system = getattr(client, "_system", None)
    if system is not None:
        with suppress(Exception):
            system.stop()


def _reset_chroma_runtime() -> None:
    """Reset cached Chroma clients to avoid stale shared-system state."""
    global _cached_vectorstore
    _stop_vectorstore_client(_cached_vectorstore)
    _cached_vectorstore = None
    with suppress(Exception):
        SharedSystemClient.clear_system_cache()


def build_vector_store(docs_dir: str = DOCS_DIR,
                       persist_dir: str = VECTORSTORE_DIR) -> Chroma:
    """Build (or rebuild) the ChromaDB vector store from PDFs."""
    global _cached_vectorstore
    _reset_chroma_runtime()
    chunks = load_and_split_pdfs(docs_dir)
    if not chunks:
        raise ValueError("No PDF documents found to index.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Clear existing store completely after the active Chroma system is released.
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
    os.makedirs(persist_dir, exist_ok=True)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name=COLLECTION_NAME,
    )
    _cached_vectorstore = vectorstore
    print(f"  Vector store built at {persist_dir}")
    return vectorstore


def get_vector_store(persist_dir: str = VECTORSTORE_DIR) -> Chroma:
    """Load existing vector store or build a new one. Cached after first load."""
    global _cached_vectorstore
    if _cached_vectorstore is not None:
        return _cached_vectorstore
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        _cached_vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME,
        )
        return _cached_vectorstore
    _cached_vectorstore = build_vector_store()
    return _cached_vectorstore


def invalidate_vector_store_cache():
    """Clear the cached vector store (call after rebuilding)."""
    _reset_chroma_runtime()
