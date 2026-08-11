"""Document parsing and retrieval data structures."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class DocumentUnit:
    source_name: str
    locator: str
    text: str


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str
    source_name: str
    locator: str
    text: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, str]) -> DocumentChunk:
        return cls(**value)


@dataclass(frozen=True, slots=True)
class DocumentHit:
    chunk: DocumentChunk
    score: float
