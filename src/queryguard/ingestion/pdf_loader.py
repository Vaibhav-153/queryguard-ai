"""PDF text extraction with optional OCR and page-level provenance."""

from __future__ import annotations

from pathlib import Path

import fitz

from queryguard.documents.models import DocumentUnit
from queryguard.ingestion.common import IngestionError, validate_extension
from queryguard.ingestion.ocr import ocr_available, ocr_pdf

PDF_EXTENSIONS = {".pdf"}


def extract_pdf_units(path: Path) -> tuple[list[DocumentUnit], list[str]]:
    validate_extension(path, PDF_EXTENSIONS)
    units: list[DocumentUnit] = []
    warnings: list[str] = []

    try:
        document = fitz.open(path)
    except Exception as exc:
        raise IngestionError(f"Could not open PDF {path.name}: {exc}") from exc

    blank_pages = 0
    try:
        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text").strip()
            if text:
                units.append(
                    DocumentUnit(
                        source_name=path.name,
                        locator=f"Page {page_number}",
                        text=text,
                    )
                )
            else:
                blank_pages += 1
    finally:
        document.close()

    if blank_pages and ocr_available():
        ocr_units = ocr_pdf(path)
        known_locators = {unit.locator.split(" · ")[0] for unit in units}
        for unit in ocr_units:
            page_locator = unit.locator.split(" · ")[0]
            if page_locator not in known_locators:
                units.append(unit)
        if ocr_units:
            warnings.append(f"OCR was used for scanned/blank pages in {path.name}.")
    elif blank_pages:
        warnings.append(
            f"{path.name} contains {blank_pages} page(s) with no extractable text. "
            "Install the optional OCR dependency and Tesseract to process scanned pages."
        )

    if not units:
        raise IngestionError(
            f"No text could be extracted from {path.name}. It may require optional OCR support."
        )
    return units, warnings
