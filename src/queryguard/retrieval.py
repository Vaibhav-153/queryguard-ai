"""Small explainable retrievers for schemas and document chunks."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from queryguard.database import TableSchema

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
QUERY_EXPANSIONS = {
    "revenue": ["invoice", "total"],
    "sales": ["invoice", "total"],
    "sale": ["invoice", "total"],
    "order": ["invoice"],
    "purchase": ["invoice", "line"],
    "customer": ["customer"],
    "song": ["track"],
}

DOCUMENT_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was",
    "what", "when", "where", "which", "who", "why", "with",
}


def normalize_token(token: str) -> str:
    token = token.lower()
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def tokenize(text: str) -> list[str]:
    tokens = [normalize_token(token) for token in TOKEN_RE.findall(text)]
    expanded = list(tokens)
    for token in tokens:
        expanded.extend(QUERY_EXPANSIONS.get(token, []))
    return expanded


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    table: str
    score: float
    reason: str


@dataclass(frozen=True, slots=True)
class SchemaDocument:
    table: str
    text: str


def schema_documents(schema: list[TableSchema]) -> list[SchemaDocument]:
    docs: list[SchemaDocument] = []
    for table in schema:
        column_names = " ".join(column.name for column in table.columns)
        relationships = " ".join(
            f"{fk.from_column} {fk.target_table} {fk.target_column}" for fk in table.foreign_keys
        )
        docs.append(SchemaDocument(table.name, f"{table.name} {column_names} {relationships}"))
    return docs


class LexicalSchemaRetriever:
    """BM25-inspired schema retriever with no external search service."""

    def __init__(self, schema: list[TableSchema]) -> None:
        self.documents = schema_documents(schema)
        if not self.documents:
            raise ValueError("At least one database table is required.")
        self.document_tokens = [tokenize(item.text) for item in self.documents]
        self.document_frequencies: Counter[str] = Counter()
        for tokens in self.document_tokens:
            self.document_frequencies.update(set(tokens))
        self.average_length = sum(map(len, self.document_tokens)) / len(self.document_tokens)

    def _idf(self, token: str) -> float:
        n = len(self.documents)
        df = self.document_frequencies.get(token, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0
        counts = Counter(doc_tokens)
        k1, b = 1.5, 0.75
        score = 0.0
        for token in set(query_tokens):
            tf = counts.get(token, 0)
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
            if normalize_token(document.table) in query_tokens:
                score += 2.0
            ranked.append((score, document))
        ranked.sort(key=lambda item: (-item[0], item[1].table.lower()))
        return [
            RetrievalResult(
                table=document.table,
                score=round(float(score), 6),
                reason="lexical BM25-style overlap with table and column metadata",
            )
            for score, document in ranked[:top_k]
        ]


@dataclass(frozen=True, slots=True)
class TextChunk:
    source_name: str
    locator: str
    text: str


@dataclass(frozen=True, slots=True)
class ChunkMatch:
    chunk: TextChunk
    score: float


def search_chunks(chunks: list[TextChunk], question: str, top_k: int) -> list[ChunkMatch]:
    query = Counter(token for token in tokenize(question) if token not in DOCUMENT_STOPWORDS)
    if not query:
        return []
    scored: list[ChunkMatch] = []
    for chunk in chunks:
        tokens = Counter(token for token in tokenize(chunk.text) if token not in DOCUMENT_STOPWORDS)
        overlap = sum(min(query[token], tokens[token]) for token in query)
        score = overlap / max(1, sum(query.values()))
        if score > 0:
            scored.append(ChunkMatch(chunk, round(score, 6)))
    scored.sort(key=lambda item: (-item.score, item.chunk.source_name, item.chunk.locator))
    return scored[:top_k]
