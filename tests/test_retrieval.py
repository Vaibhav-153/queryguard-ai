from queryguard.database import extract_schema
from queryguard.retrieval import LexicalSchemaRetriever, TextChunk, search_chunks


def test_schema_retrieval_finds_revenue_tables(demo_db):
    retriever = LexicalSchemaRetriever(extract_schema(demo_db))
    names = [item.table for item in retriever.search("top customers by revenue", 3)]
    assert "Customer" in names
    assert "Invoice" in names


def test_document_search_returns_only_matching_evidence():
    chunks = [
        TextChunk("guide.pdf", "page 1", "QueryGuard validates SQL before execution."),
        TextChunk("guide.pdf", "page 2", "Invoice files can be normalized into SQLite."),
    ]
    results = search_chunks(chunks, "How is SQL validated?", 2)
    assert results
    assert results[0].chunk.locator == "page 1"
