"""Build configured schema retrievers."""

from queryguard.config import Settings
from queryguard.database.schema import TableSchema
from queryguard.retrieval.base import SchemaRetriever
from queryguard.retrieval.lexical import LexicalSchemaRetriever
from queryguard.retrieval.semantic import SemanticSchemaRetriever
from queryguard.schema.documents import build_schema_documents


def build_retriever(settings: Settings, schema: list[TableSchema]) -> SchemaRetriever:
    documents = build_schema_documents(schema)
    if settings.retrieval_strategy == "semantic":
        return SemanticSchemaRetriever(documents, settings.embedding_model)
    return LexicalSchemaRetriever(documents)
