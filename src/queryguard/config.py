"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration.

    Every field can be overridden with an environment variable prefixed by
    ``QUERYGUARD_``. Secrets use ``SecretStr`` so accidental logging does not
    reveal their values.
    """

    model_config = SettingsConfigDict(
        env_prefix="QUERYGUARD_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "QueryGuard AI"
    environment: Literal["development", "test", "production"] = "development"
    database_path: Path = Path("data/chinook/Chinook_Sqlite.sqlite")

    llm_provider: Literal["ollama", "gemini", "groq", "demo"] = "ollama"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_timeout_seconds: float = Field(default=120.0, gt=0, le=600)

    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-3.5-flash"
    gemini_thinking_level: Literal["minimal", "low", "medium", "high"] = "low"
    gemini_timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    groq_api_key: SecretStr | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "qwen/qwen3.6-27b"
    groq_timeout_seconds: float = Field(default=60.0, gt=0, le=300)

    # Optional shared secret between the hosted Streamlit UI and FastAPI API.
    # Local development can leave it unset. Production should set it.
    api_access_key: SecretStr | None = None

    retrieval_strategy: Literal["lexical", "semantic"] = "lexical"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k_tables: int = Field(default=5, ge=1, le=20)

    max_result_rows: int = Field(default=200, ge=1, le=5000)
    query_timeout_ms: int = Field(default=5000, ge=100, le=120000)
    log_level: str = "INFO"
    enable_repair: bool = True

    @field_validator("database_path", mode="before")
    @classmethod
    def normalize_database_path(cls, value: str | Path) -> Path:
        return Path(value)

    @property
    def llm_model_name(self) -> str:
        """Return the configured model name without exposing credentials."""
        if self.llm_provider == "gemini":
            return self.gemini_model
        if self.llm_provider == "groq":
            return self.groq_model
        if self.llm_provider == "ollama":
            return self.ollama_model
        return "deterministic-demo"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for application use."""
    return Settings()
