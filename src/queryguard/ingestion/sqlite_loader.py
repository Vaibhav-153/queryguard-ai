"""Validation for uploaded SQLite databases."""

from __future__ import annotations

from pathlib import Path

from queryguard.database.connection import DatabaseError, open_read_only
from queryguard.database.schema import TableSchema, extract_schema
from queryguard.ingestion.common import IngestionError, validate_extension

SQLITE_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}


def validate_sqlite_database(path: Path) -> list[TableSchema]:
    """Check file type, SQLite integrity, and presence of user tables."""
    validate_extension(path, SQLITE_EXTENSIONS)

    try:
        with open_read_only(path) as connection:
            result = connection.execute("PRAGMA quick_check").fetchone()
            status = str(result[0]) if result else "unknown"
    except DatabaseError as exc:
        raise IngestionError(f"Could not open SQLite database: {exc}") from exc

    if status.lower() != "ok":
        raise IngestionError(f"SQLite integrity check failed: {status}")

    try:
        schema = extract_schema(path)
    except DatabaseError as exc:
        raise IngestionError(f"Could not inspect SQLite schema: {exc}") from exc

    if not schema:
        raise IngestionError("The SQLite database does not contain any user tables.")

    return schema
