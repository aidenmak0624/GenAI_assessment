"""
LangGraph Multi-Agent Orchestrator.

Routes user queries to the appropriate agent(s):
  - SQL Agent: for structured customer data queries
  - RAG Agent: for policy document questions
  - Hybrid: invokes both SQL + RAG and synthesizes results
  - General: for greetings and general conversation

Supports conversation context for follow-up questions.
"""

import re
from datetime import date
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


from agents.sql_agent import answer_sql_question, answer_sql_facts_question
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
  support tickets, product info, pricing, services, or anything that could be
  answered from a database. This includes questions about what products or
  services the company offers.
  Examples: "Show me Ema's profile", "What orders did Liam place?",
  "List open support tickets", "How many premium customers are there?",
  "What is TechCare?", "Show me all products", "What services do you offer?"

- "rag" -- if the question is about company policies, procedures, terms,
  refund policy, privacy policy, support SLAs, or general company rules.
  Examples: "What is the refund policy?", "How do I escalate a ticket?",
  "What data does TechCorp collect?"

- "hybrid" -- if the question requires BOTH customer data AND policy knowledge.
  Examples: "Does Ema qualify for a refund based on her order history and the refund policy?",
  "What support SLA applies to Liam given his membership tier?",
  "Check Sophia's ticket history and tell me if her escalation follows policy."

- "general" -- ONLY for greetings, thanks, or questions completely unrelated
  to customer data, products, services, or company policy. When in doubt
  between "general" and another category, choose the other category.

Respond with ONLY one word: sql, rag, hybrid, or general.
"""

SQL_HINT_TERMS = {
    "customer", "profile", "order", "orders", "ticket", "tickets", "support ticket",
    "membership", "tier", "database", "sql", "account", "accounts", "revenue",
    "premium", "gold", "standard", "email", "phone", "address",
}
CATALOG_SQL_HINT_TERMS = {
    "what products", "show me all products", "list products", "all products",
    "what services", "services do you offer", "list services", "pricing",
    "price list", "product catalog", "service catalog",
}
RAG_HINT_TERMS = {
    "policy", "policies", "refund", "return", "privacy", "retention", "document",
    "documents", "sla", "support plan", "support plans", "coverage", "warranty",
    "restocking", "terms", "procedure", "procedures",
}
HYBRID_HINT_TERMS = {
    "qualify", "eligible", "still qualify", "still be within", "inside the return window",
}
FOLLOW_UP_HINT_PATTERN = (
    r"\b(it|they|them|their|he|him|his|she|her|hers|that|those|these|this)\b"
    r"|what about|how about|that order|the policy|the ticket|the customer"
    r"|the account|that customer|that ticket|that product|that policy"
)


def _keyword_route(question: str) -> str | None:
    """Apply simple deterministic routing for obvious cases before using the LLM."""
    lowered = question.lower()
    has_sql = any(term in lowered for term in SQL_HINT_TERMS)
    has_catalog_sql = any(term in lowered for term in CATALOG_SQL_HINT_TERMS)
    has_rag = any(term in lowered for term in RAG_HINT_TERMS)
    has_hybrid = any(term in lowered for term in HYBRID_HINT_TERMS)

    if has_rag and (has_sql or has_hybrid):
        return "hybrid"
    if has_rag:
        return "rag"
    if has_sql or has_catalog_sql:
        return "sql"
    return None


def _build_context_prefix(chat_history: list[dict]) -> str:
    """Build a conversation context string from chat history."""
    if not chat_history:
        return ""
    lines = []
    for msg in chat_history[-6:]:  # last 3 exchanges
        role = msg.get("role", "user")
        lines.append(f"{role.capitalize()}: {msg['content']}")
    return "Previous conversation:\n" + "\n".join(lines) + "\n\n"


def _needs_question_rewrite(question: str) -> bool:
    """Only rewrite follow-ups that rely on earlier context."""
    return bool(re.search(FOLLOW_UP_HINT_PATTERN, question.lower()))


QUESTION_REWRITE_PROMPT = """Rewrite the user's current message into a standalone
question using the recent conversation only when needed.

Rules:
- Preserve the user's original intent exactly.
- Resolve pronouns or vague references such as "her", "his", "that order",
  or "the policy" using recent conversation when needed.
