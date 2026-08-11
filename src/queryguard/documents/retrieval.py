"""Explainable lexical retrieval for uploaded document chunks."""

from __future__ import annotations

import math
import re
from collections import Counter

from queryguard.documents.models import DocumentChunk, DocumentHit

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]+")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


class LexicalDocumentRetriever:
    """Small BM25-style retriever suitable for personal document workspaces."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("At least one document chunk is required.")
        self.chunks = chunks
        # Include locators so section titles such as "Password Policy" or
        # "Annual Leave" can contribute to retrieval without changing evidence text.
        self.tokens = [tokenize(f"{chunk.locator} {chunk.text}") for chunk in chunks]
        self.average_length = sum(len(tokens) for tokens in self.tokens) / len(self.tokens)
        self.document_frequencies = Counter()
        for tokens in self.tokens:
            self.document_frequencies.update(set(tokens))

    def _idf(self, token: str) -> float:
        n = len(self.chunks)
        df = self.document_frequencies.get(token, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        counts = Counter(doc_tokens)
        k1 = 1.5
        b = 0.75
        score = 0.0
        for token in set(query_tokens):
            tf = counts.get(token, 0)
            if not tf:
                continue
            denominator = tf + k1 * (1 - b + b * len(doc_tokens) / self.average_length)
            score += self._idf(token) * (tf * (k1 + 1)) / denominator
        return score

    def search(self, question: str, top_k: int) -> list[DocumentHit]:
        query_tokens = tokenize(question)
        ranked = [
            (self._score(query_tokens, doc_tokens), chunk)
            for chunk, doc_tokens in zip(self.chunks, self.tokens, strict=True)
        ]
        ranked.sort(key=lambda item: (-item[0], item[1].source_name, item[1].locator))
        return [
            DocumentHit(chunk=chunk, score=round(float(score), 6))
            for score, chunk in ranked[:top_k]
            if score > 0
        ]
