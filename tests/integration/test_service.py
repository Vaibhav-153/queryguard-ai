from queryguard.config import Settings
from queryguard.services.query_service import QueryService


def test_demo_service_executes_full_pipeline(database_path):
    service = QueryService(
        Settings(
            environment="test",
            database_path=database_path,
            llm_provider="demo",
            retrieval_strategy="lexical",
        )
    )

    response = service.ask("Show the top 5 customers by revenue")

    assert response.status == "success"
    assert response.row_count == 5
    assert response.validation is not None
    assert response.validation.is_safe
    assert {"Customer", "Invoice"} <= set(response.validation.tables)


def test_demo_service_requests_clarification(database_path):
    service = QueryService(
        Settings(
            environment="test",
            database_path=database_path,
            llm_provider="demo",
        )
    )

    response = service.ask("Who are the best customers?")

    assert response.status == "clarification"
