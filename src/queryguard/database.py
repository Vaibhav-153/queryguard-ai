"""SQLite schema discovery and read-only execution."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class DatabaseError(RuntimeError):
    pass


class QueryTimeoutError(DatabaseError):
    pass


@dataclass(frozen=True, slots=True)
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool
    primary_key: bool


@dataclass(frozen=True, slots=True)
class ForeignKey:
    from_column: str
    target_table: str
    target_column: str


@dataclass(frozen=True, slots=True)
class TableSchema:
    name: str
    columns: tuple[ColumnSchema, ...] = field(default_factory=tuple)
    foreign_keys: tuple[ForeignKey, ...] = field(default_factory=tuple)

    def as_prompt_text(self) -> str:
        columns = ", ".join(
            f"{column.name} {column.data_type}"
            + (" PRIMARY KEY" if column.primary_key else "")
            for column in self.columns
        )
        foreign_keys = "; ".join(
            f"{fk.from_column} -> {fk.target_table}.{fk.target_column}"
            for fk in self.foreign_keys
        )
        suffix = f" | FOREIGN KEYS: {foreign_keys}" if foreign_keys else ""
        return f"TABLE {self.name}({columns}){suffix}"


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


def extract_schema(database_path: Path) -> list[TableSchema]:
    with open_read_only(database_path) as connection:
        table_rows = connection.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        tables: list[TableSchema] = []
        for table_row in table_rows:
            table_name = str(table_row["name"])
            escaped = table_name.replace("'", "''")
            column_rows = connection.execute(f"PRAGMA table_info('{escaped}')").fetchall()
            fk_rows = connection.execute(f"PRAGMA foreign_key_list('{escaped}')").fetchall()
            columns = tuple(
                ColumnSchema(
                    name=str(row["name"]),
                    data_type=str(row["type"] or "UNKNOWN"),
                    nullable=not bool(row["notnull"]),
                    primary_key=bool(row["pk"]),
                )
                for row in column_rows
            )
            foreign_keys = tuple(
                ForeignKey(
                    from_column=str(row["from"]),
                    target_table=str(row["table"]),
                    target_column=str(row["to"]),
                )
                for row in fk_rows
            )
            tables.append(TableSchema(table_name, columns, foreign_keys))
    return tables


def allowed_table_names(schema: list[TableSchema]) -> set[str]:
    return {table.name.lower() for table in schema}


def execute_read_only(
    database_path: Path,
    sql: str,
    *,
    max_rows: int = 200,
    timeout_ms: int = 5000,
) -> QueryResult:
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
            raise QueryTimeoutError(
                f"Query exceeded the {timeout_ms} ms execution limit."
            ) from exc
        raise DatabaseError(f"SQLite execution failed: {exc}") from exc
    except sqlite3.DatabaseError as exc:
        raise DatabaseError(f"SQLite database error: {exc}") from exc
    return QueryResult(
        columns=columns,
        rows=rows,
        truncated=truncated,
        execution_ms=round((time.perf_counter() - start) * 1000, 3),
    )
