"""Deterministic result explanation and chart recommendation."""

from __future__ import annotations

import re
from numbers import Number
from typing import Any

DATE_LIKE = re.compile(r"^\d{4}[-/]\d{1,2}(?:[-/]\d{1,2})?")


def choose_chart(columns: list[str], rows: list[list[Any]]) -> str:
    if not rows or len(columns) < 2:
        return "table"

    first_values = [row[0] for row in rows[:10] if row]
    second_values = [row[1] for row in rows[:10] if len(row) > 1]
    if not second_values or not all(isinstance(value, Number) for value in second_values):
        return "table"

    if first_values and all(
        isinstance(value, str) and DATE_LIKE.match(value) for value in first_values
    ):
        return "line"
    if first_values and all(isinstance(value, (str, int, float)) for value in first_values):
        return "bar"
    return "table"


def explain_result(columns: list[str], rows: list[list[Any]], truncated: bool) -> str:
    if not rows:
        return "The query executed successfully but returned no rows."
    if len(rows) == 1 and len(columns) == 1:
        return f"The query returned {columns[0]} = {rows[0][0]}."
    message = f"The query returned {len(rows)} row(s) across {len(columns)} column(s)."
    if truncated:
        message += " The displayed result was truncated by the configured row limit."
    return message
