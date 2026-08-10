"""Optional sentence-transformer schema retriever."""

from __future__ import annotations

import numpy as np

from queryguard.retrieval.base import RetrievalResult
from queryguard.schema.documents import SchemaDocument


class SemanticDependencyError(RuntimeError):
    pass


class SemanticSchemaRetriever:
    """Semantic retrieval using Sentence Transformers and cosine similarity."""

    def __init__(self, documents: list[SchemaDocument], model_name: str) -> None:
        if not documents:
            raise ValueError("At least one schema document is required.")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise SemanticDependencyError(
                "Semantic retrieval requires the optional 'semantic' dependencies. "
                "Install with: pip install -e '.[semantic]'"
            ) from exc

        self.documents = documents
        self.model = SentenceTransformer(model_name)
        texts = [document.text for document in documents]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        self.document_embeddings = np.asarray(embeddings, dtype=np.float32)

    def search(self, question: str, top_k: int) -> list[RetrievalResult]:
        query = self.model.encode([question], normalize_embeddings=True)
        query_vector = np.asarray(query[0], dtype=np.float32)
        scores = self.document_embeddings @ query_vector
        indices = np.argsort(-scores)[:top_k]
        return [
            RetrievalResult(
                table=self.documents[int(index)].table,
                score=round(float(scores[int(index)]), 6),
                reason="sentence-transformer cosine similarity",
            )
            for index in indices
        ]
