"""Shared helpers for safely handling user-uploaded files."""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

SAFE_FILE_RE = re.compile(r"[^A-Za-z0-9._-]+")


class IngestionError(RuntimeError):
    """Raised when an uploaded file cannot be safely ingested."""


def safe_filename(name: str) -> str:
    """Return a filesystem-safe basename without accepting user paths."""
    base = Path(name).name.strip()
    cleaned = SAFE_FILE_RE.sub("_", base).strip("._")
    if not cleaned:
        raise IngestionError("The uploaded file name is empty or unsupported.")
    return cleaned[:180]


def validate_extension(path: Path, allowed: set[str]) -> None:
    extension = path.suffix.lower()
    if extension not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise IngestionError(
            f"Unsupported file type '{extension or 'none'}'. Allowed types: {allowed_text}."
        )


def validate_office_archive(
    path: Path,
    *,
    max_uncompressed_bytes: int,
    max_members: int = 5000,
) -> None:
    """Reject malformed or unexpectedly large Office ZIP containers."""
    if not zipfile.is_zipfile(path):
        raise IngestionError(f"{path.name} is not a valid Office Open XML file.")

    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > max_members:
            raise IngestionError(f"{path.name} contains too many internal files ({len(members)}).")

        total = sum(item.file_size for item in members)
        if total > max_uncompressed_bytes:
            size_mb = round(total / (1024 * 1024), 1)
            raise IngestionError(
                f"{path.name} expands to {size_mb} MB, above the configured safety limit."
            )
