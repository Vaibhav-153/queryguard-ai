"""Normalized invoice data structures."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InvoiceRecord(BaseModel):
    source_file: str
    invoice_number: str | None = None
    vendor: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    needs_review: bool = False
    notes: list[str] = Field(default_factory=list)
    raw_text: str = ""
