from queryguard.retrieval.lexical import LexicalSchemaRetriever
from queryguard.schema.documents import SchemaDocument


def test_lexical_retrieval_finds_customer_and_invoice_for_revenue():
    docs = [
        SchemaDocument("Customer", "Table Customer. Columns: CustomerId, FirstName, LastName."),
        SchemaDocument(
            "Invoice", "Table Invoice. Columns: InvoiceId, CustomerId, Total, BillingCountry."
        ),
        SchemaDocument("Track", "Table Track. Columns: TrackId, Name, UnitPrice."),
    ]
    retriever = LexicalSchemaRetriever(docs)
    results = retriever.search("top customers by revenue", 3)
    names = [item.table for item in results[:2]]
    assert "Customer" in names
    assert "Invoice" in names


def test_plural_normalization_matches_tracks():
    docs = [
        SchemaDocument("Track", "Table Track. Columns: TrackId, Name."),
        SchemaDocument("Artist", "Table Artist. Columns: ArtistId, Name."),
    ]
    retriever = LexicalSchemaRetriever(docs)
    assert retriever.search("How many tracks are there?", 1)[0].table == "Track"
