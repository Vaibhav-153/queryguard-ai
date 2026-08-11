"""Read-only SQLite access with row and time limits."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DatabaseError(RuntimeError):
    """Raised for controlled database failures."""


class QueryTimeoutError(DatabaseError):
    """Raised when a query exceeds the configured execution budget."""


@dataclass(slots=True)
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool
    execution_ms: float

    @property
    def row_count(self) -> int:
        return len(self.rows)


@contextmanager
def open_read_only(database_path: Path) -> Iterator[sqlite3.Connection]:
    """Yield a SQLite connection opened in URI read-only mode.

    The explicit ``finally: close`` matters on modern Python versions because
    the sqlite transaction context manager does not itself guarantee that the
    connection object is closed immediately.
    """
    resolved = database_path.expanduser().resolve()
    if not resolved.is_file():
        raise DatabaseError(f"Database file does not exist: {resolved}")

    uri = f"file:{resolved.as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True, check_same_thread=False)
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        yield connection
    finally:
        connection.close()


def execute_read_only(
    database_path: Path,
    sql: str,
    *,
    max_rows: int = 200,
    timeout_ms: int = 5000,
) -> QueryResult:
    """Execute an already-validated query through a read-only connection."""
    start = time.perf_counter()
    deadline = start + timeout_ms / 1000.0

    try:
        with open_read_only(database_path) as connection:

            def progress_handler() -> int:
                return 1 if time.perf_counter() >= deadline else 0

            connection.set_progress_handler(progress_handler, 1000)
            cursor = connection.execute(sql)
            columns = [item[0] for item in (cursor.description or [])]
            fetched = cursor.fetchmany(max_rows + 1)
            truncated = len(fetched) > max_rows
            rows = [list(row) for row in fetched[:max_rows]]
    except sqlite3.OperationalError as exc:
        if "interrupted" in str(exc).lower():
            raise QueryTimeoutError(f"Query exceeded the {timeout_ms} ms execution limit.") from exc
        raise DatabaseError(f"SQLite execution failed: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseError(f"SQLite database error: {exc}") from exc

    elapsed_ms = (time.perf_counter() - start) * 1000
    return QueryResult(
        columns=columns,
        rows=rows,
        truncated=truncated,
        execution_ms=round(elapsed_ms, 3),
    )
