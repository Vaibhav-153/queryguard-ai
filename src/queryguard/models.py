"""Public API request and response models."""

from __future__ import annotations

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
    tables: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    status: Literal["success", "clarification", "blocked", "error"]
    question: str
    sql: str | None = None
    columns: list[str] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    explanation: str | None = None
    chart_type: Literal["table", "bar", "line", "none"] = "none"
    clarification: str | None = None
    error: str | None = None
    validation: ValidationInfo | None = None
    retrieved_tables: list[RetrievedTable] = Field(default_factory=list)
    latency_ms: dict[str, float] = Field(default_factory=dict)
    repaired: bool = False


class DocumentQueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    top_k: int | None = Field(default=None, ge=1, le=20)


class DocumentSource(BaseModel):
    source_name: str
    locator: str
    excerpt: str
    score: float


class DocumentQueryResponse(BaseModel):
    status: Literal["success", "error"]
    question: str
    answer: str | None = None
    sources: list[DocumentSource] = Field(default_factory=list)
    error: str | None = None
    latency_ms: dict[str, float] = Field(default_factory=dict)


class WorkspaceInfo(BaseModel):
    workspace_id: str
    kind: Literal["database", "spreadsheet", "document", "invoice"]
    display_name: str
    source_files: list[str] = Field(default_factory=list)
    created_at: str
    expires_at: str
    database_available: bool = False
    document_available: bool = False
    table_count: int = 0
    column_count: int = 0
    relationship_count: int = 0
    document_chunk_count: int = 0
    invoice_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database_available: bool
    llm_provider: str
    llm_model: str
    retrieval_strategy: str
    api_protected: bool
    max_upload_mb: int
    max_total_upload_mb: int
    max_upload_files: int
    workspace_ttl_minutes: int
    ocr_available: bool
    supported_sources: list[str] = Field(default_factory=list)
