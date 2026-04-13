"""
RAG Agent — answers questions using policy documents from the vector store.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from utils.vector_store import get_vector_store

RAG_SYSTEM_PROMPT = """You are a helpful customer support assistant specializing in
company policies. Answer the user's question based ONLY on the provided context
from our policy documents.

Rules:
- Base your answer strictly on the provided context.
- If the context does not contain enough information, say so clearly.
- Cite which policy document the information comes from.
- Be concise but thorough.
- Use a friendly, professional tone.
"""


def answer_rag_question(question: str, llm: ChatOpenAI) -> str:
    """Retrieve relevant policy chunks and generate an answer."""
    vectorstore = get_vector_store()
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    docs = retriever.invoke(question)

    if not docs:
        return ("I couldn't find any relevant information in our policy documents "
                "for your question. Could you please rephrase or provide more details?")

    context_parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "Unknown")
        context_parts.append(f"[Source: {source}]\n{doc.page_content}")

    context = "\n\n---\n\n".join(context_parts)

    prompt = (
        f"Context from policy documents:\n\n{context}\n\n"
        f"---\n\nUser question: {question}"
    )

    response = llm.invoke([
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    return response.content
