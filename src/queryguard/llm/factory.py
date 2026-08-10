"""Build the configured SQL generator."""

from queryguard.config import Settings
from queryguard.llm.base import SQLGenerator
from queryguard.llm.demo import DemoSQLGenerator
from queryguard.llm.gemini import GeminiSQLGenerator
from queryguard.llm.groq import GroqSQLGenerator
from queryguard.llm.ollama import OllamaSQLGenerator


def _secret_value(secret, provider: str, variable_name: str) -> str:
    if secret is None or not secret.get_secret_value().strip():
        raise ValueError(
            f"{variable_name} is required when QUERYGUARD_LLM_PROVIDER={provider}."
        )
    return secret.get_secret_value()


def build_sql_generator(settings: Settings) -> SQLGenerator:
    """Create one small provider client from application settings."""
    if settings.llm_provider == "demo":
        return DemoSQLGenerator()

    if settings.llm_provider == "gemini":
        return GeminiSQLGenerator(
            api_key=_secret_value(
                settings.gemini_api_key,
                "gemini",
                "QUERYGUARD_GEMINI_API_KEY",
            ),
            model=settings.gemini_model,
            base_url=settings.gemini_base_url,
            timeout_seconds=settings.gemini_timeout_seconds,
            thinking_level=settings.gemini_thinking_level,
        )

    if settings.llm_provider == "groq":
        return GroqSQLGenerator(
            api_key=_secret_value(
                settings.groq_api_key,
                "groq",
                "QUERYGUARD_GROQ_API_KEY",
            ),
            model=settings.groq_model,
            base_url=settings.groq_base_url,
            timeout_seconds=settings.groq_timeout_seconds,
        )

    return OllamaSQLGenerator(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
