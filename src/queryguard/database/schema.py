"""SQLite schema extraction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from queryguard.database.connection import open_read_only


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
        if foreign_keys:
            return f"TABLE {self.name}({columns}) | FOREIGN KEYS: {foreign_keys}"
        return f"TABLE {self.name}({columns})"


def extract_schema(database_path: Path) -> list[TableSchema]:
    """Read user tables, columns, and foreign keys from SQLite metadata."""
    with open_read_only(database_path) as connection:
        table_rows = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        tables: list[TableSchema] = []
        for table_row in table_rows:
            table_name = str(table_row["name"])
            escaped = table_name.replace("'", "''")
            column_rows = connection.execute(
                f"PRAGMA table_info('{escaped}')"
            ).fetchall()
            fk_rows = connection.execute(
                f"PRAGMA foreign_key_list('{escaped}')"
            ).fetchall()

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
            tables.append(
                TableSchema(
                    name=table_name,
                    columns=columns,
                    foreign_keys=foreign_keys,
                )
            )

    return tables


def allowed_table_names(schema: list[TableSchema]) -> set[str]:
    return {table.name.lower() for table in schema}
