"""
RAG Agent — answers questions using policy documents from the vector store.
"""

import math
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.vector_store import get_vector_store

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with",
    "what", "which", "does", "say", "about", "how", "quickly", "is", "are",
    "be", "can", "within", "policy", "policies", "document", "documents",
    "support", "customer", "customers", "current", "give", "tell", "from",
    "this", "that", "these", "those", "into", "your", "their", "still",
    "would", "could", "should",
}

RAG_SYSTEM_PROMPT = """You are a helpful customer support assistant specializing in
company policies. Answer the user's question based ONLY on the provided context
from our policy documents.

Rules:
- Base your answer strictly on the provided context.
- If the context does not contain enough information, say so clearly.
- Be concise but thorough.
- Use a friendly, professional tone.
- Do not include inline bracket citations in the main answer.
- Do not invent citations or policy details that are not in the context.
"""


def _tokenize_for_rag_ranking(text: str) -> set[str]:
    """Extract meaningful lowercase tokens for simple lexical reranking."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {
        token for token in tokens
        if len(token) >= 3 and token not in STOPWORDS
    }


def _select_relevant_docs(question: str, docs: list) -> list:
    """Filter semantic hits so clearly relevant uploaded docs win over weak matches."""
    if not docs:
        return docs

    question_terms = _tokenize_for_rag_ranking(question)
    if not question_terms:
        return docs

    scored_docs = []
    for index, doc in enumerate(docs):
        source = doc.metadata.get("source", "")
        haystack = f"{source} {doc.page_content}"
        doc_terms = _tokenize_for_rag_ranking(haystack)
        overlap = question_terms & doc_terms
        scored_docs.append((len(overlap), index, doc))

    max_overlap = max(score for score, _, _ in scored_docs)
    if max_overlap <= 0:
        return docs

    if max_overlap >= 2:
        min_overlap = max(1, math.ceil(max_overlap * 0.5))
        filtered = [item for item in scored_docs if item[0] >= min_overlap]
    else:
        filtered = [item for item in scored_docs if item[0] > 0]

    if not filtered:
        filtered = [item for item in scored_docs if item[0] == max_overlap]

    filtered.sort(key=lambda item: (-item[0], item[1]))
    return [doc for _, _, doc in filtered[:4]]


def _format_policy_source_line(docs) -> str:
    """Build a deterministic source footer from retrieved policy chunks."""
    seen = set()
    refs = ["**Source:**"]
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        line_start = doc.metadata.get("line_start", "?")
        line_end = doc.metadata.get("line_end", "?")
        chunk_index = doc.metadata.get("chunk_index", "?")
        key = (source, page, line_start, line_end, chunk_index)
        if key in seen:
            continue
        seen.add(key)
        refs.append(
            f"- `{source}` (page {page}, lines {line_start}-{line_end}, chunk {chunk_index})"
        )
    return "\n".join(refs)


def _format_policy_evidence(docs) -> str:
    """Build a short evidence block with excerpts for reviewer-friendly auditing."""
    lines = ["**Evidence:**"]
    seen = set()
    for doc in docs:
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        line_start = doc.metadata.get("line_start", "?")
        line_end = doc.metadata.get("line_end", "?")
        chunk_index = doc.metadata.get("chunk_index", "?")
        key = (source, page, line_start, line_end, chunk_index)
        if key in seen:
            continue
        seen.add(key)
        excerpt = " ".join(doc.page_content.split())
        excerpt = excerpt[:180].rstrip()
        if len(" ".join(doc.page_content.split())) > 180:
            excerpt += "..."
        lines.append(
            f"- `{source}` page {page}, lines {line_start}-{line_end}, chunk {chunk_index}: "
            f"{excerpt}"
        )
    return "\n".join(lines)


def answer_rag_question(question: str, llm: ChatOpenAI) -> str:
    """Retrieve relevant policy chunks and generate an answer."""
    try:
        vectorstore = get_vector_store()
    except ValueError:
        return ("The policy document knowledge base has not been built yet. "
                "Please use the sidebar to generate policy documents and build "
                "the vector store before asking policy questions.")
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 8},
    )

    docs = _select_relevant_docs(question, retriever.invoke(question))

    if not docs:
        return ("I couldn't find any relevant information in our policy documents "
                "for your question. Could you please rephrase or provide more details?")

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page", "?")
        line_start = doc.metadata.get("line_start", "?")
        line_end = doc.metadata.get("line_end", "?")
        chunk_index = doc.metadata.get("chunk_index", "?")
        context_parts.append(
            f"[Source {i}: {source} p.{page} lines {line_start}-{line_end} chunk {chunk_index}]\n"
            f"{doc.page_content}"
        )

    context = "\n\n---\n\n".join(context_parts)

    prompt = (
        f"Context from policy documents:\n\n{context}\n\n"
        f"---\n\nUser question: {question}"
    )

    response = llm.invoke([
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    answer = response.content.strip()
    source_line = _format_policy_source_line(docs)
    evidence = _format_policy_evidence(docs)
    return f"{answer}\n\n---\n{source_line}\n\n{evidence}"
