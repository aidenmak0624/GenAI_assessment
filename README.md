# TechCorp Customer Support AI -- Multi-Agent System

A **Generative AI-powered Multi-Agent System** that enables natural language interaction with both structured customer data (SQL) and unstructured policy documents (PDF). Built with **LangChain**, **LangGraph**, **ChromaDB**, and **Streamlit**, orchestrated via the **Model Context Protocol (MCP)**.

## Demo Video

🎥 **[Watch the demo video](https://your-demo-video-url-here)**

---

## Table of Contents

- [Architecture](#architecture)
- [Hybrid Query Flow](#hybrid-query-flow)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [MCP Server](#mcp-server)
- [Database Schema](#database-schema)
- [Document Chunking Strategy](#document-chunking-strategy)
- [Example Queries](#example-queries)
- [Architecture Decisions & Tradeoffs](#architecture-decisions--tradeoffs)
- [Evaluation & Testing](#evaluation--testing)
- [Limitations & Known Constraints](#limitations--known-constraints)

---

## Architecture

```
                    ┌──────────────────┐
                    │   Streamlit UI   │
                    │  (MCP Host)      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  LangGraph        │
                    │  Supervisor Router│
                    └──┬──┬──┬──┬──────┘
                       │  │  │  │
           ┌───────────┘  │  │  └───────────┐
           ▼              │  │              ▼
     ┌──────────┐         │  │        ┌──────────┐
     │ SQL Agent│         │  │        │ General  │
     │          │         │  │        │ Agent    │
     └────┬─────┘         │  │        └──────────┘
          │          ┌────┘  └────┐
          │          ▼            ▼
     ┌────▼─────┐ ┌──────────────────┐
     │  SQLite  │ │  Hybrid Path     │
     │ Database │ │  SQL + RAG       │
     └──────────┘ │  → Synthesizer   │
                  └───────┬──────────┘
                          │
                  ┌───────▼──────────┐
                  │    RAG Agent     │
                  └───────┬──────────┘
                          │
                  ┌───────▼──────────┐
                  │    ChromaDB      │
                  │    VectorDB      │
                  └──────────────────┘
```

### How It Works

1. The user submits a natural language query through the Streamlit UI (or MCP client).
2. The **LangGraph Supervisor Router** classifies the query into one of four categories:
   - **SQL** → routes to the SQL Agent for structured database queries.
   - **RAG** → routes to the RAG Agent for policy document search.
   - **Hybrid** → invokes **both** the SQL Agent and RAG Agent sequentially, then a **Synthesizer Agent** combines both results into a single coherent answer.
   - **General** → routes to the General Agent for greetings / general help.
3. **Conversation context** from previous turns is passed to agents, enabling follow-up questions (e.g., "What about her last order?" after asking about Ema).
4. The response is returned with an indicator showing which agent(s) handled the query.

---

## Hybrid Query Flow

A key differentiator of this system is its ability to handle queries that require **both structured data and policy knowledge**. Here is a concrete example:

**User asks:** *"Does Ema qualify for a refund on her SmartDesk Hub based on our refund policy?"*

```
Step 1: Router detects the query needs BOTH customer data and policy → routes to "hybrid"

Step 2: SQL Agent retrieves Ema's order data:
        SELECT o.*, p.product_name, p.category, c.membership_tier
        FROM orders o
        JOIN products p ON o.product_id = p.product_id
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE c.first_name = 'Ema' AND p.product_name LIKE '%SmartDesk%'
        → Result: Ema ordered SmartDesk Hub on 2023-06-15, status: Delivered,
          she's a Premium member.

Step 3: RAG Agent retrieves refund policy:
        → Relevant chunks: "Hardware products may be returned within 30 days
          of delivery..." and "Service plans are eligible for prorated refunds..."

Step 4: Synthesizer Agent combines both:
        → "Based on Ema's order records, she purchased a SmartDesk Hub on
           June 15, 2023 (Delivered). According to our refund policy, hardware
           products may be returned within 30 days of delivery. Since this is
           well past the 30-day window, Ema would not qualify for a standard
           refund. However, she may be eligible for a warranty claim if the
           product is defective, as all hardware includes a 1-year warranty."
```

This flow demonstrates true **multi-agent coordination** -- not just routing to a single agent, but orchestrating multiple agents and synthesizing their outputs.

---

## Features

- **Natural language SQL queries** -- ask about customers, orders, and support tickets in plain English. The SQL Agent translates questions to SQL, validates for safety (read-only), executes, and summarizes results.
- **PDF policy document search** -- upload company policy PDFs, which are chunked, embedded, and stored in ChromaDB. The RAG Agent retrieves relevant sections with source citations.
- **Hybrid multi-agent reasoning** -- queries that span both structured data and policy documents invoke both agents and synthesize a unified answer.
- **Conversation context** -- follow-up questions are resolved using previous conversation turns (e.g., "What about her last ticket?" after asking about Ema).
- **Intelligent routing** -- LangGraph-based supervisor automatically detects query intent and routes to the correct agent(s).
- **MCP Server** -- FastMCP-based server exposing all agents as tools for integration with any MCP-compatible client.
- **SQL safety** -- generated SQL is validated to be read-only before execution; destructive operations are rejected.
- **Interactive UI** -- Streamlit chat interface with example queries, PDF upload, auto-indexing, and system setup controls.

---

## Technology Stack

| Component           | Technology                      | Purpose                                       |
|---------------------|---------------------------------|-----------------------------------------------|
| Orchestration       | LangGraph                       | Multi-agent state graph with conditional routing |
| LLM Framework       | LangChain                       | Agent abstractions and prompt management       |
| LLM                 | OpenAI GPT-4o-mini              | Query routing, SQL generation, answer synthesis |
| Embeddings          | OpenAI text-embedding-3-small   | Document chunk vectorization                   |
| Structured DB       | SQLite                          | Customer profiles, orders, support tickets     |
| Vector DB           | ChromaDB                        | Semantic search over policy documents          |
| PDF Processing      | PyMuPDF (fitz)                  | Text extraction from uploaded/generated PDFs   |
| MCP Server          | FastMCP                         | Standardized tool exposure via MCP protocol    |
| UI                  | Streamlit                       | Chat interface with session state management   |
| PDF Generation      | ReportLab                       | Generate synthetic sample policy PDFs for demo |

---

## Project Structure

```
├── README.md                  # This file
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── setup.py                   # One-command setup script
├── app.py                     # Streamlit UI application
│
├── agents/
│   ├── __init__.py
│   ├── graph.py               # LangGraph multi-agent orchestrator (router + hybrid path)
│   ├── sql_agent.py           # SQL agent (NL → SQL → validate → execute → NL)
│   └── rag_agent.py           # RAG agent (semantic search over policy documents)
│
├── data/
│   ├── __init__.py
│   ├── init_db.py             # SQLite database initialization + seed data
│   └── generate_policies.py   # Generate sample policy PDFs with ReportLab
│
├── docs/                      # Policy PDF documents (generated / uploaded)
│
├── mcp_server/
│   ├── __init__.py
│   └── server.py              # FastMCP server with tool endpoints
│
└── utils/
    ├── __init__.py
    └── vector_store.py        # ChromaDB vector store management
```

---

## Setup & Installation

### Prerequisites

- Python 3.10+
- An OpenAI API key

### 1. Clone the repository

```bash
git clone https://github.com/aidenmak0624/GenAI_assessment.git
cd GenAI_assessment
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set your API key

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 5. Run the setup script

This initializes the SQLite database with synthetic data, generates sample policy PDFs, and builds the vector store:

```bash
python setup.py
```

### 6. Launch the application

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## Usage

### Streamlit UI

1. **Enter your OpenAI API key** in the sidebar (or set it in `.env`).
2. **Click "Full Setup"** to initialize the database, generate policy PDFs, and build the vector store in one step.
3. **Start chatting!** Ask questions in the chat input or click the example query buttons.
4. **Upload custom PDFs** via the sidebar -- they are automatically re-indexed.
5. **Ask follow-up questions** -- the system preserves conversation context (e.g., ask about Ema, then say "What was her last order?").

### Upload Custom Policy Documents

Use the file uploader in the sidebar to add your own PDF policy documents. The system automatically re-indexes the vector store after upload.

---

## MCP Server

The project includes a **FastMCP server** that exposes the multi-agent system as tools via the Model Context Protocol. This allows any MCP-compatible client to interact with the system.

### Why MCP?

MCP provides a standardized interface for AI tool discovery and invocation. Instead of hard-coding tool integrations, the MCP server:
- **Exposes tools with JSON Schema** -- clients automatically discover available tools and their parameters.
- **Decouples the agent logic from the client** -- the same server works with Claude Desktop, IDE extensions, or custom applications.
- **Enables extensibility** -- new tools (e.g., a shipping API) can be added to the server without modifying any client code.

In this architecture, the **Streamlit app acts as the MCP Host**, while the FastMCP server provides an alternative integration path for programmatic or external clients.

### Running the MCP Server

```bash
python mcp_server/server.py
```

### Available Tools

| Tool                    | Description                                      |
|-------------------------|--------------------------------------------------|
| `query_customer_data`   | Query customer profiles, orders, tickets via NL   |
| `search_policies`       | Search policy documents via NL                    |
| `customer_support_chat` | Auto-routed support (SQL, RAG, hybrid, or general) with optional conversation history |

### MCP Configuration

To use with an MCP-compatible client, add to your MCP config:

```json
{
  "mcpServers": {
    "customer-support": {
      "command": "python",
      "args": ["mcp_server/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-api-key"
      }
    }
  }
}
```

---

## Database Schema

The SQLite database contains four relational tables with the following structure:

### customers
| Column           | Type    | Description                           |
|------------------|---------|---------------------------------------|
| customer_id      | INTEGER | Primary key                           |
| first_name       | TEXT    | Customer first name                   |
| last_name        | TEXT    | Customer last name                    |
| email            | TEXT    | Unique email address                  |
| phone            | TEXT    | Phone number                          |
| address          | TEXT    | Street address                        |
| city             | TEXT    | City                                  |
| country          | TEXT    | Country                               |
| membership_tier  | TEXT    | Standard, Premium, or Gold            |
| account_created  | DATE    | Account creation date                 |
| is_active        | BOOLEAN | Whether the account is active         |

### products
| Column       | Type    | Description                              |
|--------------|---------|------------------------------------------|
| product_id   | INTEGER | Primary key                              |
| product_name | TEXT    | Product name                             |
| category     | TEXT    | Software, Hardware, or Service           |
| price        | REAL    | Unit price                               |
| description  | TEXT    | Product description                      |

### orders
| Column       | Type    | Description                              |
|--------------|---------|------------------------------------------|
| order_id     | INTEGER | Primary key                              |
| customer_id  | INTEGER | FK → customers                           |
| product_id   | INTEGER | FK → products                            |
| order_date   | DATE    | Date of order                            |
| quantity     | INTEGER | Items ordered                            |
| total_amount | REAL    | Total order value                        |
| status       | TEXT    | Delivered, Active, Cancelled, Completed  |

### support_tickets
| Column           | Type     | Description                          |
|------------------|----------|--------------------------------------|
| ticket_id        | INTEGER  | Primary key                          |
| customer_id      | INTEGER  | FK → customers                       |
| subject          | TEXT     | Ticket subject                       |
| description      | TEXT     | Issue description                    |
| category         | TEXT     | Technical, Billing, Hardware, Feature Request |
| priority         | TEXT     | Critical, High, Medium, Low          |
| status           | TEXT     | Open, Resolved, Closed               |
| created_at       | DATETIME | Ticket creation timestamp            |
| resolved_at      | DATETIME | Resolution timestamp (nullable)      |
| resolution_notes | TEXT     | How the issue was resolved           |
| assigned_agent   | TEXT     | Support agent handling the ticket    |

### Relationships
```
customers 1──┬──* orders
             │
             └──* support_tickets

products 1────* orders
```

The database is seeded with **10 customers**, **10 products**, **22 orders**, and **16 support tickets**.

---

## Document Chunking Strategy

Policy PDFs are processed through the following pipeline:

1. **Text extraction**: PyMuPDF extracts all text from each PDF page.
2. **Chunking**: Documents are split using `RecursiveCharacterTextSplitter` with:
   - **Chunk size**: 800 characters -- balances granularity with sufficient context per chunk.
   - **Chunk overlap**: 150 characters (~19%) -- ensures semantic continuity at chunk boundaries.
   - **Separators**: `["\n\n", "\n", ". ", " ", ""]` -- splits preferentially at paragraph/sentence boundaries.
3. **Metadata**: Each chunk retains source filename and document type for citation in responses.
4. **Embedding**: Chunks are embedded using OpenAI `text-embedding-3-small` (1536 dimensions).
5. **Storage**: Embeddings are stored in ChromaDB with cosine similarity search.
6. **Retrieval**: Top 4 most similar chunks are retrieved per query (k=4).

---

## Example Queries

### Structured Data (SQL Agent)

- *"Give me a quick overview of customer Ema's profile and past support ticket details."*
- *"What orders has Liam Smith placed?"*
- *"List all open support tickets with their priorities."*
- *"How many Premium tier customers do we have?"*
- *"What is the total revenue from hardware products?"*

### Policy Documents (RAG Agent)

- *"What is the current refund policy?"*
- *"What are the support SLA response times for Premium customers?"*
- *"How long does TechCorp retain customer data?"*
- *"What data does TechCorp collect about users?"*
- *"How do I escalate a support ticket?"*

### Hybrid Queries (SQL + RAG)

- *"Does Ema qualify for a refund on her SmartDesk Hub based on our refund policy?"*
- *"What support SLA applies to Liam given his membership tier?"*
- *"Check Sophia's ticket history and tell me if her escalation follows policy."*

### Follow-up Questions (Context-Aware)

1. *"Tell me about customer Ema Johnson."* → SQL Agent retrieves Ema's profile
2. *"What about her support tickets?"* → SQL Agent resolves "her" as Ema from context
3. *"Is she eligible for a refund?"* → Hybrid route: checks her orders + refund policy

---

## Architecture Decisions & Tradeoffs

| Decision                          | Rationale                                                    |
|-----------------------------------|--------------------------------------------------------------|
| **LangGraph over LangChain Agents** | LangGraph's state graph with conditional edges gives explicit control over routing and supports cyclic/hybrid flows. Standard LangChain agents lack the deterministic routing needed for the supervisor pattern. |
| **Supervisor routing (not swarm)** | For a customer support use case, a central router provides predictable behavior and clear auditability. Peer-to-peer "swarm" coordination adds complexity without proportional benefit here. |
| **SQLite over PostgreSQL**        | Simplifies setup (no external DB server). For a demo/assessment, SQLite is sufficient. Production would use PostgreSQL with connection pooling. |
| **ChromaDB over FAISS/Pinecone**  | ChromaDB provides persistent storage with a simple API and runs locally. FAISS lacks persistence; Pinecone requires a cloud account. |
| **GPT-4o-mini for all agents**    | Cost-effective for routing, SQL generation, and summarization. GPT-4o could improve accuracy on complex SQL but at ~15x the cost. The router task is simple enough for the mini model. |
| **FastMCP for the MCP server**    | FastMCP provides a minimal, Pythonic way to define MCP tools. It handles JSON-RPC transport and tool schema generation automatically. |
| **Read-only SQL validation**      | Regex-based validation rejects any non-SELECT queries before execution. This is a defense-in-depth measure alongside the LLM prompt instructions. |
| **Sequential hybrid (not parallel)** | The hybrid path runs SQL → RAG → Synthesize sequentially. While parallel execution would be faster, sequential flow is simpler to debug and the latency difference is marginal for this use case. |

---

## Evaluation & Testing

### Sample Test Scenarios

| # | Query | Expected Behavior | Agent(s) |
|---|-------|-------------------|----------|
| 1 | "What is the refund policy?" | Returns summary of refund eligibility, timelines, non-refundable items from refund_policy.pdf | RAG |
| 2 | "Show me Ema Johnson's profile" | Returns Ema's full profile (email, tier, city, etc.) from customers table | SQL |
| 3 | "List all open support tickets" | Returns 4 open tickets with subjects, priorities, and assigned agents | SQL |
| 4 | "Does Ema qualify for a refund on her SmartDesk Hub?" | Retrieves Ema's order history AND refund policy, synthesizes eligibility answer | Hybrid |
| 5 | "How long is customer data retained?" | Returns "2 years after account closure" from privacy_policy.pdf | RAG |
| 6 | "Hello!" | Friendly greeting response | General |
| 7 | "What was her last order?" (after asking about Ema) | Correctly resolves "her" to Ema using conversation context | SQL |
| 8 | "How many Gold tier customers are there?" | Returns count (3) from customers table | SQL |
| 9 | "What SLA applies to Liam's tickets given his tier?" | Retrieves Liam's tier (Standard) and support SLA policy for that tier | Hybrid |
| 10 | "What are the non-refundable items?" | Returns list from refund_policy.pdf (setup services, downloaded software, etc.) | RAG |

### Quality Measures

- **SQL safety**: All generated SQL is validated as read-only (SELECT only) before execution. Destructive queries are blocked.
- **Hallucination mitigation**: The RAG agent is instructed to answer strictly from provided context and to explicitly state when information is insufficient.
- **Source citations**: RAG responses include the source document filename so John can verify the information.
- **Graceful error handling**: SQL errors return the generated query for debugging. Missing vector store returns a clear setup prompt.

---

## Limitations & Known Constraints

- **Synthetic dataset only** -- the seeded data covers 10 customers, 10 products, 22 orders, and 16 support tickets. Real-world deployment would need production data pipelines.
- **PDF extraction quality** -- text extraction depends on PDF structure. Scanned PDFs (image-based) would require OCR preprocessing not included here.
- **SQL generation accuracy** -- GPT-4o-mini handles straightforward queries well but may struggle with complex multi-join aggregations or ambiguous column references.
- **No authentication / RBAC** -- the system has no user authentication. In production, access to customer data would require role-based access controls.
- **Single-user session** -- Streamlit session state is per-browser-tab. There is no multi-user session management or persistent conversation storage.
- **Embedding cost** -- rebuilding the vector store re-embeds all documents. Incremental indexing is not implemented.
- **Schema is fixed** -- the SQL agent's schema description is hardcoded. Schema changes require updating the agent prompt.
- **No real-time data** -- customer data is static after seeding. There is no live sync with external systems.
- **Best for support lookup, not compliance decisions** -- responses should be verified by a human before taking action on policy-sensitive matters.

---

## License

This project is for assessment/demonstration purposes.
