"""Minimal Ollama HTTP client with no agent framework."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError
from queryguard.llm.prompts import SYSTEM_PROMPT, generation_prompt, repair_prompt
from queryguard.llm.utils import extract_sql


class OllamaSQLGenerator:
    """Generate SQLite with a locally running Ollama model."""

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _chat(self, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "options": {"temperature": 0},
        }
        try:
            response = httpx.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content")
            if not content:
                raise LLMError("Ollama returned no message content.")
            return extract_sql(str(content))
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Ollama: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise LLMError(f"Could not parse Ollama response: {exc}") from exc

    def generate_sql(self, question: str, schema_context: str) -> str:
        return self._chat(generation_prompt(question, schema_context))

    def repair_sql(
        self,
        question: str,
        schema_context: str,
        previous_sql: str,
        error: str,
    ) -> str:
        return self._chat(repair_prompt(question, schema_context, previous_sql, error))
