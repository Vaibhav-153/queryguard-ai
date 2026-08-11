"""Minimal Groq REST client using its OpenAI-compatible chat endpoint."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError


class GroqLLM:
    provider_name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Groq API key is required for the groq provider.")
        self.api_key = api_key
        self.model_name = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_completion_tokens": max_tokens,
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
            return str(content).strip()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMError(f"Groq API request failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Groq: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise LLMError(f"Could not parse Groq response: {exc}") from exc
