"""Minimal Ollama HTTP client for local/offline inference."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError


class OllamaLLM:
    provider_name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model
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
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "options": {"temperature": 0, "num_predict": max_tokens},
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
            return str(content).strip()
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Ollama: {exc}") from exc
        except (TypeError, ValueError) as exc:
            raise LLMError(f"Could not parse Ollama response: {exc}") from exc
