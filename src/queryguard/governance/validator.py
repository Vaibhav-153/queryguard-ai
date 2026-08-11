"""AST-based SQL governance for read-only analytics."""

from __future__ import annotations

from dataclasses import dataclass, field

try:
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import ParseError
except ImportError:  # Allows health/docs imports before dependencies are installed.
    sqlglot = None
    exp = None

    class ParseError(Exception):
        pass


@dataclass(slots=True)
class SQLValidationResult:
    is_safe: bool
    tables: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


DENIED_NODE_NAMES = {
    "Alter",
    "Analyze",
    "Attach",
    "Command",
    "Copy",
    "Create",
    "Delete",
    "Detach",
    "Drop",
    "Grant",
    "Insert",
    "LoadData",
    "Merge",
    "Pragma",
    "Replace",
    "Revoke",
    "Set",
    "Transaction",
    "TruncateTable",
    "Update",
    "Use",
}

ALLOWED_ROOT_NAMES = {"Select", "Union", "Intersect", "Except"}


def _node_name(node) -> str:
    return type(node).__name__


def validate_sql(
    sql: str,
    allowed_tables: set[str],
    dialect: str = "sqlite",
) -> SQLValidationResult:
    """Parse SQL and enforce a single read-only statement using approved tables."""
    cleaned = sql.strip()
    if not cleaned:
        return SQLValidationResult(is_safe=False, errors=["SQL is empty."])
    if sqlglot is None or exp is None:
        return SQLValidationResult(
            is_safe=False,
            errors=["SQLGlot is required for SQL validation but is not installed."],
        )

    try:
        statements = sqlglot.parse(cleaned, read=dialect)
    except ParseError as exc:
        return SQLValidationResult(is_safe=False, errors=[f"SQL parse error: {exc}"])

    if len(statements) != 1:
        return SQLValidationResult(
            is_safe=False,
            errors=["Exactly one SQL statement is allowed."],
        )

    statement = statements[0]
    errors: list[str] = []
    warnings: list[str] = []

    if _node_name(statement) not in ALLOWED_ROOT_NAMES:
        errors.append(
            f"Only read-only SELECT-style queries are allowed, not {_node_name(statement)}."
        )

    denied_seen = sorted(
        {_node_name(node) for node in statement.walk() if _node_name(node) in DENIED_NODE_NAMES}
    )
    if denied_seen:
        errors.append("Denied SQL operation detected: " + ", ".join(denied_seen))

    cte_names = {
        cte.alias_or_name.lower() for cte in statement.find_all(exp.CTE) if cte.alias_or_name
    }
    tables = sorted(
        {
            table.name
            for table in statement.find_all(exp.Table)
            if table.name and table.name.lower() not in cte_names
        },
        key=str.lower,
    )
    unknown_tables = sorted(table for table in tables if table.lower() not in allowed_tables)
    if unknown_tables:
        errors.append("Query references unapproved table(s): " + ", ".join(unknown_tables))

    if not tables:
        warnings.append("Query does not reference a database table.")

    return SQLValidationResult(
        is_safe=not errors,
        tables=tables,
        errors=errors,
        warnings=warnings,
    )
