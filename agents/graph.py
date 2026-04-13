"""
LangGraph Multi-Agent Orchestrator.

Routes user queries to the appropriate agent(s):
  - SQL Agent: for structured customer data queries
  - RAG Agent: for policy document questions
  - Hybrid: invokes both SQL + RAG and synthesizes results
  - General: for greetings and general conversation

Supports conversation context for follow-up questions.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


from agents.sql_agent import answer_sql_question
from agents.rag_agent import answer_rag_question


# -- State ------------------------------------------------------------------
class AgentState(TypedDict):
    question: str
    chat_history: list[dict]  # previous turns for context
    route: str
    sql_response: str
    rag_response: str
    response: str


# -- Router -----------------------------------------------------------------
ROUTER_PROMPT = """You are a query router for a customer support system.
Classify the user's message into exactly one category:

- "sql" -- if the question asks about specific customer data, profiles, orders,
  support tickets, product info, or anything stored in a database.
  Examples: "Show me Ema's profile", "What orders did Liam place?",
  "List open support tickets", "How many premium customers are there?"

- "rag" -- if the question is about company policies, procedures, terms,
  refund policy, privacy policy, support SLAs, or general company rules.
  Examples: "What is the refund policy?", "How do I escalate a ticket?",
  "What data does TechCorp collect?"

- "hybrid" -- if the question requires BOTH customer data AND policy knowledge.
  Examples: "Does Ema qualify for a refund based on her order history and the refund policy?",
  "What support SLA applies to Liam given his membership tier?",
  "Check Sophia's ticket history and tell me if her escalation follows policy."

- "general" -- greetings, thanks, or questions unrelated to customer data
  or company policy.

Respond with ONLY one word: sql, rag, hybrid, or general.
"""


def _build_context_prefix(chat_history: list[dict]) -> str:
    """Build a conversation context string from chat history."""
    if not chat_history:
        return ""
    lines = []
    for msg in chat_history[-6:]:  # last 3 exchanges
        role = msg.get("role", "user")
        lines.append(f"{role.capitalize()}: {msg['content']}")
    return "Previous conversation:\n" + "\n".join(lines) + "\n\n"


def route_query(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Classify the user question and set the route."""
    context = _build_context_prefix(state.get("chat_history", []))
    user_msg = context + f"Current question: {state['question']}"

    response = llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=user_msg),
    ])
    route = response.content.strip().lower()
    if route not in ("sql", "rag", "hybrid", "general"):
        route = "general"
    return {**state, "route": route}


# -- Agent nodes ------------------------------------------------------------
def sql_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    context = _build_context_prefix(state.get("chat_history", []))
    question = context + state["question"] if context else state["question"]
    answer = answer_sql_question(question, llm)
    return {**state, "sql_response": answer}


def rag_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    context = _build_context_prefix(state.get("chat_history", []))
    question = context + state["question"] if context else state["question"]
    answer = answer_rag_question(question, llm)
    return {**state, "rag_response": answer}


def hybrid_sql_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """SQL retrieval step for hybrid queries."""
    context = _build_context_prefix(state.get("chat_history", []))
    question = context + state["question"] if context else state["question"]
    answer = answer_sql_question(question, llm)
    return {**state, "sql_response": answer}


def hybrid_rag_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """RAG retrieval step for hybrid queries."""
    context = _build_context_prefix(state.get("chat_history", []))
    question = context + state["question"] if context else state["question"]
    answer = answer_rag_question(question, llm)
    return {**state, "rag_response": answer}


SYNTHESIZER_PROMPT = """You are a customer support assistant for TechCorp.
You have been given information from two sources:

1. CUSTOMER DATABASE RESULTS (structured data about customers, orders, tickets):
{sql_response}

2. POLICY DOCUMENT RESULTS (company policies, procedures, terms):
{rag_response}

Using BOTH sources, provide a comprehensive, accurate answer to the user's question.
Clearly indicate which information comes from customer records vs. company policy.
Be concise but thorough. Use a friendly, professional tone."""


def synthesize_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Combine SQL and RAG results into a single coherent answer."""
    prompt = SYNTHESIZER_PROMPT.format(
        sql_response=state.get("sql_response", "No data retrieved."),
        rag_response=state.get("rag_response", "No policy information found."),
    )
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=state["question"]),
    ])
    return {**state, "response": response.content}


def sql_finalize(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Copy sql_response to response for single-agent routes."""
    return {**state, "response": state.get("sql_response", "")}


def rag_finalize(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Copy rag_response to response for single-agent routes."""
    return {**state, "response": state.get("rag_response", "")}


def general_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    context = _build_context_prefix(state.get("chat_history", []))
    response = llm.invoke([
        SystemMessage(content="You are a friendly customer support assistant for "
                      "TechCorp. Respond helpfully to greetings, thanks, and "
                      "general queries. Keep responses concise."),
        HumanMessage(content=context + state["question"]),
    ])
    return {**state, "response": response.content}


# -- Conditional edges ------------------------------------------------------
def pick_agent(state: AgentState) -> Literal["sql_agent", "rag_agent",
                                              "hybrid_sql", "general_agent"]:
    mapping = {
        "sql": "sql_agent",
        "rag": "rag_agent",
        "hybrid": "hybrid_sql",
    }
    return mapping.get(state["route"], "general_agent")


# -- Build graph ------------------------------------------------------------
def build_graph(llm: ChatOpenAI | None = None):
    """Construct and compile the LangGraph agent graph."""
    if llm is None:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    graph = StateGraph(AgentState)

    # Add nodes (wrap with llm via closures)
    graph.add_node("router", lambda s: route_query(s, llm))
    graph.add_node("sql_agent", lambda s: sql_node(s, llm))
    graph.add_node("rag_agent", lambda s: rag_node(s, llm))
    graph.add_node("general_agent", lambda s: general_node(s, llm))

    # SQL / RAG single-agent finalize nodes
    graph.add_node("sql_finalize", lambda s: sql_finalize(s, llm))
    graph.add_node("rag_finalize", lambda s: rag_finalize(s, llm))

    # Hybrid path: SQL -> RAG -> Synthesize
    graph.add_node("hybrid_sql", lambda s: hybrid_sql_node(s, llm))
    graph.add_node("hybrid_rag", lambda s: hybrid_rag_node(s, llm))
    graph.add_node("synthesize", lambda s: synthesize_node(s, llm))

    # Entry
    graph.set_entry_point("router")

    # Router -> agents
    graph.add_conditional_edges("router", pick_agent,
                                 {"sql_agent": "sql_agent",
                                  "rag_agent": "rag_agent",
                                  "hybrid_sql": "hybrid_sql",
                                  "general_agent": "general_agent"})

    # Single-agent paths -> finalize -> END
    graph.add_edge("sql_agent", "sql_finalize")
    graph.add_edge("sql_finalize", END)

    graph.add_edge("rag_agent", "rag_finalize")
    graph.add_edge("rag_finalize", END)

    graph.add_edge("general_agent", END)

    # Hybrid path: SQL -> RAG -> Synthesize -> END
    graph.add_edge("hybrid_sql", "hybrid_rag")
    graph.add_edge("hybrid_rag", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


def ask(question: str, llm: ChatOpenAI | None = None,
        chat_history: list[dict] | None = None) -> dict:
    """Run a question through the full agent graph.

    Returns dict with 'response' and 'route' keys.
    """
    app = build_graph(llm)
    result = app.invoke({
        "question": question,
        "chat_history": chat_history or [],
        "route": "",
        "sql_response": "",
        "rag_response": "",
        "response": "",
    })
    return {"response": result["response"], "route": result["route"]}
