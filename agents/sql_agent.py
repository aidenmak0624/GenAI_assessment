"""
SQL Agent -- handles natural language queries against the customer database.

Includes read-only SQL validation to prevent destructive operations.
"""

import re
import sqlite3
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "data", "customer_support.db")

SCHEMA_DESCRIPTION = """
Database schema:

TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT, last_name TEXT, email TEXT UNIQUE,
    phone TEXT, address TEXT, city TEXT, country TEXT,
    membership_tier TEXT ('Standard','Premium','Gold'),
    account_created DATE, is_active BOOLEAN
)

TABLE products (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT, category TEXT ('Software','Hardware','Service'),
    price REAL, description TEXT
)

TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers,
    product_id INTEGER REFERENCES products,
    order_date DATE, quantity INTEGER, total_amount REAL,
    status TEXT ('Delivered','Active','Cancelled','Completed')
)

TABLE support_tickets (
    ticket_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers,
    subject TEXT, description TEXT,
    category TEXT ('Technical','Billing','Hardware','Feature Request'),
    priority TEXT ('Critical','High','Medium','Low'),
    status TEXT ('Open','Resolved','Closed'),
    created_at DATETIME, resolved_at DATETIME,
    resolution_notes TEXT, assigned_agent TEXT
)
"""

SQL_SYSTEM_PROMPT = f"""You are a SQL expert. Given a natural language question about
customer support data, generate a valid SQLite query to answer it.

{SCHEMA_DESCRIPTION}

Rules:
- Return ONLY the SQL query, no explanation, no markdown fences.
- Use JOINs when data spans multiple tables.
- Always limit results to 20 rows max unless the user asks for more.
- Use LIKE with % for partial name matching (case-insensitive).
- For customer lookups by name, search both first_name and last_name.
- ONLY generate SELECT statements. Never generate INSERT, UPDATE, DELETE, DROP,
  ALTER, CREATE, or any other data-modifying statements.
"""

# Dangerous SQL patterns (case-insensitive)
_DANGEROUS_SQL = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|EXEC|EXECUTE|GRANT|REVOKE)\b',
    re.IGNORECASE,
)


def validate_sql_readonly(sql: str) -> bool:
    """Return True if the SQL is a safe read-only query."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        return False
    if _DANGEROUS_SQL.search(stripped):
        return False
    return True


def run_sql_query(query: str) -> list[dict]:
    """Execute a SQL query and return results as list of dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()
    return rows


def generate_sql(question: str, llm: ChatOpenAI) -> str:
    """Use the LLM to convert a natural language question to SQL."""
    response = llm.invoke([
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ])
    sql = response.content.strip()
    # Strip markdown fences if present
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1] if "\n" in sql else sql[3:]
        # Remove optional language tag (e.g. "sql\n") after the opening fence
        if sql.lower().startswith("sql"):
            sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    sql = sql.strip()
    return sql


def _tables_used_from_sql(sql: str) -> list[str]:
    """Extract known table names mentioned in the generated SQL."""
    tables_used = []
    lowered = sql.lower()
    for table_name in ["customers", "products", "orders", "support_tickets"]:
        if table_name in lowered:
            tables_used.append(table_name)
    return tables_used


def _format_sql_source(sql: str, tables_used: list[str], row_count: int) -> str:
    """Create a deterministic SQL trace footer for the user-facing answer."""
    table_refs = ", ".join(f"`{table}`" for table in tables_used) if tables_used else "`unknown`"
    compact_sql = " ".join(sql.split())
    return (
        f"**Source:** {table_refs} ({row_count} row{'s' if row_count != 1 else ''} returned)\n"
        f"**SQL:** `{compact_sql}`"
    )


def _format_sql_facts(results: list[dict]) -> str:
    """Format SQL rows deterministically for hybrid reasoning."""
    if not results:
        return "**Database Facts:** No matching customer records were found."

    lines = ["**Database Facts:**"]
    for index, row in enumerate(results, 1):
        parts = [f"{key}: {value}" for key, value in row.items()]
        lines.append(f"- Row {index}: " + ", ".join(parts))
    return "\n".join(lines)


def answer_sql_question(question: str, llm: ChatOpenAI) -> str:
    """Full pipeline: question -> SQL -> validate -> execute -> natural language answer."""
    sql = generate_sql(question, llm)
    tables_used = _tables_used_from_sql(sql)

    # Safety check: only allow SELECT queries
    if not validate_sql_readonly(sql):
        return ("I can only run read-only queries against the database. "
                "The generated query was rejected for safety reasons.")

    try:
        results = run_sql_query(sql)
    except Exception as e:
        return f"I encountered an error querying the database: {e}\n\nGenerated SQL: {sql}"

    if not results:
        summary_prompt = (
            f"The user asked: '{question}'\n"
            f"SQL query returned no results.\n"
            f"Generated SQL: {sql}\n"
            "Provide a helpful response explaining no matching data was found."
        )
    else:
        summary_prompt = (
            f"The user asked: '{question}'\n"
            f"SQL query: {sql}\n"
            f"Tables queried: {', '.join(tables_used)}\n"
            f"Results ({len(results)} rows):\n{results}\n\n"
            "Summarize these results in a clear, friendly, natural language response. "
            "Include relevant details and format nicely."
        )

    response = llm.invoke([
        SystemMessage(content="You are a helpful customer support assistant. "
                      "Summarize database query results in a clear, friendly manner."),
        HumanMessage(content=summary_prompt),
    ])
    return f"{response.content.strip()}\n\n---\n{_format_sql_source(sql, tables_used, len(results))}"


def answer_sql_facts_question(question: str, llm: ChatOpenAI) -> str:
    """Run a SQL lookup but return only factual database rows for hybrid reasoning."""
    sql = generate_sql(question, llm)
    tables_used = _tables_used_from_sql(sql)

    if not validate_sql_readonly(sql):
        return ("**Database Facts:** The generated database lookup was rejected "
                "because it was not a safe read-only query.")

    try:
        results = run_sql_query(sql)
    except Exception as e:
        return f"**Database Facts:** I encountered an error querying the database: {e}"

    return f"{_format_sql_facts(results)}\n\n---\n{_format_sql_source(sql, tables_used, len(results))}"
