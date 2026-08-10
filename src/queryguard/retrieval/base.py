"""Retrieval interfaces shared by lexical and semantic implementations."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    table: str
    score: float
    reason: str


class SchemaRetriever(Protocol):
    def search(self, question: str, top_k: int) -> list[RetrievalResult]:
        """Return the most relevant tables for a user question."""
