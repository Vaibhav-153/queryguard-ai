"""Document chunk persistence and evidence-grounded Q&A."""

from __future__ import annotations

import json
import time
from pathlib import Path

from queryguard.config import Settings
from queryguard.llm import answer_from_evidence, build_text_llm
from queryguard.models import DocumentQueryResponse, DocumentSource
from queryguard.retrieval import TextChunk, search_chunks


def save_chunks(chunks: list[TextChunk], path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {"source_name": item.source_name, "locator": item.locator, "text": item.text}
                for item in chunks
            ],
            indent=2,
        ),
        encoding="utf-8",
    )


def load_chunks(path: Path) -> list[TextChunk]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [TextChunk(**item) for item in payload]


class DocumentService:
    def __init__(self, settings: Settings, chunks: list[TextChunk]) -> None:
        if not chunks:
            raise ValueError("No document text is available in this workspace.")
        self.settings = settings
        self.chunks = chunks
        self.llm = build_text_llm(settings)

    def ask(self, question: str, top_k: int | None = None) -> DocumentQueryResponse:
        started = time.perf_counter()
        matches = search_chunks(self.chunks, question, top_k or self.settings.document_top_k)
        if not matches:
            return DocumentQueryResponse(
                status="success",
                question=question,
                answer="The answer is not available in the retrieved passages.",
                latency_ms={"total": round((time.perf_counter() - started) * 1000, 3)},
            )
        evidence = [match.chunk.text for match in matches]
        try:
            answer = answer_from_evidence(self.llm, question, evidence)
        except Exception as exc:
            return DocumentQueryResponse(
                status="error",
                question=question,
                error=f"Document answer generation failed: {exc}",
                latency_ms={"total": round((time.perf_counter() - started) * 1000, 3)},
            )
        sources = [
            DocumentSource(
                source_name=match.chunk.source_name,
                locator=match.chunk.locator,
                excerpt=match.chunk.text[:400],
                score=match.score,
            )
            for match in matches
        ]
        return DocumentQueryResponse(
            status="success",
            question=question,
            answer=answer,
            sources=sources,
            latency_ms={"total": round((time.perf_counter() - started) * 1000, 3)},
        )
