"""Store normalized invoice fields in SQLite for governed analytics."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from queryguard.invoices.models import InvoiceRecord

INVOICE_TABLE_SQL = """
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_file TEXT NOT NULL,
    invoice_number TEXT,
    vendor TEXT,
    invoice_date TEXT,
    due_date TEXT,
    currency TEXT,
    subtotal REAL,
    tax REAL,
    total REAL,
    needs_review INTEGER NOT NULL
)
"""


def write_invoice_database(records: list[InvoiceRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    with closing(sqlite3.connect(path)) as connection:
        connection.execute(INVOICE_TABLE_SQL)
        connection.executemany(
            """
            INSERT INTO invoices (
                source_file, invoice_number, vendor, invoice_date, due_date,
                currency, subtotal, tax, total, needs_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    record.source_file,
                    record.invoice_number,
                    record.vendor,
                    record.invoice_date,
                    record.due_date,
                    record.currency,
                    record.subtotal,
                    record.tax,
                    record.total,
                    int(record.needs_review),
                )
                for record in records
            ],
        )
        connection.commit()
