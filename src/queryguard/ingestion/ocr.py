"""Optional OCR helpers. Tesseract is not required for normal text documents."""

from __future__ import annotations

import io
import shutil
from pathlib import Path

import fitz
from PIL import Image

from queryguard.documents.models import DocumentUnit
from queryguard.ingestion.common import IngestionError


class OCRUnavailableError(IngestionError):
    """Raised when a file needs OCR but Tesseract is unavailable."""


def ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return shutil.which("tesseract") is not None


def _require_ocr():
    if not ocr_available():
        raise OCRUnavailableError(
            "OCR requires the optional pytesseract package and the Tesseract system binary."
        )
    import pytesseract

    return pytesseract


def ocr_image(path: Path) -> str:
    pytesseract = _require_ocr()
    try:
        with Image.open(path) as image:
            return pytesseract.image_to_string(image).strip()
    except Exception as exc:
        raise IngestionError(f"Could not OCR image {path.name}: {exc}") from exc


def ocr_pdf(path: Path) -> list[DocumentUnit]:
    """OCR every PDF page while preserving page numbers."""
    pytesseract = _require_ocr()
    try:
        document = fitz.open(path)
    except Exception as exc:
        raise IngestionError(f"Could not open PDF {path.name}: {exc}") from exc

    units: list[DocumentUnit] = []
    try:
        for page_number, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            text = pytesseract.image_to_string(image).strip()
            if text:
                units.append(
                    DocumentUnit(
                        source_name=path.name,
                        locator=f"Page {page_number} · OCR",
                        text=text,
                    )
                )
    finally:
        document.close()
    return units
