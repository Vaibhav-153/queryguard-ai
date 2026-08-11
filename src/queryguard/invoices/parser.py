"""Conservative invoice field extraction for common personal-project formats."""

from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from queryguard.documents.models import DocumentUnit
from queryguard.ingestion.common import IngestionError, validate_office_archive
from queryguard.ingestion.document_loader import extract_document_units
from queryguard.ingestion.ocr import OCRUnavailableError, ocr_image
from queryguard.invoices.models import InvoiceRecord

INVOICE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".xlsx", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

INVOICE_NUMBER_RE = re.compile(
    r"(?:invoice\s*(?:no\.?|number|#)|inv\s*#)\s*[:\-]?\s*([A-Za-z0-9][A-Za-z0-9\-_/]*)",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"(?:invoice\s*date|date)\s*[:\-]?\s*([0-9]{1,4}[./\-][0-9]{1,2}[./\-][0-9]{1,4})",
    re.IGNORECASE,
)
DUE_DATE_RE = re.compile(
    r"(?:due\s*date|payment\s*due)\s*[:\-]?\s*([0-9]{1,4}[./\-][0-9]{1,2}[./\-][0-9]{1,4})",
    re.IGNORECASE,
)
AMOUNT_PATTERN = r"(?:[$₹€£]\s*)?([0-9][0-9,]*(?:\.\d{1,2})?)"
CURRENCY_SYMBOLS = {"$": "USD", "₹": "INR", "€": "EUR", "£": "GBP"}

COLUMN_ALIASES = {
    "invoice_number": {"invoice", "invoice_no", "invoice_number", "invoice_id", "inv_no"},
    "vendor": {"vendor", "supplier", "seller", "company", "merchant"},
    "invoice_date": {"date", "invoice_date", "issued_date"},
    "due_date": {"due_date", "payment_due", "due"},
    "currency": {"currency", "currency_code"},
    "subtotal": {"subtotal", "sub_total", "net_amount"},
    "tax": {"tax", "gst", "vat", "tax_amount"},
    "total": {"total", "grand_total", "amount", "amount_due", "invoice_total"},
}


def _normalized_column(value: Any) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return text


