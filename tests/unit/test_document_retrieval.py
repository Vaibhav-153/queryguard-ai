from queryguard.documents.models import DocumentChunk
from queryguard.documents.retrieval import LexicalDocumentRetriever


def test_document_retrieval_returns_relevant_chunk():
    chunks = [
        DocumentChunk("1", "policy.docx", "Leave", "Employees receive 20 days annual leave."),
        DocumentChunk("2", "policy.docx", "Security", "Passwords must be changed regularly."),
    ]
    retriever = LexicalDocumentRetriever(chunks)
    hits = retriever.search("How many annual leave days are provided?", 1)
    assert hits[0].chunk.locator == "Leave"


def test_document_retrieval_uses_section_locator_as_search_context():
    chunks = [
        DocumentChunk(
            "1",
            "policy.docx",
            "Password Policy",
            "Credentials must contain at least 12 characters.",
        ),
        DocumentChunk("2", "policy.docx", "General", "Employees should read the handbook."),
    ]
    retriever = LexicalDocumentRetriever(chunks)
    hits = retriever.search("What does the password policy require?", 1)
    assert hits[0].chunk.locator == "Password Policy"
