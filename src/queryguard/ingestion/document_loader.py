"""Route supported document files to the correct parser."""

from __future__ import annotations

from pathlib import Path

from queryguard.documents.models import DocumentUnit
from queryguard.ingestion.common import IngestionError
from queryguard.ingestion.docx_loader import extract_docx_units
from queryguard.ingestion.pdf_loader import extract_pdf_units
from queryguard.ingestion.pptx_loader import extract_pptx_units

DOCUMENT_EXTENSIONS = {".pdf", ".docx", ".pptx"}


def extract_document_units(
    path: Path,
    *,
    max_uncompressed_bytes: int,
) -> tuple[list[DocumentUnit], list[str]]:
    extension = path.suffix.lower()
    if extension == ".pdf":
        return extract_pdf_units(path)
    if extension == ".docx":
        return extract_docx_units(path, max_uncompressed_bytes=max_uncompressed_bytes)
    if extension == ".pptx":
        return extract_pptx_units(path, max_uncompressed_bytes=max_uncompressed_bytes)
    raise IngestionError(f"Unsupported document type: {extension or 'none'}")
