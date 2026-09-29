from pathlib import Path

import pandas as pd

from queryguard.invoices import parse_invoice_file, parse_structured_invoices, write_invoice_database


def test_structured_invoice_csv_is_parsed(tmp_path: Path):
    path = tmp_path / "invoices.csv"
    pd.DataFrame(
        [{
            "invoice_number": "INV-10",
            "invoice_date": "2026-02-01",
            "vendor": "Acme",
            "customer": "Farm Co",
            "currency": "INR",
            "total": "12,500.00",
        }]
    ).to_csv(path, index=False)
    records = parse_structured_invoices(path, 10_000_000)
    assert records[0].invoice_number == "INV-10"
    assert records[0].total == 12500.0
    assert records[0].needs_review is False


def test_invoice_records_can_be_written_to_sqlite(tmp_path: Path):
    path = tmp_path / "invoices.csv"
    path.write_text("invoice_number,total\nINV-1,99.50\n", encoding="utf-8")
    records, chunks, warnings = parse_invoice_file(path, 10_000_000)
    assert not chunks
    assert not warnings
    database = tmp_path / "invoices.sqlite"
    write_invoice_database(records, database)
    assert database.is_file()
