from queryguard.documents import DocumentService
from queryguard.retrieval import TextChunk


def test_document_answer_contains_sources(settings):
    chunks = [
        TextChunk("architecture.pdf", "page 2", "QueryGuard validates generated SQL before execution."),
        TextChunk("architecture.pdf", "page 3", "The database connection is opened in read-only mode."),
    ]
    response = DocumentService(settings, chunks).ask("How does QueryGuard protect SQL execution?")
    assert response.status == "success"
    assert response.answer
    assert response.sources
    assert response.sources[0].source_name == "architecture.pdf"


def test_document_answer_handles_no_match(settings):
    chunks = [TextChunk("notes.pdf", "page 1", "The sky is blue.")]
    response = DocumentService(settings, chunks).ask("What database is used?")
    assert response.status == "success"
    assert "not available" in (response.answer or "").lower()
    assert response.sources == []
