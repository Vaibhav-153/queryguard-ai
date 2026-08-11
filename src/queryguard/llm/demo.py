"""Deterministic providers used by tests and offline smoke demos."""

from __future__ import annotations


class DemoSQLGenerator:
    """Small question-to-SQL map for the bundled Chinook demo.

    It is intentionally not presented as an AI model. It exists so CI can test
    the complete governed SQL pipeline without downloading or calling an LLM.
    """

    EXAMPLES: list[tuple[tuple[str, ...], str]] = [
        (("how many", "customers"), "SELECT COUNT(*) AS customer_count FROM Customer"),
        (("total", "artists"), "SELECT COUNT(*) AS artist_count FROM Artist"),
        (
            ("top", "customers", "revenue"),
            """
            SELECT c.CustomerId, c.FirstName || ' ' || c.LastName AS customer,
                   ROUND(SUM(i.Total), 2) AS revenue
            FROM Customer AS c
            JOIN Invoice AS i ON i.CustomerId = c.CustomerId
            GROUP BY c.CustomerId, customer
            ORDER BY revenue DESC
            LIMIT 5
            """,
        ),
        (
            ("revenue", "country"),
            """
            SELECT BillingCountry AS country, ROUND(SUM(Total), 2) AS revenue
            FROM Invoice
            GROUP BY BillingCountry
            ORDER BY revenue DESC
            """,
        ),
        (
            ("tracks", "genre"),
            """
            SELECT g.Name AS genre, COUNT(*) AS track_count
            FROM Genre AS g
            JOIN Track AS t ON t.GenreId = g.GenreId
            GROUP BY g.GenreId, g.Name
            ORDER BY track_count DESC
            """,
        ),
        (
            ("average", "track", "price"),
            "SELECT ROUND(AVG(UnitPrice), 3) AS average_track_price FROM Track",
        ),
    ]

    @staticmethod
    def _normalized(text: str) -> str:
        return " ".join(text.lower().replace("?", "").split())

    def generate_sql(self, question: str, schema_context: str) -> str:
        normalized = self._normalized(question)
        for required_terms, sql in self.EXAMPLES:
            if all(term in normalized for term in required_terms):
                return " ".join(sql.split())
        return "SELECT 'Demo provider has no rule for this question' AS message"

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        previous_sql: str,
        error: str,
    ) -> str:
        return self.generate_sql(question, schema_context)


class DemoTextLLM:
    """Deterministic text completion for document-pipeline smoke tests."""

    provider_name = "demo"
    model_name = "deterministic-demo"

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        # Return a grounded-looking answer without pretending that this is an LLM.
        evidence_line = next(
            (line for line in prompt.splitlines() if line.strip().startswith("[S1]")),
            "[S1] Evidence was retrieved from the uploaded document.",
        )
        return f"Demo mode retrieved evidence successfully. {evidence_line}"
