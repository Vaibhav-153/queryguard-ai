"""Optional semantic retrieval for uploaded documents."""

from __future__ import annotations

import numpy as np

from queryguard.documents.models import DocumentChunk, DocumentHit


class SemanticDocumentRetriever:
    def __init__(self, chunks: list[DocumentChunk], model_name: str) -> None:
        if not chunks:
            raise ValueError("At least one document chunk is required.")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Semantic document retrieval requires: pip install -e '.[semantic]'"
            ) from exc

        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        self.embeddings = np.asarray(
            self.model.encode(
                [f"{chunk.locator} {chunk.text}" for chunk in chunks],
                normalize_embeddings=True,
            ),
            dtype=np.float32,
        )

    def search(self, question: str, top_k: int) -> list[DocumentHit]:
        query = np.asarray(
            self.model.encode([question], normalize_embeddings=True)[0],
            dtype=np.float32,
        )
        scores = self.embeddings @ query
        indices = np.argsort(-scores)[:top_k]
        return [
            DocumentHit(
                chunk=self.chunks[int(index)],
                score=round(float(scores[int(index)]), 6),
            )
            for index in indices
        ]
