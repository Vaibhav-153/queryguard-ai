"""Public request and response models."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k_tables: int | None = Field(default=None, ge=1, le=20)


class RetrievedTable(BaseModel):
    table: str
    score: float
    reason: str


class ValidationInfo(BaseModel):
    is_safe: bool
    tables: list[str] = []
    warnings: list[str] = []


class QueryResponse(BaseModel):
    status: Literal["success", "clarification", "blocked", "error"]
    question: str
    sql: str | None = None
    columns: list[str] = []
    rows: list[list[Any]] = []
    row_count: int = 0
    truncated: bool = False
    explanation: str | None = None
    chart_type: Literal["table", "bar", "line", "none"] = "none"
    clarification: str | None = None
    error: str | None = None
    validation: ValidationInfo | None = None
    retrieved_tables: list[RetrievedTable] = []
    latency_ms: dict[str, float] = {}
    repaired: bool = False


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database_available: bool
    llm_provider: str
    llm_model: str
    retrieval_strategy: str
    api_protected: bool
