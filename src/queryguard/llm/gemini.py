"""Gemini REST client for the hosted portfolio deployment."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError
from queryguard.llm.prompts import SYSTEM_PROMPT, generation_prompt, repair_prompt
from queryguard.llm.utils import extract_sql


class GeminiSQLGenerator:
    """Generate SQLite using the Gemini generateContent REST API."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 60.0,
        thinking_level: str = "low",
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for the gemini provider.")
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.thinking_level = thinking_level

    def _chat(self, user_prompt: str) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {
                "maxOutputTokens": 2048,
                "thinkingConfig": {"thinkingLevel": self.thinking_level},
            },
        }
        try:
            response = httpx.post(
                f"{self.base_url}/models/{self.model}:generateContent",
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            candidates = data.get("candidates") or []
            if not candidates:
                feedback = data.get("promptFeedback") or {}
                raise LLMError(f"Gemini returned no candidate. Feedback: {feedback}")

            parts = candidates[0].get("content", {}).get("parts", [])
            text_parts = [
                str(part.get("text"))
                for part in parts
                if part.get("text") and not part.get("thought", False)
            ]
            if not text_parts:
                raise LLMError("Gemini returned no final text content.")
            return extract_sql("\n".join(text_parts))
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMError(f"Gemini API request failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Gemini: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise LLMError(f"Could not parse Gemini response: {exc}") from exc

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
