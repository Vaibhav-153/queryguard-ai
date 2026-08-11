"""Simple source-preserving document chunking."""

from __future__ import annotations

import hashlib

from queryguard.documents.models import DocumentChunk, DocumentUnit


def _chunk_id(source_name: str, locator: str, index: int, text: str) -> str:
    value = f"{source_name}|{locator}|{index}|{text[:100]}".encode()
    return hashlib.sha1(value).hexdigest()[:16]


def chunk_units(
    units: list[DocumentUnit],
    *,
    max_chars: int = 1600,
    overlap_chars: int = 200,
) -> list[DocumentChunk]:
    """Split long units while retaining their original page/slide/section locator."""
    chunks: list[DocumentChunk] = []
    step = max(1, max_chars - overlap_chars)

    for unit in units:
        text = " ".join(unit.text.split())
        if not text:
            continue
        if len(text) <= max_chars:
            chunks.append(
                DocumentChunk(
                    chunk_id=_chunk_id(unit.source_name, unit.locator, 0, text),
                    source_name=unit.source_name,
                    locator=unit.locator,
                    text=text,
                )
            )
            continue

        index = 0
        start = 0
        while start < len(text):
            end = min(len(text), start + max_chars)
            piece = text[start:end].strip()
            if piece:
                chunks.append(
                    DocumentChunk(
                        chunk_id=_chunk_id(unit.source_name, unit.locator, index, piece),
                        source_name=unit.source_name,
                        locator=unit.locator,
                        text=piece,
                    )
                )
            index += 1
            if end >= len(text):
                break
            start += step

    return chunks
