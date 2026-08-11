"""Convert CSV and Excel files into temporary SQLite databases."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from queryguard.ingestion.common import (
    IngestionError,
    validate_extension,
    validate_office_archive,
)

SPREADSHEET_EXTENSIONS = {".csv", ".xlsx"}
TABLE_NAME_RE = re.compile(r"[^A-Za-z0-9_]+")


@dataclass(slots=True)
class SpreadsheetLoadResult:
    database_path: Path
    table_rows: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def safe_table_name(value: str, fallback: str = "data") -> str:
    """Convert a sheet/file name into a predictable SQLite table name."""
    name = TABLE_NAME_RE.sub("_", value.strip()).strip("_")
    if not name:
        name = fallback
    if name[0].isdigit():
        name = f"table_{name}"
    return name[:60]


def _unique_table_name(base: str, used: set[str]) -> str:
    candidate = base
    counter = 2
    while candidate.lower() in used:
        candidate = f"{base}_{counter}"
        counter += 1
    used.add(candidate.lower())
    return candidate


def _prepare_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Make column labels usable without silently changing cell values."""
    frame = frame.copy()
    columns: list[str] = []
    used: set[str] = set()
    for index, column in enumerate(frame.columns, start=1):
        base = safe_table_name(str(column), fallback=f"column_{index}")
        columns.append(_unique_table_name(base, used))
    frame.columns = columns
    return frame


def spreadsheet_to_sqlite(
    source_path: Path,
    database_path: Path,
    *,
    max_office_uncompressed_bytes: int,
) -> SpreadsheetLoadResult:
    """Convert one CSV or XLSX upload into a SQLite database."""
    validate_extension(source_path, SPREADSHEET_EXTENSIONS)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    if database_path.exists():
        database_path.unlink()

    warnings: list[str] = []
    tables: list[tuple[str, pd.DataFrame]] = []
    used_names: set[str] = set()

    if source_path.suffix.lower() == ".csv":
        try:
            frame = pd.read_csv(source_path)
        except Exception as exc:
            raise IngestionError(f"Could not read CSV file: {exc}") from exc
        name = _unique_table_name(safe_table_name(source_path.stem), used_names)
        tables.append((name, _prepare_frame(frame)))
    else:
        validate_office_archive(
            source_path,
            max_uncompressed_bytes=max_office_uncompressed_bytes,
        )
        try:
            workbook = pd.ExcelFile(source_path, engine="openpyxl")
        except Exception as exc:
            raise IngestionError(f"Could not read Excel workbook: {exc}") from exc

        for sheet_name in workbook.sheet_names:
            try:
                frame = pd.read_excel(workbook, sheet_name=sheet_name)
            except Exception as exc:
                raise IngestionError(f"Could not read Excel sheet '{sheet_name}': {exc}") from exc
            if frame.empty and len(frame.columns) == 0:
                warnings.append(f"Skipped empty sheet: {sheet_name}")
                continue
            name = _unique_table_name(safe_table_name(sheet_name, "sheet"), used_names)
            tables.append((name, _prepare_frame(frame)))

    if not tables:
        raise IngestionError("The spreadsheet did not contain any usable tables.")

    table_rows: dict[str, int] = {}
    try:
        with closing(sqlite3.connect(database_path)) as connection:
            for table_name, frame in tables:
                frame.to_sql(table_name, connection, if_exists="replace", index=False)
                table_rows[table_name] = len(frame)
    except Exception as exc:
        raise IngestionError(f"Could not convert spreadsheet to SQLite: {exc}") from exc

    return SpreadsheetLoadResult(
        database_path=database_path,
        table_rows=table_rows,
        warnings=warnings,
    )
