from __future__ import annotations

import httpx
import pytest

from queryguard.config import Settings
from queryguard.llm.factory import build_sql_generator, build_text_llm
from queryguard.llm.gemini import GeminiLLM
from queryguard.llm.groq import GroqLLM
from queryguard.llm.sql_generator import LLMSQLGenerator


class FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)
        self.request = httpx.Request("POST", "https://example.test")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(
                self.status_code,
                request=self.request,
                text=self.text,
            )
            raise httpx.HTTPStatusError(
                "request failed",
                request=self.request,
                response=response,
            )

    def json(self) -> dict:
        return self._payload


def test_gemini_text_client_and_sql_adapter(monkeypatch):
    def fake_post(*args, **kwargs):
        assert kwargs["headers"]["x-goog-api-key"] == "test-key"
        return FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "```sql\nSELECT COUNT(*) FROM Customer;\n```"}]
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = GeminiLLM(
        api_key="test-key",
        model="gemini-test",
        base_url="https://example.test/v1beta",
        timeout_seconds=10,
    )
    generator = LLMSQLGenerator(client)
    assert generator.generate_sql("How many customers?", "TABLE Customer") == (
        "SELECT COUNT(*) FROM Customer"
    )


def test_groq_text_client_and_sql_adapter(monkeypatch):
    def fake_post(*args, **kwargs):
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
        return FakeResponse(
            {"choices": [{"message": {"content": "Here is SQL: SELECT Name FROM Artist;"}}]}
        )

    monkeypatch.setattr(httpx, "post", fake_post)
    client = GroqLLM(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
        timeout_seconds=10,
    )
    generator = LLMSQLGenerator(client)
    assert generator.generate_sql("List artists", "TABLE Artist") == "SELECT Name FROM Artist"


def test_factory_requires_gemini_key():
    settings = Settings(llm_provider="gemini", gemini_api_key=None)
    with pytest.raises(ValueError, match="QUERYGUARD_GEMINI_API_KEY"):
        build_text_llm(settings)


def test_factory_requires_groq_key():
    settings = Settings(llm_provider="groq", groq_api_key=None)
    with pytest.raises(ValueError, match="QUERYGUARD_GROQ_API_KEY"):
        build_sql_generator(settings)
