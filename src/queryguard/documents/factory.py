"""Create the configured document retriever."""

from queryguard.config import Settings
from queryguard.documents.models import DocumentChunk
from queryguard.documents.retrieval import LexicalDocumentRetriever
from queryguard.documents.semantic import SemanticDocumentRetriever


def build_document_retriever(settings: Settings, chunks: list[DocumentChunk]):
    if settings.retrieval_strategy == "semantic":
        return SemanticDocumentRetriever(chunks, settings.embedding_model)
    return LexicalDocumentRetriever(chunks)
