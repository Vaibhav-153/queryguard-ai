"""Groq REST client using its OpenAI-compatible chat endpoint."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError
from queryguard.llm.prompts import SYSTEM_PROMPT, generation_prompt, repair_prompt
from queryguard.llm.utils import extract_sql


class GroqSQLGenerator:
    """Generate SQLite with a Groq-hosted model."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen/qwen3.6-27b",
        base_url: str = "https://api.groq.com/openai/v1",
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Groq API key is required for the groq provider.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _chat(self, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "max_completion_tokens": 2048,
            "stream": False,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices") or []
            if not choices:
                raise LLMError("Groq returned no completion choice.")
            content = choices[0].get("message", {}).get("content")
            if not content:
                raise LLMError("Groq returned no message content.")
            return extract_sql(str(content))
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMError(f"Groq API request failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Groq: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise LLMError(f"Could not parse Groq response: {exc}") from exc

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