- Remove unrelated details from earlier turns.
- If the current question is already standalone, return it unchanged.
- Do not answer the question.
- Return ONLY the rewritten standalone question.
"""


def _rewrite_question_with_history(
    question: str,
    chat_history: list[dict],
    llm: ChatOpenAI,
) -> str:
    """Resolve follow-up references without polluting retrieval with raw chat history."""
    if not chat_history or not _needs_question_rewrite(question):
        return question

    context = _build_context_prefix(chat_history)
    response = llm.invoke([
        SystemMessage(content=QUESTION_REWRITE_PROMPT),
        HumanMessage(content=context + f"Current question: {question}"),
    ])
    rewritten = response.content.strip()
    return rewritten or question


def route_query(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Classify the user question and set the route."""
    rewritten_question = _rewrite_question_with_history(
        state["question"],
        state.get("chat_history", []),
        llm,
    )
    heuristic_route = _keyword_route(rewritten_question)
    if heuristic_route is not None:
        return {**state, "route": heuristic_route}

    user_msg = f"Current question: {rewritten_question}"

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
    question = _rewrite_question_with_history(
        state["question"],
        state.get("chat_history", []),
        llm,
    )
    answer = answer_sql_question(question, llm)
    return {**state, "sql_response": answer}


def rag_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    question = _rewrite_question_with_history(
        state["question"],
        state.get("chat_history", []),
        llm,
    )
    answer = answer_rag_question(question, llm)
    return {**state, "rag_response": answer}


def hybrid_sql_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """SQL retrieval step for hybrid queries."""
    question = _rewrite_question_with_history(
        state["question"],
        state.get("chat_history", []),
        llm,
    )
    answer = answer_sql_facts_question(question, llm)
    return {**state, "sql_response": answer}


HYBRID_POLICY_REWRITE_PROMPT = """Rewrite the user's request into a standalone
policy-document search query.

Rules:
- Keep only the policy topic or rule that needs to be looked up in documents.
- Remove customer names, emails, order ids, ticket ids, and database-specific wording.
- Prefer general policy wording such as return window, refund eligibility,
  privacy retention, support SLA, escalation rules, or warranty coverage.
- Return ONLY the rewritten query.
"""


def _rewrite_hybrid_policy_question(question: str, llm: ChatOpenAI) -> str:
    """Focus hybrid policy lookups on the document-side rule instead of customer facts."""
    response = llm.invoke([
        SystemMessage(content=HYBRID_POLICY_REWRITE_PROMPT),
        HumanMessage(content=question),
    ])
    rewritten = response.content.strip()
    return rewritten or question


def hybrid_rag_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """RAG retrieval step for hybrid queries."""
    question = _rewrite_question_with_history(
        state["question"],
        state.get("chat_history", []),
        llm,
    )
    policy_question = _rewrite_hybrid_policy_question(question, llm)
    answer = answer_rag_question(policy_question, llm)
    return {**state, "rag_response": answer}


SYNTHESIZER_PROMPT = """You are a customer support assistant for TechCorp.
You have been given information from two sources:

1. CUSTOMER DATABASE RESULTS (structured data about customers, orders, tickets):
{sql_response}

2. POLICY DOCUMENT RESULTS (company policies, procedures, terms):
{rag_response}

Today is {today}.

Using BOTH sources, provide a comprehensive, accurate answer to the user's question.
Clearly indicate which information comes from customer records vs. company policy.
Be concise but thorough. Use a friendly, professional tone.
Treat dates in the database as literal facts and compare them against the policy windows.
Never describe an old purchase as recent. If a policy gives a 15/30/45-day window and
the customer order date is clearly older than that relative to today, say the customer
is outside the documented return window.
If the policy evidence is general rather than product-specific, state that clearly.
Preserve the explicit source details already included in the agent outputs.
End with a '---' divider followed by a short '**Source Details:**' section that
summarizes the database trace and the policy file/page/line references you used."""


def synthesize_node(state: AgentState, llm: ChatOpenAI) -> AgentState:
    """Combine SQL and RAG results into a single coherent answer."""
    prompt = SYNTHESIZER_PROMPT.format(
        sql_response=state.get("sql_response", "No data retrieved."),
        rag_response=state.get("rag_response", "No policy information found."),
        today=date.today().isoformat(),
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