def _parse_amount(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = re.sub(r"[^0-9.\-]", "", str(value).replace(",", ""))
    if not text or text in {"-", "."}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _string_value(value: Any) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _find_labeled_amount(text: str, labels: tuple[str, ...]) -> float | None:
    label_group = "|".join(re.escape(label) for label in labels)
    pattern = re.compile(
        rf"(?:{label_group})\s*[:\-]?\s*{AMOUNT_PATTERN}",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if not matches:
        return None
    value = matches[-1]
    if isinstance(value, tuple):
        value = value[-1]
    return _parse_amount(value)


def _detect_currency(text: str) -> str | None:
    upper = text.upper()
    for code in ("USD", "INR", "EUR", "GBP", "AUD", "CAD"):
        if re.search(rf"\b{code}\b", upper):
            return code
    for symbol, code in CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code
    return None


def _guess_vendor(lines: list[str]) -> str | None:
    for line in lines[:8]:
        lower = line.lower()
        if any(term in lower for term in ("invoice", "date", "bill to", "ship to", "tax invoice")):
            continue
        if 2 <= len(line) <= 100 and re.search(r"[A-Za-z]", line):
            return line
    return None


def parse_invoice_text(source_file: str, text: str) -> InvoiceRecord:
    """Extract a small, explainable field set and flag uncertain records for review."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    invoice_match = INVOICE_NUMBER_RE.search(text)
    date_match = DATE_RE.search(text)
    due_match = DUE_DATE_RE.search(text)

    subtotal = _find_labeled_amount(text, ("subtotal", "sub total", "net amount"))
    tax = _find_labeled_amount(text, ("tax", "gst", "vat"))
    total = _find_labeled_amount(
        text,
        ("grand total", "invoice total", "amount due", "total due", "total"),
    )

    notes: list[str] = []
    if not invoice_match:
        notes.append("Invoice number was not confidently detected.")
    if total is None:
        notes.append("Total amount was not confidently detected.")

    return InvoiceRecord(
        source_file=source_file,
        invoice_number=invoice_match.group(1) if invoice_match else None,
        vendor=_guess_vendor(lines),
        invoice_date=date_match.group(1) if date_match else None,
        due_date=due_match.group(1) if due_match else None,
        currency=_detect_currency(text),
        subtotal=subtotal,
        tax=tax,
        total=total,
        needs_review=bool(notes),
        notes=notes,
        raw_text=text.strip(),
    )


def _column_mapping(columns: list[Any]) -> dict[str, str]:
    normalized = {_normalized_column(column): str(column) for column in columns}
    mapping: dict[str, str] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                mapping[field] = normalized[alias]
                break
    return mapping


def _records_from_frame(frame: pd.DataFrame, source_file: str) -> list[InvoiceRecord]:
    mapping = _column_mapping(list(frame.columns))
    if "total" not in mapping:
        raise IngestionError(
            f"{source_file} does not contain a recognizable invoice total/amount column."
        )

    records: list[InvoiceRecord] = []
    for _, row in frame.iterrows():
        total = _parse_amount(row.get(mapping["total"]))
        invoice_number = _string_value(row.get(mapping.get("invoice_number", "")))
        notes = []
        if invoice_number is None:
            notes.append("Invoice number missing from spreadsheet row.")
        if total is None:
            notes.append("Total amount missing from spreadsheet row.")

        records.append(
            InvoiceRecord(
                source_file=source_file,
                invoice_number=invoice_number,
                vendor=_string_value(row.get(mapping.get("vendor", ""))),
                invoice_date=_string_value(row.get(mapping.get("invoice_date", ""))),
                due_date=_string_value(row.get(mapping.get("due_date", ""))),
                currency=_string_value(row.get(mapping.get("currency", ""))),
                subtotal=_parse_amount(row.get(mapping.get("subtotal", ""))),
                tax=_parse_amount(row.get(mapping.get("tax", ""))),
                total=total,
                needs_review=bool(notes),
                notes=notes,
            )
        )
    return records


def parse_invoice_file(
    path: Path,
    *,
    max_office_uncompressed_bytes: int,
) -> tuple[list[InvoiceRecord], list[DocumentUnit], list[str]]:
    """Parse one invoice file into structured records plus raw text evidence."""
    extension = path.suffix.lower()
    if extension not in INVOICE_EXTENSIONS:
        raise IngestionError(f"Unsupported invoice file type: {extension or 'none'}")

    if extension == ".csv":
        frame = pd.read_csv(path)
        records = _records_from_frame(frame, path.name)
        return records, [], []

    if extension == ".xlsx":
        validate_office_archive(
            path,
            max_uncompressed_bytes=max_office_uncompressed_bytes,
        )
        workbook = pd.ExcelFile(path, engine="openpyxl")
        records: list[InvoiceRecord] = []
        warnings: list[str] = []
        for sheet in workbook.sheet_names:
            frame = pd.read_excel(workbook, sheet_name=sheet)
            if frame.empty:
                continue
            try:
                records.extend(_records_from_frame(frame, f"{path.name} · {sheet}"))
            except IngestionError:
                warnings.append(
                    f"Skipped sheet '{sheet}' because no recognizable invoice total column was found."
                )
        if not records:
            raise IngestionError(f"No invoice rows were found in {path.name}.")
        return records, [], warnings

    if extension in IMAGE_EXTENSIONS:
        try:
            text = ocr_image(path)
        except OCRUnavailableError as exc:
            raise IngestionError(str(exc)) from exc
        if not text:
            raise IngestionError(f"OCR returned no text for {path.name}.")
        units = [DocumentUnit(source_name=path.name, locator="OCR text", text=text)]
        return [parse_invoice_text(path.name, text)], units, []

    units, warnings = extract_document_units(
        path,
        max_uncompressed_bytes=max_office_uncompressed_bytes,
    )
    text = "\n".join(unit.text for unit in units)
    return [parse_invoice_text(path.name, text)], units, warnings
