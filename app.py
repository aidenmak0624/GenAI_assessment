"""
Streamlit UI for the Customer Support Multi-Agent System.

Features:
  - Conversation history with follow-up question support
  - PDF upload and indexing
  - One-click system setup
  - Agent routing indicators
"""

import os
import sys
import streamlit as st
from dotenv import load_dotenv

# -- Setup ------------------------------------------------------------------
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from langchain_openai import ChatOpenAI
from agents.graph import build_graph
from utils.vector_store import build_vector_store, get_vector_store, VECTORSTORE_DIR
from data.init_db import init_database, DB_PATH
from data.generate_policies import generate_all_policies, DOCS_DIR

# -- Page config ------------------------------------------------------------
st.set_page_config(
    page_title="TechCorp Customer Support AI",
    page_icon="🤖",
    layout="wide",
)

# -- Sidebar ----------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Configuration")

    api_key = st.text_input("OpenAI API Key", type="password",
                            value=os.getenv("OPENAI_API_KEY", ""))
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.divider()

    st.subheader("🗄️ System Setup")

    # One-click full setup
    if st.button("🚀 Full Setup (DB + PDFs + Vector Store)", use_container_width=True):
        if not api_key:
            st.error("Please set your OpenAI API key first.")
        else:
            with st.spinner("Setting up everything..."):
                init_database()
                generate_all_policies()
                build_vector_store()
            st.success("System fully initialized!")

    st.caption("Or set up individually:")

    # Database initialization
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Init Database", use_container_width=True):
            with st.spinner("Creating database..."):
                init_database()
            st.success("Database ready!")

    with col2:
        db_exists = os.path.exists(DB_PATH)
        st.metric("DB Status", "Ready" if db_exists else "Not Found")

    # Policy PDF generation
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Generate Policies", use_container_width=True):
            with st.spinner("Generating PDFs..."):
                generate_all_policies()
            st.success("Policies generated!")

    with col4:
        pdf_count = len([f for f in os.listdir(DOCS_DIR) if f.endswith(".pdf")]
                        ) if os.path.exists(DOCS_DIR) else 0
        st.metric("PDFs", pdf_count)

    # Vector store
    if st.button("Build Vector Store", use_container_width=True):
        if not api_key:
            st.error("Please set your OpenAI API key first.")
        else:
            with st.spinner("Building vector store..."):
                build_vector_store()
            st.success("Vector store ready!")

    vs_exists = (os.path.exists(VECTORSTORE_DIR) and os.listdir(VECTORSTORE_DIR)
                 if os.path.exists(VECTORSTORE_DIR) else False)
    st.metric("Vector Store", "Ready" if vs_exists else "Not Built")

    st.divider()

    # PDF Upload
    st.subheader("📄 Upload Policy PDFs")
    uploaded_files = st.file_uploader(
        "Upload additional policy documents",
        type=["pdf"],
        accept_multiple_files=True,
    )
    if uploaded_files:
        os.makedirs(DOCS_DIR, exist_ok=True)
        for uploaded_file in uploaded_files:
            filepath = os.path.join(DOCS_DIR, uploaded_file.name)
            with open(filepath, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Uploaded: {uploaded_file.name}")
        if api_key:
            with st.spinner("Re-indexing documents..."):
                build_vector_store()
            st.success("Vector store updated with new documents!")
        else:
            st.info("Click 'Build Vector Store' to index new documents.")

    st.divider()

    # Clear chat
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("Built with LangChain, LangGraph, ChromaDB & Streamlit")

# -- Main area --------------------------------------------------------------
st.title("🤖 TechCorp Customer Support AI")
st.caption("Ask about customer data, company policies, or get general support help. "
           "Supports follow-up questions with conversation context.")

# Quick-start buttons
st.markdown("**Try these example queries:**")
examples = [
    "What is the current refund policy?",
    "Give me a quick overview of customer Ema's profile and past support ticket details.",
    "List all open support tickets with their priorities.",
    "Does Ema qualify for a refund on her SmartDesk Hub based on our refund policy?",
    "How many Premium tier customers do we have?",
    "What data does TechCorp collect about users?",
]
cols = st.columns(3)
for i, example in enumerate(examples):
    with cols[i % 3]:
        if st.button(example, key=f"ex_{i}", use_container_width=True):
            st.session_state["prefill"] = example

# -- Chat -------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg.get("agent_label"):
            st.caption(f"Routed to: {msg['agent_label']}")
        st.markdown(msg["content"])

# Handle prefilled example
prefill = st.session_state.pop("prefill", None)
prompt = st.chat_input("Ask a question about customers, policies, or support...")

if prefill:
    prompt = prefill

if prompt:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()

    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build conversation history for context
    chat_history = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages[:-1]  # exclude current message
    ]

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
                graph = build_graph(llm)
                result = graph.invoke({
                    "question": prompt,
                    "chat_history": chat_history,
                    "route": "",
                    "sql_response": "",
                    "rag_response": "",
                    "response": "",
                })
                response = result["response"]
                route = result["route"]

                # Show which agent handled it
                agent_labels = {
                    "sql": "📊 SQL Agent (Customer Database)",
                    "rag": "📄 RAG Agent (Policy Documents)",
                    "hybrid": "📊📄 Hybrid (SQL + RAG Synthesis)",
                    "general": "💬 General Assistant",
                }
                agent_label = agent_labels.get(route, route)
                st.caption(f"Routed to: {agent_label}")
                st.markdown(response)
            except Exception as e:
                response = f"An error occurred: {str(e)}"
                route = "error"
                agent_label = ""
                st.error(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "agent_label": agent_label if route != "error" else "",
    })
