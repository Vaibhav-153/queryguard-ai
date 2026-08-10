"""LLM client interface shared by local and hosted providers."""

from typing import Protocol


class LLMError(RuntimeError):
    """Raised when an LLM provider cannot return a usable response."""


class SQLGenerator(Protocol):
    def generate_sql(self, question: str, schema_context: str) -> str:
        """Generate one SQLite query."""

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        previous_sql: str,
        error: str,
    ) -> str:
        """Return one corrected SQLite query after a controlled failure."""
