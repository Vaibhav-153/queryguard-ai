"""Persist normalized invoice records in workspace JSON."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.invoices.models import InvoiceRecord


def save_invoice_records(records: list[InvoiceRecord], path: Path) -> None:
    path.write_text(
        json.dumps([record.model_dump() for record in records], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_invoice_records(path: Path) -> list[InvoiceRecord]:
    values = json.loads(path.read_text(encoding="utf-8"))
    return [InvoiceRecord.model_validate(value) for value in values]
