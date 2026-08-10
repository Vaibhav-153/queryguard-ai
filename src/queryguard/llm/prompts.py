"""Prompt templates kept separate for versioning and review."""

SYSTEM_PROMPT = """You are a careful text-to-SQL generator for an analytics application.
Return exactly one SQLite SELECT query and nothing else.
Rules:
- Use only tables and columns in the supplied schema context.
- Never write INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, ATTACH, DETACH, PRAGMA, or transaction statements.
- Do not invent columns.
- Prefer explicit JOIN conditions from foreign keys.
- Use clear aliases.
- If the question asks for a count, sum, average, minimum, maximum, or ranking, perform the calculation in SQL.
- Do not explain the query.
"""


def generation_prompt(question: str, schema_context: str) -> str:
    return f"""Schema context:\n{schema_context}\n\nUser question:\n{question}\n\nSQLite SQL:"""


def repair_prompt(question: str, schema_context: str, previous_sql: str, error: str) -> str:
    return f"""The previous SQL failed validation or execution.
Return one corrected SQLite SELECT query only.

Schema context:
{schema_context}

Question:
{question}

Previous SQL:
{previous_sql}

Failure:
{error}

Corrected SQLite SQL:"""
