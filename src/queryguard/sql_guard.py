"""Read-only SQL validation with SQLGlot and a fail-closed fallback."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import ParseError
except ImportError:  # pragma: no cover - SQLGlot is a declared dependency.
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
    "Alter", "Analyze", "Attach", "Command", "Copy", "Create", "Delete",
    "Detach", "Drop", "Grant", "Insert", "LoadData", "Merge", "Pragma",
    "Replace", "Revoke", "Set", "Transaction", "TruncateTable", "Update", "Use",
}
ALLOWED_ROOT_NAMES = {"Select", "Union", "Intersect", "Except"}
DENIED_WORDS = re.compile(
    r"\b(ALTER|ANALYZE|ATTACH|CREATE|DELETE|DETACH|DROP|GRANT|INSERT|PRAGMA|"
    r"REPLACE|REVOKE|TRUNCATE|UPDATE|VACUUM)\b",
    re.IGNORECASE,
)
TABLE_REF = re.compile(r"\b(?:FROM|JOIN)\s+[\"`\[]?([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
CTE_NAME = re.compile(r"(?:\bWITH\b|,)\s*([A-Za-z_][A-Za-z0-9_]*)\s+AS\s*\(", re.IGNORECASE)


def _fallback_validate(sql: str, allowed_tables: set[str]) -> SQLValidationResult:
    """Conservative fallback used only when the declared SQLGlot dependency is absent."""
    cleaned = sql.strip()
    if not cleaned:
        return SQLValidationResult(False, errors=["SQL is empty."])
    if "--" in cleaned or "/*" in cleaned:
        return SQLValidationResult(False, errors=["SQL comments are not allowed without SQLGlot."])
    statements = [part.strip() for part in cleaned.split(";") if part.strip()]
    if len(statements) != 1:
        return SQLValidationResult(False, errors=["Exactly one SQL statement is allowed."])
    if not re.match(r"^(SELECT|WITH)\b", statements[0], flags=re.IGNORECASE):
        return SQLValidationResult(False, errors=["Only read-only SELECT-style queries are allowed."])
    match = DENIED_WORDS.search(statements[0])
    if match:
        return SQLValidationResult(False, errors=[f"Denied SQL operation detected: {match.group(1).upper()}"])
    ctes = {name.lower() for name in CTE_NAME.findall(statements[0])}
    tables = sorted({name for name in TABLE_REF.findall(statements[0]) if name.lower() not in ctes})
    unknown = sorted(name for name in tables if name.lower() not in allowed_tables)
    if unknown:
        return SQLValidationResult(False, tables=tables, errors=["Query references unapproved table(s): " + ", ".join(unknown)])
    return SQLValidationResult(True, tables=tables, warnings=["SQLGlot unavailable; conservative fallback validation used."])


def validate_sql(sql: str, allowed_tables: set[str], dialect: str = "sqlite") -> SQLValidationResult:
    cleaned = sql.strip()
    if not cleaned:
        return SQLValidationResult(False, errors=["SQL is empty."])
    if sqlglot is None or exp is None:
        return _fallback_validate(cleaned, allowed_tables)

    try:
        statements = sqlglot.parse(cleaned, read=dialect)
    except ParseError as exc:
        return SQLValidationResult(False, errors=[f"SQL parse error: {exc}"])
    if len(statements) != 1:
        return SQLValidationResult(False, errors=["Exactly one SQL statement is allowed."])

    statement = statements[0]
    errors: list[str] = []
    warnings: list[str] = []
    node_name = type(statement).__name__
    if node_name not in ALLOWED_ROOT_NAMES:
        errors.append(f"Only read-only SELECT-style queries are allowed, not {node_name}.")
    denied_seen = sorted(
        {type(node).__name__ for node in statement.walk() if type(node).__name__ in DENIED_NODE_NAMES}
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
    unknown = sorted(table for table in tables if table.lower() not in allowed_tables)
    if unknown:
        errors.append("Query references unapproved table(s): " + ", ".join(unknown))
    if not tables:
        warnings.append("Query does not reference a database table.")
    return SQLValidationResult(not errors, tables, errors, warnings)
