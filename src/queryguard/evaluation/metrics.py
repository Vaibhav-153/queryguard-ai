"""Evaluation helpers for result matching and retrieval metrics."""

from __future__ import annotations

from typing import Any


def _normalize_value(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 6)
    return value


def normalize_rows(rows: list[list[Any]], order_sensitive: bool) -> list[tuple[Any, ...]]:
    normalized = [tuple(_normalize_value(value) for value in row) for row in rows]
    if order_sensitive:
        return normalized
    return sorted(normalized, key=repr)


def result_match(
    generated_columns: list[str],
    generated_rows: list[list[Any]],
    gold_columns: list[str],
    gold_rows: list[list[Any]],
    order_sensitive: bool,
) -> bool:
    if [name.lower() for name in generated_columns] != [name.lower() for name in gold_columns]:
        return False
    return normalize_rows(generated_rows, order_sensitive) == normalize_rows(gold_rows, order_sensitive)


def table_recall_at_k(retrieved: list[str], required: list[str], k: int) -> float:
    required_set = {table.lower() for table in required}
    if not required_set:
        return 1.0
    found = {table.lower() for table in retrieved[:k]}
    return len(required_set & found) / len(required_set)


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percentile_value))))
    return ordered[index]
