"""Lightweight ambiguity detection before SQL generation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AmbiguityResult:
    ambiguous: bool
    reason: str | None = None
    clarification: str | None = None


VAGUE_RANKING_TERMS = {"best", "worst", "top", "bottom", "highest", "lowest"}
METRIC_TERMS = {
    "revenue",
    "sales",
    "total",
    "count",
    "number",
    "average",
    "avg",
    "price",
    "quantity",
    "purchases",
    "orders",
    "invoices",
    "tracks",
}


def detect_ambiguity(question: str) -> AmbiguityResult:
    """Identify a few high-value ambiguities without pretending to solve NLP generally."""
    normalized = " ".join(question.lower().strip().split())
    words = set(normalized.replace("?", "").replace(",", " ").split())

    if len(words) < 2:
        return AmbiguityResult(
            ambiguous=True,
            reason="question_too_short",
            clarification="Please provide a complete analytical question.",
        )

    ranking_terms = words & VAGUE_RANKING_TERMS
    if ranking_terms and not (words & METRIC_TERMS):
        return AmbiguityResult(
            ambiguous=True,
            reason="ranking_metric_missing",
            clarification=(
                "Please specify how the ranking should be measured, for example by revenue, "
                "invoice count, purchases, or another metric."
            ),
        )

    if "recent" in words and not any(
        unit in words for unit in {"day", "days", "week", "weeks", "month", "months", "year", "years"}
    ):
        return AmbiguityResult(
            ambiguous=True,
            reason="time_window_missing",
            clarification="What time window should 'recent' represent?",
        )

    return AmbiguityResult(ambiguous=False)
