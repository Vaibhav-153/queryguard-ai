"""Small LLM interfaces shared by local and hosted providers."""

from __future__ import annotations

from typing import Protocol


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot return usable text."""


class TextLLM(Protocol):
    """Minimal interface used by SQL, document, and invoice services."""

    provider_name: str
    model_name: str

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        """Return one text completion."""


class SQLGenerator(Protocol):
    """Interface used by the governed Text-to-SQL pipeline."""

    def generate_sql(self, question: str, schema_context: str) -> str:
        """Generate one SQLite query."""

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        previous_sql: str,
        error: str,
    ) -> str:
        """Return one corrected SQLite query after one controlled failure."""
