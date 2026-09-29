"""Conservative invoice extraction and normalized SQLite storage."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path

import fitz
import pandas as pd

from queryguard.ingestion import IngestionError, validate_office_archive
from queryguard.retrieval import TextChunk


@dataclass(slots=True)
class InvoiceRecord:
    source_name: str
    invoice_number: str | None = None
    invoice_date: str | None = None
    vendor: str | None = None
    customer: str | None = None
    currency: str | None = None
    total: float | None = None
    needs_review: bool = True
    raw_text: str = ""


FIELD_ALIASES = {
    "invoice_number": {"invoice", "invoice_number", "invoice_no", "invoice_id", "number"},
    "invoice_date": {"date", "invoice_date"},
    "vendor": {"vendor", "supplier", "seller"},
    "customer": {"customer", "buyer", "client"},
    "currency": {"currency"},
    "total": {"total", "amount", "invoice_total", "grand_total"},
}


def _normalize_columns(frame: pd.DataFrame) -> dict[str, str]:
    by_normalized = {re.sub(r"[^a-z0-9]+", "_", str(col).lower()).strip("_"): str(col) for col in frame.columns}
    mapping: dict[str, str] = {}
    for target, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in by_normalized:
                mapping[target] = by_normalized[alias]
                break
    return mapping


def _to_float(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(value)))
    except ValueError:
        return None


def parse_structured_invoices(path: Path, max_uncompressed_bytes: int) -> list[InvoiceRecord]:
    if path.suffix.lower() == ".xlsx":
        validate_office_archive(path, max_uncompressed_bytes)
        frame = pd.read_excel(path, engine="openpyxl")
    else:
        frame = pd.read_csv(path)
    mapping = _normalize_columns(frame)
    records: list[InvoiceRecord] = []
    for _, row in frame.iterrows():
        values = {target: row[column] for target, column in mapping.items()}
        record = InvoiceRecord(
            source_name=path.name,
            invoice_number=str(values.get("invoice_number")) if values.get("invoice_number") is not None else None,
            invoice_date=str(values.get("invoice_date")) if values.get("invoice_date") is not None else None,
            vendor=str(values.get("vendor")) if values.get("vendor") is not None else None,
            customer=str(values.get("customer")) if values.get("customer") is not None else None,
            currency=str(values.get("currency")) if values.get("currency") is not None else None,
            total=_to_float(values.get("total")),
        )
        record.needs_review = not (record.invoice_number and record.total is not None)
        records.append(record)
    return records


def _extract_pdf_text(path: Path) -> str:
    document = fitz.open(path)
    try:
        return "\n".join(page.get_text("text") for page in document)
    finally:
        document.close()


def _ocr_image(path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return ""
    try:
        return pytesseract.image_to_string(Image.open(path))
    except Exception:
        return ""


def _record_from_text(path: Path, text: str) -> InvoiceRecord:
    invoice = re.search(r"invoice\s*(?:no\.?|number|#)?\s*[:#-]?\s*([A-Z0-9-]+)", text, re.IGNORECASE)
    date = re.search(r"(?:invoice\s+)?date\s*[:#-]?\s*([0-9]{1,4}[-/.][0-9]{1,2}[-/.][0-9]{1,4})", text, re.IGNORECASE)
    vendor_match = re.search(r"(?:vendor|supplier|seller)\s*[:#-]\s*([^\n\r]+)", text, re.IGNORECASE)
    customer_match = re.search(r"(?:customer|buyer|client|bill\s+to)\s*[:#-]\s*([^\n\r]+)", text, re.IGNORECASE)
    total_match = re.search(r"(?:grand\s+total|invoice\s+total|total)\s*[:#-]?\s*(?:INR|USD|EUR|GBP|₹|\$|€|£)?\s*([0-9][0-9,]*(?:\.\d{1,2})?)", text, re.IGNORECASE)
    currency_match = re.search(r"\b(INR|USD|EUR|GBP)\b|([₹$€£])", text, re.IGNORECASE)
    currency = None
    if currency_match:
        token = (currency_match.group(1) or currency_match.group(2)).upper()
        currency = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}.get(token, token)
    total = float(total_match.group(1).replace(",", "")) if total_match else None
    record = InvoiceRecord(
        source_name=path.name,
        invoice_number=invoice.group(1).strip() if invoice else None,
        invoice_date=date.group(1).strip() if date else None,
        vendor=vendor_match.group(1).strip() if vendor_match else None,
        customer=customer_match.group(1).strip() if customer_match else None,
        currency=currency,
        total=total,
        raw_text=text.strip(),
    )
    record.needs_review = not (record.invoice_number and record.total is not None)
    return record


def parse_invoice_file(path: Path, max_office_uncompressed_bytes: int) -> tuple[list[InvoiceRecord], list[TextChunk], list[str]]:
    suffix = path.suffix.lower()
    warnings: list[str] = []
    if suffix in {".csv", ".xlsx"}:
        records = parse_structured_invoices(path, max_office_uncompressed_bytes)
        return records, [], warnings
    if suffix == ".pdf":
        text = _extract_pdf_text(path)
    elif suffix in {".png", ".jpg", ".jpeg"}:
        text = _ocr_image(path)
        if not text:
            raise IngestionError("Image invoice requires Tesseract/pytesseract for OCR.")
    else:
        raise IngestionError("Unsupported invoice file type.")
    if not text.strip():
        raise IngestionError("No invoice text could be extracted.")
    record = _record_from_text(path, text)
    if record.needs_review:
        warnings.append(f"{path.name}: key fields were not confidently extracted; manual review is required.")
    chunks = [TextChunk(path.name, "invoice text", " ".join(text.split()))]
    return [record], chunks, warnings


def save_invoice_records(records: list[InvoiceRecord], path: Path) -> None:
    path.write_text(json.dumps([asdict(record) for record in records], indent=2), encoding="utf-8")


def load_invoice_records(path: Path) -> list[InvoiceRecord]:
    return [InvoiceRecord(**item) for item in json.loads(path.read_text(encoding="utf-8"))]


def write_invoice_database(records: list[InvoiceRecord], database_path: Path) -> None:
    if database_path.exists():
        database_path.unlink()
    connection = sqlite3.connect(database_path)
    try:
        connection.execute(
            """
            CREATE TABLE invoices (
                source_name TEXT,
                invoice_number TEXT,
                invoice_date TEXT,
                vendor TEXT,
                customer TEXT,
                currency TEXT,
                total REAL,
                needs_review INTEGER
            )
            """
        )
        connection.executemany(
            "INSERT INTO invoices VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    r.source_name, r.invoice_number, r.invoice_date, r.vendor, r.customer,
                    r.currency, r.total, int(r.needs_review),
                )
                for r in records
            ],
        )
        connection.commit()
    finally:
        connection.close()
