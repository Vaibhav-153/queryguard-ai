"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for local, test, and hosted deployments.

    Every field can be overridden with an environment variable prefixed by
    ``QUERYGUARD_``. Secrets use ``SecretStr`` so normal logging does not reveal
    their values.
    """

    model_config = SettingsConfigDict(
        env_prefix="QUERYGUARD_",
        env_file=".env",
        extra="ignore",
    )

    app_name: str = "QueryGuard AI"
    environment: Literal["development", "test", "production"] = "development"

    # Built-in demo database. Uploaded sources use isolated workspace paths.
    database_path: Path = Path("data/chinook/Chinook_Sqlite.sqlite")
    workspace_root: Path = Path("data/workspaces")
    workspace_ttl_minutes: int = Field(default=120, ge=5, le=10080)
    max_upload_mb: int = Field(default=50, ge=1, le=500)
    max_total_upload_mb: int = Field(default=100, ge=1, le=1000)
    max_upload_files: int = Field(default=10, ge=1, le=50)
    max_office_uncompressed_mb: int = Field(default=120, ge=10, le=1000)

    llm_provider: Literal["ollama", "gemini", "groq", "demo"] = "demo"

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

    # Optional shared secret between Streamlit and FastAPI. Local development
    # can leave it unset. Hosted deployments should set it on both services.
    api_access_key: SecretStr | None = None

    retrieval_strategy: Literal["lexical", "semantic"] = "lexical"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k_tables: int = Field(default=5, ge=1, le=20)
    document_top_k: int = Field(default=5, ge=1, le=20)

    max_result_rows: int = Field(default=200, ge=1, le=5000)
    query_timeout_ms: int = Field(default=5000, ge=100, le=120000)
    log_level: str = "INFO"
    enable_repair: bool = True

    @field_validator("database_path", "workspace_root", mode="before")
    @classmethod
    def normalize_paths(cls, value: str | Path) -> Path:
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

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    @property
    def max_total_upload_bytes(self) -> int:
        return self.max_total_upload_mb * 1024 * 1024

    @property
    def max_office_uncompressed_bytes(self) -> int:
        return self.max_office_uncompressed_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings for application use."""
    return Settings()
