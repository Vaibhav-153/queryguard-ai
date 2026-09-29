"""LLM provider adapters and SQL prompt handling."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx

from queryguard.config import Settings


class LLMError(RuntimeError):
    pass


SQL_FENCE = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
TABLE_IN_CONTEXT = re.compile(r"TABLE\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)


def clean_sql(text: str) -> str:
    match = SQL_FENCE.search(text)
    if match:
        text = match.group(1)
    text = text.strip()
    if text.lower().startswith("sql:"):
        text = text[4:].strip()
    return text.rstrip(";").strip()


class TextLLM:
    def complete(self, system: str, user: str) -> str:
        raise NotImplementedError


class DemoLLM(TextLLM):
    """Deterministic provider for local smoke tests and the bundled demo."""

    def complete(self, system: str, user: str) -> str:
        # Document mode passes evidence with a distinctive marker.
        if "EVIDENCE:" in user:
            evidence = user.split("EVIDENCE:", 1)[1].strip()
            first = evidence.split("\n\n", 1)[0]
            return "Based on the retrieved evidence: " + re.sub(r"^\[S\d+\]\s*", "", first)

        question_match = re.search(r"QUESTION:\s*(.+?)\n(?:SCHEMA|PREVIOUS SQL):", user, re.DOTALL)
        question = (question_match.group(1).strip() if question_match else user).lower()
        tables = TABLE_IN_CONTEXT.findall(user)
        lowered = {table.lower(): table for table in tables}

        if "customer" in question and "revenue" in question and "invoice" in lowered:
            customer = lowered.get("customer", "Customer")
            invoice = lowered["invoice"]
            return (
                f'SELECT c.CustomerId, c.FirstName || " " || c.LastName AS customer, '
                f'ROUND(SUM(i.Total), 2) AS revenue FROM "{customer}" c '
                f'JOIN "{invoice}" i ON i.CustomerId = c.CustomerId '
                "GROUP BY c.CustomerId, c.FirstName, c.LastName ORDER BY revenue DESC LIMIT 5"
            )
        if "country" in question and "revenue" in question and "invoice" in lowered:
            customer = lowered.get("customer", "Customer")
            invoice = lowered["invoice"]
            return (
                f'SELECT c.Country, ROUND(SUM(i.Total), 2) AS revenue FROM "{customer}" c '
                f'JOIN "{invoice}" i ON i.CustomerId = c.CustomerId '
                "GROUP BY c.Country ORDER BY revenue DESC"
            )
        if "how many" in question and "customer" in question and "customer" in lowered:
            return f'SELECT COUNT(*) AS customer_count FROM "{lowered["customer"]}"'
        if "average" in question and "price" in question and "track" in lowered:
            return f'SELECT ROUND(AVG(UnitPrice), 2) AS average_price FROM "{lowered["track"]}"'
        if "genre" in question and "track" in lowered:
            return (
                f'SELECT Genre, COUNT(*) AS track_count FROM "{lowered["track"]}" '
                "GROUP BY Genre ORDER BY track_count DESC"
            )
        if tables:
            return f'SELECT * FROM "{tables[0]}" LIMIT 10'
        return "SELECT 1 AS result"


@dataclass(slots=True)
class OllamaLLM(TextLLM):
    base_url: str
    model: str
    timeout: float

    def complete(self, system: str, user: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/api/chat",
                json={
                    "model": self.model,
                    "stream": False,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return str(response.json()["message"]["content"])
        except Exception as exc:
            raise LLMError(f"Ollama request failed: {exc}") from exc


@dataclass(slots=True)
class GroqLLM(TextLLM):
    base_url: str
    model: str
    api_key: str
    timeout: float

    def complete(self, system: str, user: str) -> str:
        try:
            response = httpx.post(
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return str(response.json()["choices"][0]["message"]["content"])
        except Exception as exc:
            raise LLMError(f"Groq request failed: {exc}") from exc


@dataclass(slots=True)
class GeminiLLM(TextLLM):
    base_url: str
    model: str
    api_key: str
    timeout: float

    def complete(self, system: str, user: str) -> str:
        url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent"
        try:
            response = httpx.post(
                url,
                params={"key": self.api_key},
                json={
                    "systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user}]}],
                    "generationConfig": {"temperature": 0},
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return str(response.json()["candidates"][0]["content"]["parts"][0]["text"])
        except Exception as exc:
            raise LLMError(f"Gemini request failed: {exc}") from exc


def build_text_llm(settings: Settings) -> TextLLM:
    if settings.llm_provider == "demo":
        return DemoLLM()
    if settings.llm_provider == "ollama":
        return OllamaLLM(settings.ollama_base_url, settings.ollama_model, settings.ollama_timeout_seconds)
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key or not settings.gemini_api_key.get_secret_value():
            raise ValueError("QUERYGUARD_GEMINI_API_KEY is required for the Gemini provider.")
        return GeminiLLM(
            settings.gemini_base_url,
            settings.gemini_model,
            settings.gemini_api_key.get_secret_value(),
            settings.gemini_timeout_seconds,
        )
    if not settings.groq_api_key or not settings.groq_api_key.get_secret_value():
        raise ValueError("QUERYGUARD_GROQ_API_KEY is required for the Groq provider.")
    return GroqLLM(
        settings.groq_base_url,
        settings.groq_model,
        settings.groq_api_key.get_secret_value(),
        settings.groq_timeout_seconds,
    )


SQL_SYSTEM = """You convert analytics questions into one SQLite SELECT query.
Use only tables and columns shown in the schema. Do not use INSERT, UPDATE, DELETE,
DDL, PRAGMA, ATTACH, or multiple statements. Return SQL only."""


def generate_sql(llm: TextLLM, question: str, schema_context: str) -> str:
    user = f"QUESTION:\n{question}\nSCHEMA:\n{schema_context}\nReturn one SQLite query."
    return clean_sql(llm.complete(SQL_SYSTEM, user))


def repair_sql(llm: TextLLM, question: str, schema_context: str, previous_sql: str, error: str) -> str:
    user = (
        f"QUESTION:\n{question}\nPREVIOUS SQL:\n{previous_sql}\nERROR:\n{error}\n"
        f"SCHEMA:\n{schema_context}\nReturn one corrected SQLite SELECT query."
    )
    return clean_sql(llm.complete(SQL_SYSTEM, user))


def answer_from_evidence(llm: TextLLM, question: str, evidence: list[str]) -> str:
    system = (
        "Answer only from the supplied evidence. If the evidence does not support the answer, "
        "say that the answer is not available in the retrieved passages."
    )
    joined = "\n\n".join(f"[S{i}] {text}" for i, text in enumerate(evidence, start=1))
    return llm.complete(system, f"QUESTION:\n{question}\nEVIDENCE:\n{joined}").strip()
