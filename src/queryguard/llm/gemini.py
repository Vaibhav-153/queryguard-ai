"""Minimal Gemini REST client used by QueryGuard."""

from __future__ import annotations

import httpx

from queryguard.llm.base import LLMError


class GeminiLLM:
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float,
        thinking_level: str = "low",
    ) -> None:
        if not api_key.strip():
            raise ValueError("A Gemini API key is required for the gemini provider.")
        self.api_key = api_key
        self.model_name = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.thinking_level = thinking_level

    def complete(
        self,
        prompt: str,
        *,
        system_prompt: str,
        max_tokens: int = 2048,
    ) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": max_tokens,
                "thinkingConfig": {"thinkingLevel": self.thinking_level},
            },
        }
        try:
            response = httpx.post(
                f"{self.base_url}/models/{self.model_name}:generateContent",
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
            return "\n".join(text_parts).strip()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMError(f"Gemini API request failed: {detail}") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"Could not call Gemini: {exc}") from exc
        except (TypeError, ValueError, KeyError) as exc:
            raise LLMError(f"Could not parse Gemini response: {exc}") from exc
