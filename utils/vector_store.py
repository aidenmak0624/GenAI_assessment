"""
Vector store management for PDF policy documents using ChromaDB.
"""

import os
import fitz  # PyMuPDF
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

VECTORSTORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "data", "vectorstore")
DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text


def load_and_split_pdfs(docs_dir: str = DOCS_DIR) -> list:
    """Load PDFs from directory, extract text, and split into chunks."""
    from langchain_core.documents import Document

    documents = []
    if not os.path.exists(docs_dir):
        print(f"Docs directory not found: {docs_dir}")
        return documents

    for filename in os.listdir(docs_dir):
        if filename.endswith(".pdf"):
            filepath = os.path.join(docs_dir, filename)
            text = extract_text_from_pdf(filepath)
            documents.append(Document(
                page_content=text,
                metadata={"source": filename, "type": "policy_document"}
            ))
            print(f"  Loaded: {filename} ({len(text)} chars)")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_documents(documents)
    print(f"  Split into {len(chunks)} chunks")
    return chunks


def build_vector_store(docs_dir: str = DOCS_DIR,
                       persist_dir: str = VECTORSTORE_DIR) -> Chroma:
    """Build (or rebuild) the ChromaDB vector store from PDFs."""
    chunks = load_and_split_pdfs(docs_dir)
    if not chunks:
        raise ValueError("No PDF documents found to index.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Clear existing store
    if os.path.exists(persist_dir):
        import shutil
        shutil.rmtree(persist_dir)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir,
        collection_name="policy_docs",
    )
    print(f"  Vector store built at {persist_dir}")
    return vectorstore


def get_vector_store(persist_dir: str = VECTORSTORE_DIR) -> Chroma:
    """Load existing vector store or build a new one."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="policy_docs",
        )
    return build_vector_store()
