"""Simple explainable lexical schema retrieval baseline."""

from __future__ import annotations

import math
import re
from collections import Counter

from queryguard.retrieval.base import RetrievalResult
from queryguard.schema.documents import SchemaDocument

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")


def _normalize_token(token: str) -> str:
    token = token.lower()
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


QUERY_EXPANSIONS = {
    "revenue": ["invoice", "total"],
    "sale": ["invoice", "total"],
    "order": ["invoice"],
    "purchase": ["invoice", "invoiceline"],
    "song": ["track"],
}


def tokenize(text: str) -> list[str]:
    tokens = [_normalize_token(token) for token in TOKEN_RE.findall(text)]
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(QUERY_EXPANSIONS.get(token, []))
    return expanded


class LexicalSchemaRetriever:
    """BM25-inspired retriever implemented with the standard library.

    This deliberately stays small so the ranking logic can be explained in an
    interview. It is a meaningful baseline for comparison with embeddings.
    """

    def __init__(self, documents: list[SchemaDocument]) -> None:
        if not documents:
            raise ValueError("At least one schema document is required.")
        self.documents = documents
        self.document_tokens = [tokenize(item.text) for item in documents]
        self.document_frequencies = self._build_document_frequencies()
        self.average_length = sum(map(len, self.document_tokens)) / len(self.document_tokens)

    def _build_document_frequencies(self) -> Counter[str]:
        frequencies: Counter[str] = Counter()
        for tokens in self.document_tokens:
            frequencies.update(set(tokens))
        return frequencies

    def _idf(self, token: str) -> float:
        n = len(self.documents)
        df = self.document_frequencies.get(token, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        term_counts = Counter(doc_tokens)
        k1 = 1.5
        b = 0.75
        score = 0.0
        for token in set(query_tokens):
            tf = term_counts.get(token, 0)
            if tf == 0:
                continue
            denominator = tf + k1 * (1 - b + b * len(doc_tokens) / self.average_length)
            score += self._idf(token) * (tf * (k1 + 1)) / denominator
        return score

    def search(self, question: str, top_k: int) -> list[RetrievalResult]:
        query_tokens = tokenize(question)
        ranked: list[tuple[float, SchemaDocument]] = []
        for document, doc_tokens in zip(self.documents, self.document_tokens, strict=True):
            score = self._score(query_tokens, doc_tokens)
            # A direct table-name mention is stronger evidence than a column-only overlap.
            if _normalize_token(document.table) in query_tokens:
                score += 2.0
            ranked.append((score, document))
        ranked.sort(key=lambda item: (-item[0], item[1].table.lower()))
        results = []
        for score, document in ranked[:top_k]:
            results.append(
                RetrievalResult(
                    table=document.table,
                    score=round(float(score), 6),
                    reason="lexical BM25-style overlap with table/column metadata",
                )
            )
        return results
