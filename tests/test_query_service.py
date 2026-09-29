from queryguard.query_service import QueryService


def test_demo_customer_revenue_query(settings):
    response = QueryService(settings).ask("Show the top 5 customers by revenue")
    assert response.status == "success"
    assert response.validation and response.validation.is_safe
    assert response.columns == ["CustomerId", "customer", "revenue"]
    assert response.rows[0][1] == "Asha Patil"
    assert response.rows[0][2] == 330.75


def test_demo_count_query(settings):
    response = QueryService(settings).ask("How many customers are in the database?")
    assert response.status == "success"
    assert response.rows == [[6]]


def test_vague_ranking_requests_clarification(settings):
    response = QueryService(settings).ask("Who are the best customers?")
    assert response.status == "clarification"
    assert response.clarification
