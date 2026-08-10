import pytest
from pydantic import SecretStr

pytest.importorskip("sqlglot")

from fastapi.testclient import TestClient

from queryguard.api.main import create_app
from queryguard.config import Settings


def test_health_and_query_with_demo_provider(database_path):
    settings = Settings(
        environment="test",
        database_path=database_path,
        llm_provider="demo",
        retrieval_strategy="lexical",
    )
    client = TestClient(create_app(settings))

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["database_available"] is True
    assert health.json()["llm_model"] == "deterministic-demo"

    response = client.post("/query", json={"question": "How many customers are in the database?"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["rows"] == [[59]]
    assert payload["validation"]["is_safe"] is True


def test_query_endpoint_can_require_shared_access_key(database_path):
    settings = Settings(
        environment="test",
        database_path=database_path,
        llm_provider="demo",
        retrieval_strategy="lexical",
        api_access_key=SecretStr("secret-test-key"),
    )
    client = TestClient(create_app(settings))

    blocked = client.post("/query", json={"question": "How many customers are in the database?"})
    assert blocked.status_code == 401

    allowed = client.post(
        "/query",
        headers={"X-QueryGuard-Key": "secret-test-key"},
        json={"question": "How many customers are in the database?"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["status"] == "success"
