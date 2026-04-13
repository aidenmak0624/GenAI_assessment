"""
MCP Server for the Customer Support Multi-Agent System.

Exposes tools for:
  - Querying customer data (SQL agent)
  - Searching policy documents (RAG agent)
  - General customer support chat (auto-routed via LangGraph)

The MCP Server acts as a standardized interface allowing any MCP-compatible
client (Claude Desktop, IDE extensions, custom apps) to interact with the
multi-agent system through a uniform tool discovery and invocation protocol.
"""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from fastmcp import FastMCP
from langchain_openai import ChatOpenAI

from agents.sql_agent import answer_sql_question
from agents.rag_agent import answer_rag_question
from agents.graph import ask

mcp = FastMCP("Customer Support AI")


def _get_llm():
    """Lazy LLM initialization (avoids error when API key not yet set)."""
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


@mcp.tool()
def query_customer_data(question: str) -> str:
    """Query structured customer data (profiles, orders, support tickets)
    using natural language.

    Examples:
        - "Show me Ema Johnson's profile"
        - "What are Liam's recent orders?"
        - "List all open support tickets"
        - "How many premium customers do we have?"
    """
    return answer_sql_question(question, _get_llm())


@mcp.tool()
def search_policies(question: str) -> str:
    """Search company policy documents (refund, privacy, support policies)
    using natural language.

    Examples:
        - "What is the refund policy for hardware?"
        - "How long is data retained?"
        - "What are the support SLA times?"
    """
    return answer_rag_question(question, _get_llm())


@mcp.tool()
def customer_support_chat(question: str, chat_history: str = "") -> str:
    """General customer support assistant that automatically routes your
    question to the right agent (SQL, policy search, hybrid, or general).

    This is the main entry point. It will figure out whether you need
    database info, policy info, both (hybrid), or just a general answer.

    Supports conversation context -- pass prior messages in chat_history
    as a string of "User: ... / Assistant: ..." lines.
    """
    history = []
    if chat_history:
        for line in chat_history.strip().split("\n"):
            line = line.strip()
            if line.startswith("User:"):
                history.append({"role": "user", "content": line[5:].strip()})
            elif line.startswith("Assistant:"):
                history.append({"role": "assistant", "content": line[10:].strip()})

    result = ask(question, _get_llm(), chat_history=history)
    return result["response"]


if __name__ == "__main__":
    mcp.run()
