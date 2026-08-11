"""Workspace metadata persisted on disk."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class WorkspaceMetadata(BaseModel):
    workspace_id: str
    kind: Literal["database", "spreadsheet", "document", "invoice"]
    display_name: str
    source_files: list[str] = Field(default_factory=list)
    created_at: datetime
    expires_at: datetime
    database_file: str | None = None
    chunks_file: str | None = None
    invoices_file: str | None = None
    table_count: int = 0
    column_count: int = 0
    relationship_count: int = 0
    document_chunk_count: int = 0
    invoice_count: int = 0
    warnings: list[str] = Field(default_factory=list)
