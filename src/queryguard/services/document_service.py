"""Evidence-grounded question answering over uploaded document chunks."""

from __future__ import annotations

import time

from queryguard.config import Settings
from queryguard.documents.factory import build_document_retriever
from queryguard.documents.models import DocumentChunk
from queryguard.llm.factory import build_text_llm
from queryguard.llm.prompts import DOCUMENT_SYSTEM_PROMPT, document_prompt
from queryguard.models import DocumentQueryResponse, DocumentSource


def _milliseconds(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


class DocumentService:
    def __init__(self, settings: Settings, chunks: list[DocumentChunk]) -> None:
        self.settings = settings
        self.chunks = chunks
        self.retriever = build_document_retriever(settings, chunks)
        self.llm = build_text_llm(settings)

    def ask(self, question: str, top_k: int | None = None) -> DocumentQueryResponse:
        request_start = time.perf_counter()
        question = question.strip()
        if len(question) < 3:
            return DocumentQueryResponse(
                status="error",
                question=question,
                error="Please provide a complete question.",
            )

        retrieval_start = time.perf_counter()
        hits = self.retriever.search(question, top_k or self.settings.document_top_k)
        retrieval_ms = _milliseconds(retrieval_start)
        if not hits:
            return DocumentQueryResponse(
                status="success",
                question=question,
                answer="The uploaded documents do not contain enough matching evidence to answer this question.",
                latency_ms={"retrieval": retrieval_ms, "total": _milliseconds(request_start)},
            )

        evidence_blocks = []
        sources = []
        for index, hit in enumerate(hits, start=1):
            label = f"S{index}"
            evidence_blocks.append(
                f"[{label}] {hit.chunk.source_name} · {hit.chunk.locator}\n{hit.chunk.text}"
            )
            sources.append(
                DocumentSource(
                    source_name=hit.chunk.source_name,
                    locator=hit.chunk.locator,
                    excerpt=hit.chunk.text[:500],
                    score=hit.score,
                )
            )

        generation_start = time.perf_counter()
        try:
            answer = self.llm.complete(
                document_prompt(question, evidence_blocks),
                system_prompt=DOCUMENT_SYSTEM_PROMPT,
                max_tokens=1200,
            )
        except Exception as exc:
            return DocumentQueryResponse(
                status="error",
                question=question,
                error=f"Document answer generation failed: {exc}",
                sources=sources,
                latency_ms={
                    "retrieval": retrieval_ms,
                    "generation": _milliseconds(generation_start),
                    "total": _milliseconds(request_start),
                },
            )

        return DocumentQueryResponse(
            status="success",
            question=question,
            answer=answer,
            sources=sources,
            latency_ms={
                "retrieval": retrieval_ms,
                "generation": _milliseconds(generation_start),
                "total": _milliseconds(request_start),
            },
        )
