"""Download helpers for query and invoice tables."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pandas as pd

FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe_spreadsheet_value(value: Any) -> Any:
    """Prevent text values from becoming formulas when an export is opened.

    Query results can contain user-controlled text from uploaded files. Prefixing
    formula-like strings with an apostrophe keeps spreadsheet software from
    executing them as formulas. Numeric negative values remain numeric.
    """
    if isinstance(value, str) and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def _safe_export_frame(frame: pd.DataFrame) -> pd.DataFrame:
    safe = frame.copy()
    for column in safe.columns:
        safe[column] = safe[column].map(_safe_spreadsheet_value)
    return safe


def dataframe_to_csv_bytes(frame: pd.DataFrame) -> bytes:
    return _safe_export_frame(frame).to_csv(index=False).encode("utf-8")


def dataframe_to_xlsx_bytes(frame: pd.DataFrame, sheet_name: str = "Results") -> bytes:
    buffer = BytesIO()
    safe = _safe_export_frame(frame)
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        safe.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    return buffer.getvalue()
