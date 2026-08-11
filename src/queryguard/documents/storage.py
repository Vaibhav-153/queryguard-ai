"""Persist parsed document chunks inside a workspace."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.documents.models import DocumentChunk


def save_chunks(chunks: list[DocumentChunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps([chunk.to_dict() for chunk in chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_chunks(path: Path) -> list[DocumentChunk]:
    values = json.loads(path.read_text(encoding="utf-8"))
    return [DocumentChunk.from_dict(value) for value in values]
